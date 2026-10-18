from datetime import datetime
from typing import List, Optional
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


class AuditLogItemResponse(_CamelModel):
    id: str
    actor: str
    actor_role: str
    action: str
    resource: str
    resource_id: str
    outcome: str
    ip_address: str
    timestamp: datetime
    customer_id: Optional[str] = None


class AuditSummaryResponse(_CamelModel):
    total_events: int
    success_count: int
    failure_count: int
    warning_count: int
    available_actors: List[str] = Field(default_factory=list)
    available_actions: List[str] = Field(default_factory=list)


class AuditLogListResponse(_CamelModel):
    total: int
    page: int
    page_size: int
    items: List[AuditLogItemResponse]
    summary: AuditSummaryResponse
