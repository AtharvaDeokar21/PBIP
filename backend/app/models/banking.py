import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    available_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Transaction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transactions"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True, nullable=False)
    transaction_reference: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(500))
    merchant_name: Mapped[str | None] = mapped_column(String(200))
    merchant_category: Mapped[str | None] = mapped_column(String(100))
    transaction_status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    channel: Mapped[str | None] = mapped_column(String(40))
    is_fraud: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Payee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payees"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_number: Mapped[str] = mapped_column(String(40), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(150))
    ifsc_code: Mapped[str | None] = mapped_column(String(20))
    nickname: Mapped[str | None] = mapped_column(String(100))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Transfer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transfers"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    source_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    destination_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    payee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payees.id"))
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    transfer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    reference_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Biller(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "billers"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    provider_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BillPayment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bill_payments"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    biller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("billers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
