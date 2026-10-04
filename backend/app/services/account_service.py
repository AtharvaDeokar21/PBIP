from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banking import Account
from app.models.identity import Customer
from app.services.common import get_owned_account


async def list_accounts(db: AsyncSession, customer: Customer) -> list[Account]:
    result = await db.scalars(
        select(Account)
        .where(Account.customer_id == customer.id)
        .order_by(Account.created_at)
    )
    return list(result)


async def get_account(db: AsyncSession, customer: Customer, account_id: UUID) -> Account:
    return await get_owned_account(db, customer.id, account_id)
