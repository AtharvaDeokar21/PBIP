"""Read-only exposure of recommendations produced by the Internal/Analytics team."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Customer
from app.models.intelligence import Recommendation
from app.services.common import utcnow


async def list_recommendations(
    db: AsyncSession, customer: Customer, *, product_type: str | None = None
) -> list[Recommendation]:
    query = select(Recommendation).where(
        Recommendation.customer_id == customer.id,
        Recommendation.status == "ACTIVE",
        or_(Recommendation.expires_at.is_(None), Recommendation.expires_at > utcnow()),
    )
    if product_type:
        query = query.where(Recommendation.product_type == product_type.upper())
    result = await db.scalars(query.order_by(Recommendation.score.desc()))
    return list(result)
