"""Helpers shared by the customer-facing services."""

import secrets
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequestContext
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.security import mask_account_number  # noqa: F401  (re-exported)
from app.models.banking import Account, Transaction
from app.models.system import AuditLog, Notification

TWO_PLACES = Decimal("0.01")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def generate_reference(prefix: str) -> str:
    """Unique, non-guessable business reference, e.g. TRF-20261003-1A2B3C4D5E6F."""
    return f"{prefix}-{utcnow():%Y%m%d}-{secrets.token_hex(6).upper()}"


async def paginate(
    db: AsyncSession, query: Select, *, page: int, page_size: int
) -> dict:
    total = await db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = await db.scalars(query.offset((page - 1) * page_size).limit(page_size))
    return {
        "items": list(rows),
        "page": page,
        "page_size": page_size,
        "total": total or 0,
    }


async def get_owned_account(
    db: AsyncSession,
    customer_id: UUID,
    account_id: UUID,
    *,
    lock: bool = False,
) -> Account:
    """Fetch an account only if it belongs to the customer.

    Returns 404 (not 403) for other customers' accounts so account IDs
    cannot be enumerated. ``lock=True`` takes a row lock for balance updates.
    """
    query = select(Account).where(
        Account.id == account_id, Account.customer_id == customer_id
    )
    if lock:
        query = query.with_for_update()
    account = await db.scalar(query)
    if account is None:
        raise NotFoundError("Account not found")
    return account


def ensure_account_active(account: Account) -> None:
    if account.status != "ACTIVE":
        raise BusinessRuleError("Account is not active")


def ensure_sufficient_funds(account: Account, amount: Decimal) -> None:
    if to_money(account.available_balance) < amount:
        raise BusinessRuleError("Insufficient available balance")


def debit_account(
    db: AsyncSession,
    account: Account,
    amount: Decimal,
    *,
    category: str,
    description: str,
    prefix: str,
    merchant_name: str | None = None,
) -> Transaction:
    """Debit a (locked) account and record the matching ledger transaction.

    Caller is responsible for ownership/status/balance checks and for commit.
    """
    account.balance = to_money(account.balance) - amount
    account.available_balance = to_money(account.available_balance) - amount
    txn = Transaction(
        account_id=account.id,
        transaction_reference=generate_reference(prefix),
        transaction_type="DEBIT",
        amount=amount,
        currency=account.currency,
        category=category,
        description=description[:500],
        merchant_name=merchant_name,
        transaction_status="COMPLETED",
        transaction_date=utcnow(),
        channel="ONLINE",
    )
    db.add(txn)
    return txn


def credit_account(
    db: AsyncSession,
    account: Account,
    amount: Decimal,
    *,
    category: str,
    description: str,
    prefix: str,
) -> Transaction:
    account.balance = to_money(account.balance) + amount
    account.available_balance = to_money(account.available_balance) + amount
    txn = Transaction(
        account_id=account.id,
        transaction_reference=generate_reference(prefix),
        transaction_type="CREDIT",
        amount=amount,
        currency=account.currency,
        category=category,
        description=description[:500],
        transaction_status="COMPLETED",
        transaction_date=utcnow(),
        channel="ONLINE",
    )
    db.add(txn)
    return txn


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (UUID, datetime)):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def write_audit(
    db: AsyncSession,
    *,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    ctx: RequestContext | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
) -> None:
    """Stage an audit entry in the current DB transaction.

    Callers must never pass secrets, and should pass masked account numbers.
    """
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=_json_safe(old_value) if old_value is not None else None,
            new_value=_json_safe(new_value) if new_value is not None else None,
            ip_address=ctx.ip_address if ctx else None,
            user_agent=ctx.user_agent if ctx else None,
            created_at=utcnow(),
        )
    )


def create_notification(
    db: AsyncSession,
    *,
    user_id: UUID,
    type: str,
    title: str,
    message: str,
    severity: str = "INFO",
) -> None:
    db.add(
        Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            severity=severity,
            is_read=False,
            created_at=utcnow(),
        )
    )
