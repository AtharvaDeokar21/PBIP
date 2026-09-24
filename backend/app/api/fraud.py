from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.dependencies import require_roles
from app.models.identity import User


router = APIRouter(
    prefix="/fraud",
    tags=["Fraud"],
)


FRAUD_ROLES = [
    "FRAUD_ANALYST",
    "ADMIN",
]


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