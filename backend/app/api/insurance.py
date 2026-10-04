from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.insurance import InsuranceProductResponse
from app.services import insurance_service

# Catalogue only: no underwriting/purchase workflow in the current scope.
router = APIRouter(
    prefix="/insurance",
    tags=["Insurance"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/products", response_model=list[InsuranceProductResponse])
async def get_insurance_products(
    insurance_type: str | None = Query(default=None, max_length=50),
    risk_level: str | None = Query(default=None, max_length=30),
    db: AsyncSession = Depends(get_db),
):
    return await insurance_service.list_products(
        db, insurance_type=insurance_type, risk_level=risk_level
    )


@router.get("/products/{product_id}", response_model=InsuranceProductResponse)
async def get_insurance_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    return await insurance_service.get_product(db, product_id)
