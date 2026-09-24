import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LoanProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loan_products"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    loan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    min_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    max_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    min_tenure_months: Mapped[int] = mapped_column(nullable=False)
    max_tenure_months: Mapped[int] = mapped_column(nullable=False)
    eligibility_rules: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LoanApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loan_applications"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    loan_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_products.id"), nullable=False)
    requested_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    tenure_months: Mapped[int] = mapped_column(nullable=False)
    interest_rate: Mapped[float | None] = mapped_column(Numeric(7, 4))
    emi_amount: Mapped[float | None] = mapped_column(Numeric(18, 2))
    eligibility_score: Mapped[float | None] = mapped_column(Numeric(7, 4))
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", nullable=False)
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)


class InvestmentProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investment_products"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)
    expected_return: Mapped[float | None] = mapped_column(Numeric(7, 4))
    minimum_investment: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    lock_in_period: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CustomerInvestment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_investments"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    investment_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investment_products.id"), nullable=False)
    amount_invested: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    units: Mapped[float | None] = mapped_column(Numeric(18, 6))
    purchase_price: Mapped[float | None] = mapped_column(Numeric(18, 6))
    current_value: Mapped[float | None] = mapped_column(Numeric(18, 2))
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)


class InsuranceProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "insurance_products"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    insurance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    premium: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    coverage_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    term_years: Mapped[int] = mapped_column(nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
