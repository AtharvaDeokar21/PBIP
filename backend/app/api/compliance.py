from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.dependencies import require_roles
from app.models.identity import User


router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"],
)


COMPLIANCE_ROLES = [
    "COMPLIANCE_OFFICER",
    "ADMIN",
]


@router.get(
    "/alerts",
    dependencies=[Depends(require_roles(*COMPLIANCE_ROLES))],
)
async def get_compliance_alerts(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Compliance alerts will be implemented here"
    }


@router.get(
    "/audit-logs",
    dependencies=[Depends(require_roles(*COMPLIANCE_ROLES))],
)
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Audit logs will be implemented here"
    }


@router.get(
    "/security-events",
    dependencies=[Depends(require_roles(*COMPLIANCE_ROLES))],
)
async def get_security_events(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Security events will be implemented here"
    }