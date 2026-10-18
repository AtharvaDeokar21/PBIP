from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class InvestigationItemResponse(_CamelModel):
    id: str
    alert_id: str
    customer_id: Optional[str] = None
    customer_name: str
    type: str
    severity: str
    status: str
    assigned_to: str
    opened_at: datetime
    updated_at: datetime
    notes: List[str] = Field(default_factory=list)
    risk_score: float
    amount: Optional[float] = None


class InvestigationListResponse(_CamelModel):
    total: int
    page: int
    page_size: int
    items: List[InvestigationItemResponse]


class FraudAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fraud_event_id: UUID
    customer_id: UUID
    status: str
    priority: int
    assigned_to: UUID | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


CANONICAL_ALERT_STATUSES = {"OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED", "FALSE_POSITIVE"}

STATUS_NORMALIZATION_MAP: dict[str, str] = {
    "OPEN": "OPEN",
    "IN_REVIEW": "IN_REVIEW",
    "IN REVIEW": "IN_REVIEW",
    "ESCALATED": "ESCALATED",
    "RESOLVED": "RESOLVED",
    "FALSE_POSITIVE": "FALSE_POSITIVE",
    "FALSE POSITIVE": "FALSE_POSITIVE",
}


class FraudAlertUpdate(BaseModel):
    status: str
    resolution_notes: str | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_and_validate_status(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Status must be a string")
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Status cannot be empty")
        upper_val = trimmed.upper()
        if upper_val in STATUS_NORMALIZATION_MAP:
            return STATUS_NORMALIZATION_MAP[upper_val]
        clean = upper_val.replace("-", "_").replace(" ", "_")
        while "__" in clean:
            clean = clean.replace("__", "_")
        if clean in CANONICAL_ALERT_STATUSES:
            return clean
        allowed_list = ", ".join(sorted(CANONICAL_ALERT_STATUSES))
        raise ValueError(f"Invalid alert status '{value}'. Allowed statuses: {allowed_list}")


class FraudRiskResponse(BaseModel):
    customer_id: UUID
    fraud_risk_score: Decimal
    risk_level: str