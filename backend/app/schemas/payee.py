from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PayeeCreate(BaseModel):
    name: str
    account_number: str
    bank_name: str
    ifsc_code: str
    nickname: str | None = None


class PayeeResponse(PayeeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    is_verified: bool
    created_at: datetime
    updated_at: datetime