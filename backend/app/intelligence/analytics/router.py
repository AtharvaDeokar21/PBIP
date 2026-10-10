from datetime import date
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.intelligence.analytics.schemas import BehaviourAnalyticsResponse, BehaviourFiltersResponse
from app.intelligence.analytics.service import BehaviourAnalyticsService

router = APIRouter(prefix="/analytics/behaviour", tags=["Analytics"])

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
