from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_number: str
    account_type: str
    currency: str
    balance: Decimal
    available_balance: Decimal
    status: str
    opened_at: datetime | None = None
    created_at: datetime


class AccountSummary(BaseModel):
    total_balance: Decimal
    total_accounts: int
    currency: str = "INR"