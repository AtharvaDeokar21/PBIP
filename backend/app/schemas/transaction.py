from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    channel: str | None = None
    is_fraud: bool