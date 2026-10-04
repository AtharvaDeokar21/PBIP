from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.core.security import mask_account_number


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

    @field_serializer("account_number")
    def _mask(self, value: str) -> str:
        return mask_account_number(value)


class AccountListResponse(BaseModel):
    items: list[AccountResponse]
    total: int
