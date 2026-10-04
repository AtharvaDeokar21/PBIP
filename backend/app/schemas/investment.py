from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Money, StrictRequest


class InvestmentProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    product_type: str
    risk_level: str
    expected_return: Decimal | None = None
    minimum_investment: Decimal
    lock_in_period: str | None = None
    description: str | None = None


class InvestmentCreate(StrictRequest):
    """Simulated investment purchase.

    If ``source_account_id`` is given, the amount is debited from that account.
    """

    investment_product_id: UUID
    amount_invested: Money
    source_account_id: UUID | None = None


class InvestmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investment_product_id: UUID
    amount_invested: Decimal
    units: Decimal | None = None
    purchase_price: Decimal | None = None
    current_value: Decimal | None = None
    purchase_date: date
    status: str
