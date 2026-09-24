import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BehaviourEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "behaviour_events"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    page: Mapped[str | None] = mapped_column(String(200))
    action: Mapped[str | None] = mapped_column(String(200))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    device_type: Mapped[str | None] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


class CustomerRiskProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_risk_profiles"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), unique=True, nullable=False)
    risk_tolerance: Mapped[str | None] = mapped_column(String(30))
    credit_score: Mapped[int | None]
    fraud_risk_score: Mapped[float | None] = mapped_column(Numeric(7, 4))
    financial_health_score: Mapped[float | None] = mapped_column(Numeric(7, 4))
    savings_ratio: Mapped[float | None] = mapped_column(Numeric(7, 4))
    debt_to_income_ratio: Mapped[float | None] = mapped_column(Numeric(7, 4))
    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Recommendation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "recommendations"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), index=True, nullable=False)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
