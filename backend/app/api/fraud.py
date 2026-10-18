from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    RequestContext,
    get_current_user,
    get_request_context,
    require_roles,
)
from app.models.identity import User
from app.schemas.fraud import (
    FraudAlertResponse,
    FraudAlertUpdate,
    InvestigationListResponse,
)
from app.services.fraud_service import FraudService

router = APIRouter(
    prefix="/fraud",
    tags=["Fraud"],
)

FRAUD_ROLES = [
    "FRAUD_ANALYST",
    "ADMIN",
]


@router.get(
    "/investigations",
    response_model=InvestigationListResponse,
    dependencies=[Depends(require_roles(*FRAUD_ROLES))],
)
async def list_fraud_investigations(
    severity: Optional[str] = Query(None, description="Filter by severity (Critical, High, Medium, Low)"),
    status: Optional[str] = Query(None, description="Filter by status (Open, In review, Escalated, Resolved, False positive)"),
    assignee: Optional[str] = Query(None, description="Filter by assigned analyst email or Unassigned"),
    search: Optional[str] = Query(None, description="Search by case ID, alert ID, customer name, customer number, event type, or description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvestigationListResponse:
    service = FraudService(db)
    return await service.list_investigations(
        severity=severity,
        status=status,
        assignee=assignee,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/alerts",
    dependencies=[Depends(require_roles(*FRAUD_ROLES))],
)
async def get_fraud_alerts(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Fraud alerts will be implemented here"
    }


@router.get(
    "/alerts/{alert_id}",
    dependencies=[Depends(require_roles(*FRAUD_ROLES))],
)
async def get_fraud_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Fraud alert details will be implemented here",
        "alert_id": alert_id,
    }


@router.patch(
    "/alerts/{alert_id}",
    response_model=FraudAlertResponse,
    dependencies=[Depends(require_roles(*FRAUD_ROLES))],
)
async def update_fraud_alert(
    alert_id: UUID,
    payload: FraudAlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ctx: RequestContext = Depends(get_request_context),
) -> FraudAlertResponse:
    service = FraudService(db)
    return await service.update_alert_status(
        alert_id=alert_id,
        payload=payload,
        acting_user=current_user,
        ctx=ctx,
    )


@router.get(
    "/customers/{customer_id}/risk",
    dependencies=[Depends(require_roles(*FRAUD_ROLES))],
)
async def get_customer_risk(
    customer_id: UUID,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Customer fraud risk will be implemented here",
        "customer_id": customer_id,
    }