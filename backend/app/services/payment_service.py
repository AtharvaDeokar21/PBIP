"""Transfers and bill payments.

Every money-moving operation runs inside a single DB transaction: all
validation happens before any write, involved accounts are row-locked, and
the session is committed once at the end. Any exception leaves the database
untouched (the session is rolled back when the request ends).
"""

from datetime import datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import RequestContext
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.banking import Account, BillPayment, Biller, Transfer
from app.models.identity import Customer
from app.models.system import SecurityEvent
from app.schemas.bill import BillPaymentCreate
from app.schemas.transfer import TransferCreate
from app.services.common import (
    create_notification,
    credit_account,
    debit_account,
    ensure_account_active,
    ensure_sufficient_funds,
    generate_reference,
    get_owned_account,
    mask_account_number,
    paginate,
    to_money,
    utcnow,
    write_audit,
)
from app.services.payee_service import get_owned_payee

# ---------------------------------------------------------------------------
# Transfer state machine. Status changes only happen through these
# transitions; the API never accepts an arbitrary status from the client.
# ---------------------------------------------------------------------------
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"PROCESSING", "CANCELLED", "FAILED"},
    "SCHEDULED": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"COMPLETED", "FAILED"},
    "COMPLETED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}
CUSTOMER_CANCELLABLE = {"PENDING", "SCHEDULED"}
# Transfers in these states count towards the daily limit.
LIMIT_COUNTED_STATUSES = ("PENDING", "PROCESSING", "COMPLETED", "SCHEDULED")
# Large transfers are flagged as security events for the fraud engine.
HIGH_VALUE_TRANSFER_THRESHOLD = Decimal("200000")


def transition(transfer: Transfer, new_status: str) -> None:
    if new_status not in ALLOWED_TRANSITIONS.get(transfer.status, set()):
        raise BusinessRuleError(
            f"Transfer cannot move from {transfer.status} to {new_status}"
        )
    transfer.status = new_status


async def _lock_accounts(
    db: AsyncSession, customer_id: UUID, account_ids: list[UUID]
) -> dict[UUID, Account]:
    # Lock in a deterministic order to avoid deadlocks between concurrent transfers.
    return {
        account_id: await get_owned_account(db, customer_id, account_id, lock=True)
        for account_id in sorted(account_ids, key=str)
    }


async def _amount_transferred_today(db: AsyncSession, customer_id: UUID) -> Decimal:
    day_start = datetime.combine(utcnow().date(), time.min, tzinfo=timezone.utc)
    total = await db.scalar(
        select(func.coalesce(func.sum(Transfer.amount), 0)).where(
            Transfer.customer_id == customer_id,
            Transfer.created_at >= day_start,
            Transfer.status.in_(LIMIT_COUNTED_STATUSES),
        )
    )
    return to_money(total)


async def _check_limits(db: AsyncSession, customer_id: UUID, amount: Decimal) -> None:
    if amount > to_money(settings.max_single_transfer_amount):
        raise BusinessRuleError("Amount exceeds the per-transfer limit")
    if await _amount_transferred_today(db, customer_id) + amount > to_money(
        settings.daily_transfer_limit
    ):
        raise BusinessRuleError("Amount exceeds the daily transfer limit")


