"""Audit service layer for querying persisted audit logs."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import String, cast, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Customer, User
from app.models.system import AuditLog
from app.schemas.audit import (
    AuditLogItemResponse,
    AuditLogListResponse,
    AuditSummaryResponse,
)

ROLE_DISPLAY_MAP: dict[str, str] = {
    "ADMIN": "Administrator",
    "COMPLIANCE_OFFICER": "Compliance Officer",
    "FRAUD_ANALYST": "Fraud Analyst",
    "MANAGER": "Relationship Manager",
    "OFFICER": "Officer",
    "CUSTOMER": "Customer",
}

ACTION_DISPLAY_MAP: dict[str, str] = {
    "USER_LOGIN": "Login",
    "CUSTOMER_REGISTERED": "Customer registered",
    "CUSTOMER_PROFILE_UPDATED": "Profile update",
    "FRAUD_ALERT_STATUS_UPDATED": "Alert resolved",
    "TRANSFER_CREATED": "Transfer created",
    "TRANSFER_COMPLETED": "Transfer completed",
    "TRANSFER_CANCELLED": "Transfer cancelled",
    "BILL_PAYMENT_COMPLETED": "Bill payment",
    "PAYEE_CREATED": "Payee created",
    "PAYEE_UPDATED": "Payee updated",
    "PAYEE_DEACTIVATED": "Payee deactivated",
    "INVESTMENT_PURCHASED": "Investment purchase",
    "LOAN_APPLICATION_SUBMITTED": "Loan application",
}

RESOURCE_DISPLAY_MAP: dict[str, str] = {
    "USER": "Auth",
    "CUSTOMER": "Customer Profile",
    "FRAUD_ALERT": "Fraud Alert",
    "TRANSFER": "Transfer",
    "CUSTOMER_INVESTMENT": "Investment",
    "LOAN_APPLICATION": "Loan Application",
    "PAYEE": "Payee",
    "BILL_PAYMENT": "Bill Payment",
}


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_audit_logs(
        self,
        *,
        search: Optional[str] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        page_size: int = 15,
    ) -> AuditLogListResponse:
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        base_stmt = (
            select(AuditLog, User, Customer)
            .outerjoin(User, User.id == AuditLog.user_id)
            .outerjoin(Customer, Customer.user_id == User.id)
        )

        filters = []

        # 1. Search across log ID, action, actor, entity type, and IP address
        if search and search.strip():
            raw_term = search.strip()
            term = f"%{raw_term}%"
            clean_term = raw_term[3:].strip() if raw_term.upper().startswith("AL-") else raw_term
            clean_like = f"%{clean_term}%"
            clean_hex_like = f"%{clean_term.replace('-', '')}%"

            clauses = [
                cast(AuditLog.id, String).ilike(clean_like),
                cast(AuditLog.id, String).ilike(clean_hex_like),
                AuditLog.action.ilike(term),
                User.email.ilike(term),
                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),
                AuditLog.entity_type.ilike(term),
                AuditLog.ip_address.ilike(term),
            ]
            try:
                parsed_uuid = UUID(clean_term)
                clauses.append(AuditLog.id == parsed_uuid)
            except (ValueError, AttributeError):
                pass

            filters.append(or_(*clauses))

        # 2. Actor filter
        if actor and actor.strip().lower() != "all":
            actor_term = actor.strip()
            filters.append(
                or_(
                    User.email.ilike(f"%{actor_term}%"),
                    Customer.first_name.ilike(f"%{actor_term}%"),
                    Customer.last_name.ilike(f"%{actor_term}%"),
                    func.concat(Customer.first_name, " ", Customer.last_name).ilike(
                        f"%{actor_term}%"
                    ),
                )
            )

        # 3. Action filter (supports matching either canonical action or display label)
        if action and action.strip().lower() != "all":
            action_term = action.strip()
            matched_actions = {action_term.upper(), action_term}
            for code, label in ACTION_DISPLAY_MAP.items():
                if (
                    label.lower() == action_term.lower()
                    or code.lower() == action_term.lower()
                ):
                    matched_actions.add(code)
            filters.append(
                or_(
                    AuditLog.action.in_(matched_actions),
                    AuditLog.action.ilike(f"%{action_term}%"),
                )
            )

        # 4. Outcome filter
        # The audit_logs table records committed successful operations.
        # If user explicitly filters for "Failure" or "Warning", return empty result set truthfully.
        if outcome and outcome.strip().lower() != "all":
            norm_outcome = outcome.strip().lower()
            if norm_outcome != "success":
                filters.append(false())

        if filters:
            base_stmt = base_stmt.where(*filters)

        # Total count matching filters
        count_stmt = (
            select(func.count(AuditLog.id))
            .outerjoin(User, User.id == AuditLog.user_id)
            .outerjoin(Customer, Customer.user_id == User.id)
        )
        if filters:
            count_stmt = count_stmt.where(*filters)

        total = await self.db.scalar(count_stmt) or 0

        # Deterministic ordering: newest first, tie-break by ID
        query_stmt = (
            base_stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )

        rows = (await self.db.execute(query_stmt)).all()

        items: List[AuditLogItemResponse] = []
        for log, user, customer in rows:
            # Resolve actor display name and role
            if customer and (customer.first_name or customer.last_name):
                actor_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
                actor_role = "Customer"
            elif user:
                actor_name = user.email
                actor_role = ROLE_DISPLAY_MAP.get(
                    user.role.upper(), user.role.replace("_", " ").title()
                )
            else:
                actor_name = "System"
                actor_role = "System"

            # Resolve action and resource labels
            action_label = ACTION_DISPLAY_MAP.get(
                log.action, log.action.replace("_", " ").capitalize()
            )
            resource_label = RESOURCE_DISPLAY_MAP.get(
                log.entity_type,
                log.entity_type.replace("_", " ").title()
                if log.entity_type
                else "System",
            )
            resource_id_str = str(log.entity_id) if log.entity_id else "-"

            cust_id_str = None
            if customer:
                cust_id_str = str(customer.id)
            elif log.entity_type == "CUSTOMER" and log.entity_id:
                cust_id_str = str(log.entity_id)

            items.append(
                AuditLogItemResponse(
                    id=f"AL-{str(log.id).upper()}",
                    actor=actor_name,
                    actor_role=actor_role,
                    action=action_label,
                    resource=resource_label,
                    resource_id=resource_id_str,
                    outcome="Success",
                    ip_address=log.ip_address or "127.0.0.1",
                    timestamp=log.created_at,
                    customer_id=cust_id_str,
                )
            )

        # Available actors & actions for dynamic frontend dropdown population
        available_actions_rows = (
            await self.db.scalars(select(AuditLog.action).distinct())
        ).all()
        available_actions = sorted(
            list(
                set(
                    ACTION_DISPLAY_MAP.get(
                        a, a.replace("_", " ").capitalize()
                    )
                    for a in available_actions_rows
                    if a
                )
            )
        )

        actor_query_rows = (
            await self.db.execute(
                select(User.email, Customer.first_name, Customer.last_name)
                .join(AuditLog, AuditLog.user_id == User.id)
                .outerjoin(Customer, Customer.user_id == User.id)
                .distinct()
            )
        ).all()
        actors_set = set()
        for email, f_name, l_name in actor_query_rows:
            if f_name or l_name:
                actors_set.add(f"{f_name or ''} {l_name or ''}".strip())
            elif email:
                actors_set.add(email)
        available_actors = sorted(list(actors_set))

        summary = AuditSummaryResponse(
            total_events=total,
            success_count=total,
            failure_count=0,
            warning_count=0,
            available_actors=available_actors,
            available_actions=available_actions,
        )

        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
            summary=summary,
        )
