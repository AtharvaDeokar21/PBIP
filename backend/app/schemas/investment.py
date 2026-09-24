from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvestmentProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    product_type: str
    risk_level: str
    expected_return: Decimal
    minimum_investment: Decimal
    description: str | None = None


class InvestmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investment_product_id: UUID
    amount_invested: Decimal
    units: Decimal
    purchase_price: Decimal
    current_value: Decimal
    purchase_date: datetime
    status: str