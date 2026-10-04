from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequestContext
from app.core.exceptions import ConflictError, NotFoundError
from app.models.banking import Payee
from app.models.identity import Customer
from app.schemas.payee import PayeeCreate, PayeeUpdate
from app.services.common import mask_account_number, write_audit


def _audit_view(payee: Payee) -> dict:
    return {
        "name": payee.name,
        "account_number": mask_account_number(payee.account_number),
        "bank_name": payee.bank_name,
        "ifsc_code": payee.ifsc_code,
        "nickname": payee.nickname,
        "is_active": payee.is_active,
    }


async def get_owned_payee(
    db: AsyncSession, customer_id: UUID, payee_id: UUID, *, active_only: bool = True
) -> Payee:
    query = select(Payee).where(Payee.id == payee_id, Payee.customer_id == customer_id)
    if active_only:
        query = query.where(Payee.is_active.is_(True))
    payee = await db.scalar(query)
    if payee is None:
        raise NotFoundError("Payee not found")
    return payee


async def list_payees(db: AsyncSession, customer: Customer) -> list[Payee]:
    result = await db.scalars(
        select(Payee)
        .where(Payee.customer_id == customer.id, Payee.is_active.is_(True))
        .order_by(Payee.name)
    )
    return list(result)


async def create_payee(
    db: AsyncSession, customer: Customer, payload: PayeeCreate, ctx: RequestContext
) -> Payee:
    duplicate = await db.scalar(
        select(Payee.id).where(
            Payee.customer_id == customer.id,
            Payee.account_number == payload.account_number,
            Payee.ifsc_code == payload.ifsc_code,
            Payee.is_active.is_(True),
        )
    )
    if duplicate:
        raise ConflictError("A payee with these bank details already exists")

    payee = Payee(
        customer_id=customer.id,
        name=payload.name,
        account_number=payload.account_number,
        bank_name=payload.bank_name,
        ifsc_code=payload.ifsc_code,
        nickname=payload.nickname,
        # No verification workflow yet: payees start unverified.
        is_verified=False,
        is_active=True,
    )
    db.add(payee)
    await db.flush()

    write_audit(
        db,
        user_id=customer.user_id,
        action="PAYEE_CREATED",
        entity_type="PAYEE",
        entity_id=payee.id,
        ctx=ctx,
        new_value=_audit_view(payee),
    )
    await db.commit()
    await db.refresh(payee)
    return payee


async def update_payee(
    db: AsyncSession,
    customer: Customer,
    payee_id: UUID,
    payload: PayeeUpdate,
    ctx: RequestContext,
) -> Payee:
    payee = await get_owned_payee(db, customer.id, payee_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        return payee

    old_value = _audit_view(payee)
    for field, value in changes.items():
        setattr(payee, field, value)

    write_audit(
        db,
        user_id=customer.user_id,
        action="PAYEE_UPDATED",
        entity_type="PAYEE",
        entity_id=payee.id,
        ctx=ctx,
        old_value=old_value,
        new_value=_audit_view(payee),
    )
    await db.commit()
    await db.refresh(payee)
    return payee


async def deactivate_payee(
    db: AsyncSession, customer: Customer, payee_id: UUID, ctx: RequestContext
) -> None:
    """Soft-delete: keeps the row so historical transfers still reference it."""
    payee = await get_owned_payee(db, customer.id, payee_id)
    payee.is_active = False

    write_audit(
        db,
        user_id=customer.user_id,
        action="PAYEE_DEACTIVATED",
        entity_type="PAYEE",
        entity_id=payee.id,
        ctx=ctx,
        old_value={"is_active": True},
        new_value={"is_active": False},
    )
    await db.commit()
