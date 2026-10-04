from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.products import InsuranceProduct


async def list_products(
    db: AsyncSession, *, insurance_type: str | None = None, risk_level: str | None = None
) -> list[InsuranceProduct]:
    query = select(InsuranceProduct).where(InsuranceProduct.is_active.is_(True))
    if insurance_type:
        query = query.where(InsuranceProduct.insurance_type == insurance_type.upper())
    if risk_level:
        query = query.where(InsuranceProduct.risk_level == risk_level.upper())
    result = await db.scalars(query.order_by(InsuranceProduct.name))
    return list(result)


async def get_product(db: AsyncSession, product_id: UUID) -> InsuranceProduct:
    product = await db.scalar(
        select(InsuranceProduct).where(
            InsuranceProduct.id == product_id, InsuranceProduct.is_active.is_(True)
        )
    )
    if product is None:
        raise NotFoundError("Insurance product not found")
    return product
