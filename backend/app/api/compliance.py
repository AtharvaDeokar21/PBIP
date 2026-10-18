from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.identity import User
from app.schemas.audit import AuditLogListResponse
from app.schemas.compliance import ComplianceAlertListResponse
from app.schemas.security import SecurityEventListResponse
from app.services.audit_service import AuditService
from app.services.compliance_service import ComplianceService
from app.services.security_service import SecurityService


router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"],
)


COMPLIANCE_ROLES = [
    "COMPLIANCE_OFFICER",
    "ADMIN",
]

SECURITY_EVENT_ROLES = [
    "COMPLIANCE_OFFICER",
    "ADMIN",
    "FRAUD_ANALYST",
]


@router.get(
    "/alerts",
    response_model=ComplianceAlertListResponse,
    dependencies=[Depends(require_roles(*COMPLIANCE_ROLES))],
)
async def get_compliance_alerts(
    as_of: Optional[date] = Query(None, description="Snapshot reference date (YYYY-MM-DD); defaults to current UTC time."),
    category: Optional[str] = Query(None, description="Filter by category (KYC, AML, Reporting, Documentation, Transaction)"),
    severity: Optional[str] = Query(None, description="Filter by severity (Critical, High, Medium, Low)"),
    status: Optional[str] = Query(None, description="Filter by status (Open, In review, Resolved)"),
    search: Optional[str] = Query(None, description="Search by alert ID, customer name, customer ID, type, or description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComplianceAlertListResponse:
    service = ComplianceService(db)
    as_of_dt = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc) if as_of else None
    return await service.list_alerts(
        category=category,
        severity=severity,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
        as_of=as_of_dt,
    )


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_roles(*COMPLIANCE_ROLES))],
)
async def get_audit_logs(
    search: Optional[str] = Query(None, description="Search by log ID, actor, action, or resource"),
    actor: Optional[str] = Query(None, description="Filter by actor name or email"),
    action: Optional[str] = Query(None, description="Filter by action code or label"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (Success, Failure, Warning)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditLogListResponse:
    service = AuditService(db)
    return await service.list_audit_logs(
        search=search,
        actor=actor,
        action=action,
        outcome=outcome,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/security-events",
    response_model=SecurityEventListResponse,
    dependencies=[Depends(require_roles(*SECURITY_EVENT_ROLES))],
)
async def get_security_events(
    search: Optional[str] = Query(None, description="Search by event ID, IP, user, email, type or description"),
    severity: Optional[str] = Query(None, description="Filter by severity (Critical, High, Medium, Low)"),
    status: Optional[str] = Query(None, description="Filter by status (Requires review, Logged, Open, Resolved)"),
    channel: Optional[str] = Query(None, description="Filter by channel (Net banking, Mobile app, API, ATM, Unknown)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SecurityEventListResponse:
    service = SecurityService(db)
    return await service.list_security_events(
        search=search,
        severity=severity,
        status=status,
        channel=channel,
        page=page,
        page_size=page_size,
    )
