from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.banking import Account, Transaction
from app.models.identity import Customer
from app.schemas.transaction import TransactionFilter
from app.services.common import get_owned_account, paginate


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so user search text is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def list_account_transactions(
    db: AsyncSession,
    customer: Customer,
    account_id: UUID,
    filters: TransactionFilter,
) -> dict:
    # Ownership check first: a foreign account_id yields 404.
    await get_owned_account(db, customer.id, account_id)

    query = select(Transaction).where(Transaction.account_id == account_id)

    if filters.category:
        query = query.where(Transaction.category == filters.category.upper())
    if filters.transaction_type:
        query = query.where(Transaction.transaction_type == filters.transaction_type.upper())
    if filters.transaction_status:
        query = query.where(Transaction.transaction_status == filters.transaction_status.upper())
    if filters.start_date:
        start = datetime.combine(filters.start_date, time.min, tzinfo=timezone.utc)
        query = query.where(Transaction.transaction_date >= start)
    if filters.end_date:
        end = datetime.combine(filters.end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        query = query.where(Transaction.transaction_date < end)
    if filters.min_amount is not None:
        query = query.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        query = query.where(Transaction.amount <= filters.max_amount)
    if filters.search:
        pattern = f"%{_escape_like(filters.search)}%"
        query = query.where(
            or_(
                Transaction.description.ilike(pattern, escape="\\"),
                Transaction.merchant_name.ilike(pattern, escape="\\"),
                Transaction.transaction_reference.ilike(pattern, escape="\\"),
            )
        )

    query = query.order_by(Transaction.transaction_date.desc(), Transaction.id)
    return await paginate(db, query, page=filters.page, page_size=filters.page_size)


async def get_transaction(
    db: AsyncSession, customer: Customer, transaction_id: UUID
) -> Transaction:
    txn = await db.scalar(
        select(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .where(Transaction.id == transaction_id, Account.customer_id == customer.id)
    )
    if txn is None:
        raise NotFoundError("Transaction not found")
    return txn
