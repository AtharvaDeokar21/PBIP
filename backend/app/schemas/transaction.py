from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    transaction_reference: str
    transaction_type: str
    amount: Decimal
    currency: str
    category: str | None = None
    description: str | None = None
    merchant_name: str | None = None
    merchant_category: str | None = None
    transaction_status: str
    transaction_date: datetime
    location: str | None = None
    channel: str | None = None


class TransactionFilter(BaseModel):
    """Query parameters for account transaction listing."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=settings.max_page_size)
    category: str | None = Field(default=None, max_length=80)
    transaction_type: str | None = Field(default=None, max_length=40)
    transaction_status: str | None = Field(default=None, max_length=30)
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = Field(default=None, ge=0)
    max_amount: Decimal | None = Field(default=None, ge=0)
    search: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def _check_ranges(self) -> "TransactionFilter":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.min_amount > self.max_amount
        ):
            raise ValueError("min_amount must be less than or equal to max_amount")
        return self
