from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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


class LoanEligibilityRequest(BaseModel):
    loan_product_id: UUID
    requested_amount: Decimal
    tenure_months: int


class LoanEligibilityResponse(BaseModel):
    eligible: bool
    eligibility_score: Decimal
    estimated_emi: Decimal
    reason: str


class LoanApplicationCreate(BaseModel):
    loan_product_id: UUID
    requested_amount: Decimal
    tenure_months: int


class LoanApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loan_product_id: UUID
    requested_amount: Decimal
    tenure_months: int
    interest_rate: Decimal
    emi_amount: Decimal
    eligibility_score: Decimal
    status: str
    application_date: datetime