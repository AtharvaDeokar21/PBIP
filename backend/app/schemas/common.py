from datetime import datetime
from decimal import Decimal
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StrictRequest(BaseModel):
    """Base for request bodies: unknown fields (e.g. customer_id) are rejected."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# Positive money amount with at most 2 decimal places.
Money = Annotated[Decimal, Field(gt=0, max_digits=16, decimal_places=2)]


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
