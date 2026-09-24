from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
)


@router.get("")
async def get_accounts(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Account listing will be implemented here"
    }


@router.get("/{account_id}")
async def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Account details will be implemented here",
        "account_id": account_id,
    }