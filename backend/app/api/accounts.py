from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_customer
from app.models.identity import Customer
from app.schemas.account import AccountListResponse, AccountResponse
from app.schemas.common import Page
from app.schemas.transaction import TransactionFilter, TransactionResponse
from app.services import account_service, transaction_service

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=AccountListResponse)
async def get_accounts(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> AccountListResponse:
    accounts = await account_service.list_accounts(db, customer)
    return AccountListResponse(
        items=[AccountResponse.model_validate(a) for a in accounts],
        total=len(accounts),
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await account_service.get_account(db, customer, account_id)


@router.get("/{account_id}/transactions", response_model=Page[TransactionResponse])
async def get_account_transactions(
    account_id: UUID,
    filters: Annotated[TransactionFilter, Query()],
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.list_account_transactions(db, customer, account_id, filters)
