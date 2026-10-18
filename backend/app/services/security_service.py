"""Security service layer for querying and aggregating security telemetry events."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import String, and_, cast, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Customer, User
from app.models.system import SecurityEvent
from app.schemas.security import (
    SecurityEventItemResponse,
    SecurityEventListResponse,
    SecuritySummaryResponse,
)


def derive_channel(device_info: str | None) -> str:
    """Deterministically derives the access channel from user-agent/device info telemetry."""
    if not device_info or not device_info.strip():
        return "Unknown"
    lower = device_info.lower()
    if any(k in lower for k in ("curl", "postman", "python", "httpclient", "insomnia", "code/", "electron")):
        return "API"
    if any(k in lower for k in ("mobile", "android", "iphone", "ipad", "phone")):
        return "Mobile app"
    if any(k in lower for k in ("atm",)):
        return "ATM"
    if any(k in lower for k in ("mozilla", "chrome", "safari", "firefox", "edg", "windows", "linux", "macintosh")):
        return "Net banking"
    return "Unknown"


def derive_severity(raw_sev: str | None) -> str:
    """Normalizes database severity codes to standard interface risk categories."""
    if not raw_sev:
        return "Low"
    upper = raw_sev.strip().upper()
    if upper == "CRITICAL":
        return "Critical"
    if upper in ("HIGH", "ERROR"):
        return "High"
    if upper in ("WARNING", "MEDIUM"):
        return "Medium"
    if upper in ("INFO", "LOW"):
        return "Low"
    return "Low"


def derive_status(raw_sev: str | None) -> str:
    """Maps event severity to truthful audit lifecycle status without fabricating mutable state."""
    if not raw_sev:
        return "Logged"
    upper = raw_sev.strip().upper()
    if upper in ("WARNING", "HIGH", "CRITICAL", "ERROR"):
        return "Requires review"
    return "Logged"


def format_event_type(raw_type: str | None) -> str:
    """Converts internal database event codes to readable labels."""
    if not raw_type:
        return "Security event"
    mapping = {
        "LOGIN_SUCCESS": "Login successful",
        "LOGIN_FAILED": "Login failed",
        "HIGH_VALUE_TRANSFER": "High value transfer",
        "PASSWORD_CHANGED": "Password changed",
        "TOKEN_REVOKED": "Token revoked",
    }
    return mapping.get(raw_type.upper(), raw_type.replace("_", " ").capitalize())


def format_description(event: SecurityEvent) -> str:
    """Constructs a descriptive, truthful explanation of the recorded security telemetry."""
    evt_type = (event.event_type or "").upper()
    meta = event.event_metadata or {}

    if evt_type == "LOGIN_SUCCESS":
        return "User authenticated successfully"

    if evt_type == "LOGIN_FAILED":
        reason = meta.get("reason")
        if reason == "unknown_email":
            email_target = meta.get("email", "unknown")
            return f"Failed login attempt: unregistered email ({email_target})"
        if reason == "invalid_password":
            return "Failed login attempt: invalid password provided"
        if reason == "inactive_account":
            return "Failed login attempt: account is inactive"
        return "Failed login attempt: authentication rejected"

    if evt_type == "HIGH_VALUE_TRANSFER":
        amt = meta.get("amount")
        if amt:
            return f"High value transfer flagged for monitoring (Amount: ₹{amt})"
        return "High value transfer transaction flagged for monitoring"

    return f"Security event recorded: {event.event_type}"


class SecurityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_security_events(
        self,
        *,
        search: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> SecurityEventListResponse:
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        base_stmt = (
            select(SecurityEvent, User, Customer)
            .outerjoin(User, User.id == SecurityEvent.user_id)
            .outerjoin(Customer, Customer.user_id == User.id)
        )

        filters = []

        # 1. Search filter across event ID, type, IP, device info, email, and customer name
        if search and search.strip():
            raw_term = search.strip()
            term = f"%{raw_term}%"
            clean_term = raw_term[3:].strip() if raw_term.upper().startswith("SE-") else raw_term
            clean_like = f"%{clean_term}%"
            clean_hex_like = f"%{clean_term.replace('-', '')}%"

            clauses = [
                cast(SecurityEvent.id, String).ilike(clean_like),
                cast(SecurityEvent.id, String).ilike(clean_hex_like),
                SecurityEvent.event_type.ilike(term),
                SecurityEvent.ip_address.ilike(term),
                SecurityEvent.device_info.ilike(term),
                User.email.ilike(term),
                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),
            ]
            try:
                parsed_uuid = UUID(clean_term)
                clauses.append(SecurityEvent.id == parsed_uuid)
                clauses.append(SecurityEvent.user_id == parsed_uuid)
            except (ValueError, TypeError):
                pass

            filters.append(or_(*clauses))

        # 2. Severity filter
        if severity and severity.strip().lower() != "all":
            norm_sev = severity.strip().lower()
            if norm_sev == "critical":
                filters.append(func.upper(SecurityEvent.severity) == "CRITICAL")
            elif norm_sev == "high":
                filters.append(func.upper(SecurityEvent.severity).in_(["HIGH", "ERROR"]))
            elif norm_sev in ("medium", "warning"):
                filters.append(func.upper(SecurityEvent.severity).in_(["WARNING", "MEDIUM"]))
            elif norm_sev in ("low", "info"):
                filters.append(func.upper(SecurityEvent.severity).in_(["INFO", "LOW"]))

        # 3. Status filter
        if status and status.strip().lower() != "all":
            norm_status = status.strip().lower()
            if norm_status in ("requires review", "requires_review", "open", "in review", "in_review"):
                filters.append(func.upper(SecurityEvent.severity).in_(["WARNING", "HIGH", "CRITICAL", "ERROR"]))
            elif norm_status in ("logged", "resolved", "closed"):
                filters.append(func.upper(SecurityEvent.severity).in_(["INFO", "LOW"]))

        # 4. Channel filter
        if channel and channel.strip().lower() != "all":
            norm_channel = channel.strip().lower()
            api_terms = [
                SecurityEvent.device_info.ilike("%curl%"),
                SecurityEvent.device_info.ilike("%postman%"),
                SecurityEvent.device_info.ilike("%python%"),
                SecurityEvent.device_info.ilike("%httpclient%"),
                SecurityEvent.device_info.ilike("%insomnia%"),
                SecurityEvent.device_info.ilike("%code/%"),
                SecurityEvent.device_info.ilike("%electron%"),
            ]
            mobile_terms = [
                SecurityEvent.device_info.ilike("%mobile%"),
                SecurityEvent.device_info.ilike("%android%"),
                SecurityEvent.device_info.ilike("%iphone%"),
                SecurityEvent.device_info.ilike("%ipad%"),
                SecurityEvent.device_info.ilike("%phone%"),
            ]
            if norm_channel == "api":
                filters.append(or_(*api_terms))
            elif norm_channel in ("mobile app", "mobile", "mobile_app"):
                filters.append(or_(*mobile_terms))
            elif norm_channel == "atm":
                filters.append(SecurityEvent.device_info.ilike("%atm%"))
            elif norm_channel in ("net banking", "net_banking", "web", "browser"):
                filters.append(
                    and_(
                        SecurityEvent.device_info.isnot(None),
                        not_(or_(*api_terms)),
                        not_(or_(*mobile_terms)),
                        not_(SecurityEvent.device_info.ilike("%atm%")),
                    )
                )
            elif norm_channel == "unknown":
                filters.append(SecurityEvent.device_info.is_(None))

        if filters:
            base_stmt = base_stmt.where(*filters)

        # Count total matching records
        count_stmt = select(func.count(SecurityEvent.id))
        if filters:
            count_stmt = (
                count_stmt
                .select_from(SecurityEvent)
                .outerjoin(User, User.id == SecurityEvent.user_id)
                .outerjoin(Customer, Customer.user_id == User.id)
                .where(*filters)
            )

        total = await self.db.scalar(count_stmt) or 0

        # Query all matching rows (unpaginated) for accurate summary distribution
        summary_query = (
            select(SecurityEvent.severity, SecurityEvent.device_info)
            .select_from(SecurityEvent)
            .outerjoin(User, User.id == SecurityEvent.user_id)
            .outerjoin(Customer, Customer.user_id == User.id)
        )
        if filters:
            summary_query = summary_query.where(*filters)

        summary_rows = (await self.db.execute(summary_query)).all()

        crit_count = 0
        req_review_count = 0
        logged_count = 0
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        channel_counts = {"Mobile app": 0, "Net banking": 0, "ATM": 0, "API": 0}

        for raw_sev, dev_info in summary_rows:
            sev_cat = derive_severity(raw_sev)
            severity_counts[sev_cat] = severity_counts.get(sev_cat, 0) + 1
            if sev_cat == "Critical":
                crit_count += 1

            status_cat = derive_status(raw_sev)
            if status_cat == "Requires review":
                req_review_count += 1
            else:
                logged_count += 1

            chan_cat = derive_channel(dev_info)
            if chan_cat in channel_counts:
                channel_counts[chan_cat] += 1
            else:
                channel_counts[chan_cat] = channel_counts.get(chan_cat, 0) + 1

        summary = SecuritySummaryResponse(
            total_events=total,
            critical_count=crit_count,
            requires_review_count=req_review_count,
            logged_count=logged_count,
            open_count=req_review_count,
            resolved_count=logged_count,
            severity_counts=severity_counts,
            channel_counts=channel_counts,
        )

        # Deterministic ordering: newest first, tie-break by ID
        query_stmt = (
            base_stmt.order_by(SecurityEvent.created_at.desc(), SecurityEvent.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )

        rows = (await self.db.execute(query_stmt)).all()

        items: List[SecurityEventItemResponse] = []
        for event, user, customer in rows:
            # Identity resolution: customer, internal user, or unauthenticated email
            cust_id_str = None
            if customer:
                cust_id_str = str(customer.id)
                display_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
                if not display_name and user and user.email:
                    display_name = user.email
            elif user and user.email:
                display_name = f"{user.email} (Internal Staff)"
            else:
                meta_email = (event.event_metadata or {}).get("email")
                if meta_email:
                    display_name = f"{meta_email} (Unregistered)"
                else:
                    display_name = "Unauthenticated / Unknown"

            channel_str = derive_channel(event.device_info)
            sev_str = derive_severity(event.severity)
            status_str = derive_status(event.severity)
            loc_str = event.location.strip() if event.location and event.location.strip() else "Unknown"
            device_str = event.device_info[:60] if event.device_info else "Unknown"

            items.append(
                SecurityEventItemResponse(
                    id=f"SE-{str(event.id).upper()}",
                    event_id=str(event.id),
                    user_id=str(event.user_id) if event.user_id else None,
                    customer_id=cust_id_str,
                    customer_name=display_name,
                    event_type=format_event_type(event.event_type),
                    channel=channel_str,
                    severity=sev_str,
                    status=status_str,
                    detected_at=event.created_at,
                    description=format_description(event),
                    location=loc_str,
                    device=device_str,
                    ip_address=event.ip_address or "Unknown",
                )
            )

        return SecurityEventListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
            summary=summary,
        )