async def create_transfer(
    db: AsyncSession, customer: Customer, payload: TransferCreate, ctx: RequestContext
) -> Transfer:
    amount = to_money(payload.amount)

    # --- validation (no writes yet) -------------------------------------
    account_ids = [payload.source_account_id]
    if payload.destination_account_id:
        account_ids.append(payload.destination_account_id)
    accounts = await _lock_accounts(db, customer.id, account_ids)

    source = accounts[payload.source_account_id]
    ensure_account_active(source)

    destination: Account | None = None
    payee = None
    if payload.destination_account_id:
        destination = accounts[payload.destination_account_id]
        ensure_account_active(destination)
        if destination.currency != source.currency:
            raise BusinessRuleError("Cross-currency transfers are not supported")
    else:
        payee = await get_owned_payee(db, customer.id, payload.payee_id)

    await _check_limits(db, customer.id, amount)
    ensure_sufficient_funds(source, amount)

    # --- writes -----------------------------------------------------------
    transfer = Transfer(
        customer_id=customer.id,
        source_account_id=source.id,
        destination_account_id=destination.id if destination else None,
        payee_id=payee.id if payee else None,
        amount=amount,
        transfer_type=payload.transfer_type,
        status="SCHEDULED" if payload.transfer_type == "SCHEDULED" else "PENDING",
        reference_number=generate_reference("TRF"),
        scheduled_at=payload.scheduled_at,
    )
    db.add(transfer)
    await db.flush()

    target_label = (
        f"own account {mask_account_number(destination.account_number)}"
        if destination
        else f"{payee.name} ({mask_account_number(payee.account_number)})"
    )
    audit_payload = {
        "reference_number": transfer.reference_number,
        "source_account": mask_account_number(source.account_number),
        "target": target_label,
        "amount": amount,
        "transfer_type": transfer.transfer_type,
        "scheduled_at": transfer.scheduled_at,
    }
    write_audit(
        db,
        user_id=customer.user_id,
        action="TRANSFER_CREATED",
        entity_type="TRANSFER",
        entity_id=transfer.id,
        ctx=ctx,
        new_value={**audit_payload, "status": transfer.status},
    )

    if payload.transfer_type == "IMMEDIATE":
        transition(transfer, "PROCESSING")
        description = f"Transfer {transfer.reference_number} to {target_label}"
        if payload.remarks:
            description += f" - {payload.remarks}"
        debit_account(
            db, source, amount, category="TRANSFER", description=description, prefix="TXN"
        )
        if destination:
            credit_account(
                db,
                destination,
                amount,
                category="TRANSFER",
                description=(
                    f"Transfer {transfer.reference_number} from own account "
                    f"{mask_account_number(source.account_number)}"
                ),
                prefix="TXN",
            )
        transition(transfer, "COMPLETED")
        transfer.executed_at = utcnow()

        write_audit(
            db,
            user_id=customer.user_id,
            action="TRANSFER_COMPLETED",
            entity_type="TRANSFER",
            entity_id=transfer.id,
            ctx=ctx,
            old_value={"status": "PROCESSING"},
            new_value={"status": "COMPLETED", "reference_number": transfer.reference_number},
        )
        create_notification(
            db,
            user_id=customer.user_id,
            type="TRANSFER_COMPLETED",
            title="Transfer completed",
            message=f"{source.currency} {amount} sent to {target_label}. Ref {transfer.reference_number}.",
        )
    else:
        create_notification(
            db,
            user_id=customer.user_id,
            type="TRANSFER_SCHEDULED",
            title="Transfer scheduled",
            message=(
                f"{source.currency} {amount} to {target_label} scheduled for "
                f"{transfer.scheduled_at:%Y-%m-%d %H:%M} UTC. Ref {transfer.reference_number}."
            ),
        )

    if amount >= HIGH_VALUE_TRANSFER_THRESHOLD:
        db.add(
            SecurityEvent(
                user_id=customer.user_id,
                event_type="HIGH_VALUE_TRANSFER",
                ip_address=ctx.ip_address,
                device_info=ctx.user_agent,
                severity="WARNING",
                event_metadata={
                    "transfer_id": str(transfer.id),
                    "amount": str(amount),
                    "payee_verified": payee.is_verified if payee else True,
                },
                created_at=utcnow(),
            )
        )

    await db.commit()
    await db.refresh(transfer)
    return transfer


async def list_transfers(
    db: AsyncSession,
    customer: Customer,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
) -> dict:
    query = select(Transfer).where(Transfer.customer_id == customer.id)
    if status:
        query = query.where(Transfer.status == status)
    query = query.order_by(Transfer.created_at.desc(), Transfer.id)
    return await paginate(db, query, page=page, page_size=page_size)


