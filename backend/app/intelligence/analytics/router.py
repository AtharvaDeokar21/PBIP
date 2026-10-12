from datetime import date
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.intelligence.analytics.schemas import (
    AnalyticsOverviewResponse,
    BehaviourAnalyticsResponse,
    BehaviourFiltersResponse,
    CustomerDirectoryResponse,
)
from app.intelligence.analytics.service import BehaviourAnalyticsService

router = APIRouter(prefix="/analytics/behaviour", tags=["Analytics"])
overview_router = APIRouter(prefix="/analytics", tags=["Analytics"])

INTERNAL_ROLES = (
    "ADMIN",
    "RELATIONSHIP_MANAGER",
    "FRAUD_ANALYST",
    "COMPLIANCE_OFFICER",
)


@overview_router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Get the internal dashboard overview",
    description=(
        "Returns real customer, behaviour, transaction and fraud data for the "
        "internal dashboard. All internal roles can access it; CUSTOMER users "
        "receive HTTP 403."
    ),
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_analytics_overview(
    as_of: Optional[date] = Query(
        None,
        description="Include records through this date; defaults to the latest behaviour event date.",
    ),
    db: AsyncSession = Depends(get_db),
):
    return await BehaviourAnalyticsService(db).get_overview(as_of=as_of)

@router.get("", response_model=BehaviourAnalyticsResponse, dependencies=[Depends(require_roles("ADMIN", "RELATIONSHIP_MANAGER"))])
async def get_behaviour_analytics(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    segment: Optional[str] = None,
    product: Optional[str] = None,
    customer_id: Optional[uuid.UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = BehaviourAnalyticsService(db)
    return await service.get_analytics(
        date_from=date_from,
        date_to=date_to,
        segment=segment,
        product=product,
        customer_id=customer_id,
        page=page,
        page_size=page_size
    )

@router.get("/filters", response_model=BehaviourFiltersResponse, dependencies=[Depends(require_roles("ADMIN", "RELATIONSHIP_MANAGER"))])
async def get_behaviour_filters(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = BehaviourAnalyticsService(db)
    return await service.get_filters(search=search)


@overview_router.get(
    "/customers",
    response_model=CustomerDirectoryResponse,
    summary="Get the internal customer directory",
    description=(
        "Returns live customer directory rows and unfiltered KPI counts. "
        "All internal roles can access it; CUSTOMER users receive HTTP 403. "
        "Search, filters, sorting and pagination are applied server-side."
    ),
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_customer_directory(
    q: str | None = Query(None, description="Search name, customer number, or email"),
    search: str | None = Query(None, description="Alias for q"),
    risk: str | None = Query(None, description="LOW, MEDIUM, HIGH, or CRITICAL"),
    alerts: str | None = Query(None, description="active or none"),
    segment: str | None = Query(None, description="Customer segment code"),
    sort: str = Query("name", description="name, name_desc, or risk"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CustomerDirectoryResponse:
    return await BehaviourAnalyticsService(db).get_customer_directory(
        search=q or search,
        risk=risk,
        alerts=alerts,
        segment=segment,
        sort=sort,
        page=page,
        page_size=page_size,
    )
