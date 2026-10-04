from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Money, StrictRequest


class BillerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: str | None = None
    provider_code: str
    is_active: bool


class BillPaymentCreate(StrictRequest):
    account_id: UUID
    biller_id: UUID
    amount: Money
    due_date: date | None = None


class BillPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    biller_id: UUID
    amount: Decimal
    status: str
    due_date: datetime | None = None
    paid_at: datetime | None = None
    reference_number: str
    created_at: datetime
