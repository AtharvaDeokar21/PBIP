from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SecurityEventItemResponse(_CamelModel):
    id: str
    event_id: str
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    event_type: str
    channel: str
    severity: str
    status: str
    detected_at: datetime
    description: str
    location: str
    device: str
    ip_address: str


class SecuritySummaryResponse(_CamelModel):
    total_events: int
    critical_count: int
    requires_review_count: int
    logged_count: int
    open_count: int
    resolved_count: int
    severity_counts: Dict[str, int] = Field(default_factory=dict)
    channel_counts: Dict[str, int] = Field(default_factory=dict)


class SecurityEventListResponse(_CamelModel):
    total: int
    page: int
    page_size: int
    items: List[SecurityEventItemResponse]
    summary: SecuritySummaryResponse
