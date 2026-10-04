from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_customer
from app.models.identity import Customer
from app.schemas.transaction import TransactionResponse
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# Listing is account-scoped: GET /accounts/{account_id}/transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.get_transaction(db, customer, transaction_id)
