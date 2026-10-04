from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Money, StrictRequest


class LoanProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    loan_type: str
    min_amount: Decimal
    max_amount: Decimal
    interest_rate: Decimal
    min_tenure_months: int
    max_tenure_months: int
    description: str | None = None


class LoanEligibilityRequest(StrictRequest):
    loan_product_id: UUID
    requested_amount: Money
    tenure_months: int = Field(ge=1, le=480)


class LoanEligibilityResponse(BaseModel):
    loan_product_id: UUID
    eligible: bool
    eligibility_score: Decimal
    interest_rate: Decimal
    estimated_emi: Decimal
    reasons: list[str]


class LoanApplicationCreate(LoanEligibilityRequest):
    pass


class LoanApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loan_product_id: UUID
    requested_amount: Decimal
    tenure_months: int
    interest_rate: Decimal | None = None
    emi_amount: Decimal | None = None
    eligibility_score: Decimal | None = None
    status: str
    application_date: datetime
    approved_at: datetime | None = None
    rejection_reason: str | None = None
