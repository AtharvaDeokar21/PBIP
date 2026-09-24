from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_number: str
    first_name: str
    last_name: str
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    occupation: str | None = None
    employment_type: str | None = None
    annual_income: Decimal | None = None
    risk_profile: str | None = None
    customer_segment: str | None = None
    created_at: datetime