"""Fraud service layer for querying and managing fraud domain data."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import cast, desc, func, or_, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequestContext
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.banking import Transaction
from app.models.fraud import FraudAlert, FraudEvent, FraudInvestigation
from app.models.identity import Customer, User
from app.schemas.fraud import (
    FraudAlertUpdate,
    InvestigationItemResponse,
    InvestigationListResponse,
)
from app.services.common import utcnow, write_audit

ALLOWED_ALERT_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"IN_REVIEW", "ESCALATED"},
    "IN_REVIEW": {"ESCALATED", "RESOLVED", "FALSE_POSITIVE"},
    "ESCALATED": {"IN_REVIEW", "RESOLVED", "FALSE_POSITIVE"},
    "RESOLVED": {"IN_REVIEW"},
    "FALSE_POSITIVE": {"IN_REVIEW"},
}

SEVERITY_BY_PRIORITY: dict[int, str] = {
    1: "Critical",
    2: "High",
    3: "Medium",
    4: "Low",
}

PRIORITY_BY_SEVERITY: dict[str, int] = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4,
}

STATUS_TO_DISPLAY: dict[str, str] = {
    "OPEN": "Open",
    "IN_REVIEW": "In review",
    "ESCALATED": "Escalated",
    "RESOLVED": "Resolved",
    "FALSE_POSITIVE": "False positive",
}

DISPLAY_TO_STATUS: dict[str, str] = {
    "Open": "OPEN",
    "In review": "IN_REVIEW",
    "Escalated": "ESCALATED",
    "Resolved": "RESOLVED",
    "False positive": "FALSE_POSITIVE",
}

SCENARIO_TYPE_LABELS: dict[str, str] = {
    "SCENARIO_1": "Unusual transfer amount",
    "SCENARIO_2": "New sign-in location",
    "SCENARIO_3": "Repeated login failures",
    "SCENARIO_4": "High velocity activity",
    "SCENARIO_5": "Monthly spend spike",
}


def _format_event_type(raw_type: str | None) -> str:
    if not raw_type:
        return "Suspicious activity"
    if raw_type in SCENARIO_TYPE_LABELS:
        return SCENARIO_TYPE_LABELS[raw_type]
    return raw_type.replace("_", " ").title()


def _format_status(raw_status: str | None) -> str:
    if not raw_status:
        return "Open"
    return STATUS_TO_DISPLAY.get(raw_status.upper(), raw_status.title())


def _format_severity(priority: int | None) -> str:
    if priority is None:
        return "Medium"
    return SEVERITY_BY_PRIORITY.get(priority, "Medium")


class FraudService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_investigations(
        self,
        *,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InvestigationListResponse:
        # Latest investigation per alert using window partition with deterministic secondary sort (id)
        inv_subq = (
            select(
                FraudInvestigation.id.label("inv_id"),
                FraudInvestigation.alert_id.label("inv_alert_id"),
                FraudInvestigation.notes.label("inv_notes"),
                func.row_number()
                .over(
                    partition_by=FraudInvestigation.alert_id,
                    order_by=(desc(FraudInvestigation.started_at), desc(FraudInvestigation.id)),
                )
                .label("rn"),
            )
            .subquery()
        )

        latest_inv = (
            select(
                inv_subq.c.inv_id,
                inv_subq.c.inv_alert_id,
                inv_subq.c.inv_notes,
            )
            .where(inv_subq.c.rn == 1)
            .subquery()
        )

        query = (
            select(
                FraudAlert,
                FraudEvent,
                Customer,
                User,
                Transaction.amount.label("txn_amount"),
                latest_inv.c.inv_id,
                latest_inv.c.inv_notes,
            )
            .join(FraudEvent, FraudEvent.id == FraudAlert.fraud_event_id)
            .outerjoin(Customer, Customer.id == FraudAlert.customer_id)
            .outerjoin(User, User.id == FraudAlert.assigned_to)
            .outerjoin(Transaction, Transaction.id == FraudEvent.transaction_id)
            .outerjoin(latest_inv, latest_inv.c.inv_alert_id == FraudAlert.id)
        )

        filters = []

        if severity and severity.lower() != "all":
            norm_sev = severity.capitalize()
            prio = PRIORITY_BY_SEVERITY.get(norm_sev)
            if prio:
                filters.append(FraudAlert.priority == prio)

        if status and status.lower() != "all":
            norm_status = DISPLAY_TO_STATUS.get(status, status.upper())
            filters.append(FraudAlert.status == norm_status)

        if assignee and assignee.lower() != "all":
            if assignee.lower() == "unassigned":
                filters.append(FraudAlert.assigned_to.is_(None))
            else:
                filters.append(User.email.ilike(f"%{assignee.strip()}%"))

        if search and search.strip():
            raw_term = search.strip()
            term = f"%{raw_term}%"
            # Strip prefixes like "INV-" or "FA-" if present to match underlying UUID
            clean_term = raw_term
            if clean_term.upper().startswith("INV-"):
                clean_term = clean_term[4:]
            elif clean_term.upper().startswith("FA-"):
                clean_term = clean_term[3:]
            clean_like = f"%{clean_term}%"

            search_clauses = [
                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),
                Customer.customer_number.ilike(term),
                FraudEvent.event_type.ilike(term),
                FraudEvent.description.ilike(term),
                cast(FraudAlert.id, String).ilike(clean_like),
            ]
            if latest_inv.c.inv_id is not None:
                search_clauses.append(cast(latest_inv.c.inv_id, String).ilike(clean_like))

            filters.append(or_(*search_clauses))

        if filters:
            query = query.where(*filters)

        total_stmt = select(func.count()).select_from(query.order_by(None).subquery())
        total = await self.db.scalar(total_stmt) or 0

        # Deterministic ordering: latest created alerts first, secondary alert id
        query = query.order_by(desc(FraudAlert.created_at), desc(FraudAlert.id)).offset((page - 1) * page_size).limit(page_size)

        rows = (await self.db.execute(query)).all()

        items: list[InvestigationItemResponse] = []
        for row in rows:
            alert: FraudAlert = row[0]
            event: FraudEvent = row[1]
            customer: Customer | None = row[2]
            assigned_user: User | None = row[3]
            txn_amount = row[4]
            inv_id = row[5]
            inv_notes = row[6]

            amount: float | None = None
            if txn_amount is not None:
                amount = float(txn_amount)
            elif event.event_metadata and isinstance(event.event_metadata, dict):
                raw_amt = event.event_metadata.get("fraud_amount") or event.event_metadata.get("transfer_amount")
                if raw_amt is not None:
                    try:
                        amount = float(raw_amt)
                    except (ValueError, TypeError):
                        pass

            if customer:
                c_name = f"{customer.first_name} {customer.last_name}".strip()
                c_id = str(customer.id)
            else:
                c_name = "Unknown Customer"
                c_id = str(alert.customer_id) if alert.customer_id else None

            assigned_name = assigned_user.email if assigned_user else "Unassigned"

            notes_list: list[str] = []
            if inv_notes:
                notes_list = [n.strip() for n in str(inv_notes).split("\n") if n.strip()]

            inv_display_id = f"INV-{str(inv_id)[:8].upper()}" if inv_id else f"INV-{str(alert.id)[:8].upper()}"

            items.append(
                InvestigationItemResponse(
                    id=inv_display_id,
                    alert_id=str(alert.id),
                    customer_id=c_id,
                    customer_name=c_name,
                    type=_format_event_type(event.event_type if event else None),
                    severity=_format_severity(alert.priority),
                    status=_format_status(alert.status),
                    assigned_to=assigned_name,
                    opened_at=alert.created_at,
                    updated_at=alert.updated_at,
                    notes=notes_list,
                    risk_score=float(event.risk_score) if event and event.risk_score is not None else 0.0,
                    amount=amount,
                )
            )

        return InvestigationListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        )

    async def update_alert_status(
        self,
        *,
        alert_id: UUID,
        payload: FraudAlertUpdate,
        acting_user: User,
        ctx: RequestContext | None = None,
    ) -> FraudAlert:
        query = select(FraudAlert).where(FraudAlert.id == alert_id).with_for_update()
        alert = await self.db.scalar(query)
        if alert is None:
            raise NotFoundError("Fraud alert not found")

        current_status = alert.status.upper()
        new_status = payload.status

        allowed = ALLOWED_ALERT_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            if new_status == current_status:
                raise BusinessRuleError(f"Alert is already in status {current_status}")
            raise BusinessRuleError(
                f"Alert cannot transition from {current_status} to {new_status}"
            )

        old_value = {
            "status": current_status,
            "assigned_to": str(alert.assigned_to) if alert.assigned_to else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "resolution_notes": alert.resolution_notes,
        }

        # Apply state transition
        alert.status = new_status
        alert.updated_at = utcnow()

        # Timestamp logic
        if new_status in {"RESOLVED", "FALSE_POSITIVE"}:
            alert.resolved_at = utcnow()
        elif new_status in {"OPEN", "IN_REVIEW", "ESCALATED"}:
            alert.resolved_at = None

        # Auto-assignment if unassigned and moving to active handling
        if alert.assigned_to is None and new_status in {"IN_REVIEW", "ESCALATED"}:
            alert.assigned_to = acting_user.id

        # Preserve existing resolution_notes unless explicitly supplied
        if payload.resolution_notes is not None:
            alert.resolution_notes = payload.resolution_notes

        new_value = {
            "status": new_status,
            "assigned_to": str(alert.assigned_to) if alert.assigned_to else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "resolution_notes": alert.resolution_notes,
        }

        write_audit(
            self.db,
            user_id=acting_user.id,
            action="FRAUD_ALERT_STATUS_UPDATED",
            entity_type="FRAUD_ALERT",
            entity_id=alert.id,
            ctx=ctx,
            old_value=old_value,
            new_value=new_value,
        )

        try:
            await self.db.commit()
            await self.db.refresh(alert)
        except Exception:
            await self.db.rollback()
            raise

        return alert
