from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ComplianceAlertItemResponse(_CamelModel):
    id: str
    customer_id: str
    customer_name: str
    type: str
    category: str
    severity: str
    status: str
    due_date: str
    raised_at: datetime
    description: str
    assigned_to: str


class ComplianceSummaryResponse(_CamelModel):
    open_count: int
    critical_count: int
    resolved_count: int
    category_counts: dict[str, int]


class ComplianceAlertListResponse(_CamelModel):
    total: int
    page: int
    page_size: int
    items: List[ComplianceAlertItemResponse]
    summary: ComplianceSummaryResponse