async def get_transfer(
    db: AsyncSession, customer: Customer, transfer_id: UUID, *, lock: bool = False
) -> Transfer:
    query = select(Transfer).where(
        Transfer.id == transfer_id, Transfer.customer_id == customer.id
    )
    if lock:
        query = query.with_for_update()
    transfer = await db.scalar(query)
    if transfer is None:
        raise NotFoundError("Transfer not found")
    return transfer


async def cancel_transfer(
    db: AsyncSession, customer: Customer, transfer_id: UUID, ctx: RequestContext
) -> Transfer:
    transfer = await get_transfer(db, customer, transfer_id, lock=True)
    if transfer.status not in CUSTOMER_CANCELLABLE:
        raise ConflictError(f"A {transfer.status} transfer cannot be cancelled")

    old_status = transfer.status
    transition(transfer, "CANCELLED")
    write_audit(
        db,
        user_id=customer.user_id,
        action="TRANSFER_CANCELLED",
        entity_type="TRANSFER",
        entity_id=transfer.id,
        ctx=ctx,
        old_value={"status": old_status},
        new_value={"status": "CANCELLED"},
    )
    create_notification(
        db,
        user_id=customer.user_id,
        type="TRANSFER_CANCELLED",
        title="Transfer cancelled",
        message=f"Transfer {transfer.reference_number} was cancelled.",
    )
    await db.commit()
    await db.refresh(transfer)
    return transfer


# ---------------------------------------------------------------------------
# Bills
# ---------------------------------------------------------------------------
async def list_billers(
    db: AsyncSession, *, category: str | None = None, provider_code: str | None = None
) -> list[Biller]:
    query = select(Biller).where(Biller.is_active.is_(True))
    if category:
        query = query.where(Biller.category == category.upper())
    if provider_code:
        query = query.where(Biller.provider_code == provider_code)
    result = await db.scalars(query.order_by(Biller.category, Biller.name))
    return list(result)


async def pay_bill(
    db: AsyncSession, customer: Customer, payload: BillPaymentCreate, ctx: RequestContext
) -> BillPayment:
    amount = to_money(payload.amount)

    biller = await db.scalar(select(Biller).where(Biller.id == payload.biller_id))
    if biller is None or not biller.is_active:
        raise NotFoundError("Biller not found")

    account = await get_owned_account(db, customer.id, payload.account_id, lock=True)
    ensure_account_active(account)
    ensure_sufficient_funds(account, amount)

    reference = generate_reference("BILL")
    debit_account(
        db,
        account,
        amount,
        category="BILL_PAYMENT",
        description=f"Bill payment {reference} to {biller.name}",
        prefix="TXN",
        merchant_name=biller.name,
    )
    payment = BillPayment(
        customer_id=customer.id,
        account_id=account.id,
        biller_id=biller.id,
        amount=amount,
        status="COMPLETED",
        due_date=(
            datetime.combine(payload.due_date, time.min, tzinfo=timezone.utc)
            if payload.due_date
            else None
        ),
        paid_at=utcnow(),
        reference_number=reference,
    )
    db.add(payment)
    await db.flush()

    write_audit(
        db,
        user_id=customer.user_id,
        action="BILL_PAYMENT_COMPLETED",
        entity_type="BILL_PAYMENT",
        entity_id=payment.id,
        ctx=ctx,
        new_value={
            "reference_number": reference,
            "account": mask_account_number(account.account_number),
            "biller": biller.provider_code,
            "amount": amount,
        },
    )
    create_notification(
        db,
        user_id=customer.user_id,
        type="BILL_PAYMENT_COMPLETED",
        title="Bill paid",
        message=f"{account.currency} {amount} paid to {biller.name}. Ref {reference}.",
    )
    await db.commit()
    await db.refresh(payment)
    return payment


async def bill_history(
    db: AsyncSession, customer: Customer, *, page: int, page_size: int
) -> dict:
    query = (
        select(BillPayment)
        .where(BillPayment.customer_id == customer.id)
        .order_by(BillPayment.created_at.desc(), BillPayment.id)
    )
    return await paginate(db, query, page=page, page_size=page_size)
