from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.security import mask_account_number
from app.schemas.common import StrictRequest

IFSC_PATTERN = r"^[A-Z]{4}0[A-Z0-9]{6}$"
ACCOUNT_NUMBER_PATTERN = r"^[0-9]{9,18}$"


class PayeeCreate(StrictRequest):
    name: str = Field(min_length=1, max_length=150)
    account_number: str = Field(pattern=ACCOUNT_NUMBER_PATTERN)
    bank_name: str = Field(min_length=1, max_length=150)
    ifsc_code: str = Field(pattern=IFSC_PATTERN)
    nickname: str = Field(min_length=1, max_length=100)

    @field_validator("ifsc_code", mode="before")
    @classmethod
    def _upper_ifsc(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class PayeeUpdate(StrictRequest):
    """Editable payee fields. Changing bank details requires a new payee."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    bank_name: str | None = Field(default=None, min_length=1, max_length=150)
    nickname: str | None = Field(default=None, min_length=1, max_length=100)


class PayeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    account_number: str
    bank_name: str | None = None
    ifsc_code: str | None = None
    nickname: str | None = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("account_number")
    def _mask(self, value: str) -> str:
        return mask_account_number(value)
