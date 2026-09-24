from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class TransferCreate(BaseModel):
    source_account_id: UUID
    payee_id: UUID
    amount: Decimal
    remarks: str | None = None
    scheduled_at: datetime | None = None


class TransferResponse(BaseModel):
    id: UUID
    source_account_id: UUID
    payee_id: UUID
    amount: Decimal
    transfer_type: str
    status: str
    reference_number: str
    scheduled_at: datetime | None = None
    executed_at: datetime | None = None
    created_at: datetime