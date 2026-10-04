from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InsuranceProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    insurance_type: str
    premium: Decimal
    coverage_amount: Decimal
    term_years: int
    risk_level: str | None = None
    description: str | None = None
