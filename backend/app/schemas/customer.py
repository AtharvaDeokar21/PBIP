from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import StrictRequest


class CustomerResponse(BaseModel):
    id: UUID
    customer_number: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    occupation: str | None = None
    employment_type: str | None = None
    annual_income: Decimal | None = None
    risk_profile: str | None = None
    customer_segment: str | None = None


class CustomerUpdate(StrictRequest):
    """Fields a customer may change themselves.

    Income, risk profile and segment are bank-controlled and not editable here.
    """

    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    address: str | None = Field(default=None, min_length=1, max_length=500)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, pattern=r"^[0-9A-Za-z\- ]{3,20}$")
    occupation: str | None = Field(default=None, min_length=1, max_length=150)


class AccountTypeBalance(BaseModel):
    account_type: str
    balance: Decimal
    account_count: int


class CustomerSummary(BaseModel):
    currency: str = "INR"
    total_balance: Decimal
    total_available_balance: Decimal
    total_accounts: int
    active_accounts: int
    balances_by_type: list[AccountTypeBalance]
    month_to_date_credits: Decimal
    month_to_date_debits: Decimal
    active_payees: int
    open_loan_applications: int
    total_invested: Decimal
