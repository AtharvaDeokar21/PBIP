from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.get("")
async def get_transactions(
    account_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Transaction listing will be implemented here",
        "account_id": account_id,
    }


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Transaction details will be implemented here",
        "transaction_id": transaction_id,
    }