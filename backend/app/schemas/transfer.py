from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import Money, StrictRequest

TransferType = Literal["IMMEDIATE", "SCHEDULED"]
TransferStatus = Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED", "SCHEDULED"]

MAX_SCHEDULE_AHEAD = timedelta(days=365)


class TransferCreate(StrictRequest):
    """Transfer to a saved payee, or to another of the customer's own accounts.

    Exactly one of ``payee_id`` / ``destination_account_id`` must be supplied.
    """

    source_account_id: UUID
    payee_id: UUID | None = None
    destination_account_id: UUID | None = None
    amount: Money
    transfer_type: TransferType = "IMMEDIATE"
    scheduled_at: datetime | None = None
    remarks: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _validate(self) -> "TransferCreate":
        if (self.payee_id is None) == (self.destination_account_id is None):
            raise ValueError("Provide exactly one of payee_id or destination_account_id")
        if self.destination_account_id == self.source_account_id:
            raise ValueError("Source and destination accounts must differ")

        if self.transfer_type == "SCHEDULED":
            if self.scheduled_at is None:
                raise ValueError("scheduled_at is required for SCHEDULED transfers")
            if self.scheduled_at.tzinfo is None:
                self.scheduled_at = self.scheduled_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if self.scheduled_at <= now:
                raise ValueError("scheduled_at must be in the future")
            if self.scheduled_at > now + MAX_SCHEDULE_AHEAD:
                raise ValueError("scheduled_at cannot be more than 1 year ahead")
        elif self.scheduled_at is not None:
            raise ValueError("scheduled_at is only allowed for SCHEDULED transfers")
        return self


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_account_id: UUID
    destination_account_id: UUID | None = None
    payee_id: UUID | None = None
    amount: Decimal
    transfer_type: str
    status: str
    reference_number: str
    scheduled_at: datetime | None = None
    executed_at: datetime | None = None
    created_at: datetime
