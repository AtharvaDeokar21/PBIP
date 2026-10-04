from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    RequestContext,
    get_current_customer,
    get_current_user,
    get_request_context,
)
from app.models.identity import Customer
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentProductResponse,
    InvestmentResponse,
)
from app.services import investment_service

router = APIRouter(prefix="/investments", tags=["Investments"])


@router.get(
    "/products",
    response_model=list[InvestmentProductResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_investment_products(
    product_type: str | None = Query(default=None, max_length=50),
    risk_level: str | None = Query(default=None, max_length=30),
    db: AsyncSession = Depends(get_db),
):
    return await investment_service.list_products(
        db, product_type=product_type, risk_level=risk_level
    )


@router.get(
    "/products/{product_id}",
    response_model=InvestmentProductResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_investment_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    return await investment_service.get_product(db, product_id)


@router.get("", response_model=list[InvestmentResponse])
async def get_investments(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await investment_service.list_holdings(db, customer)


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(
    payload: InvestmentCreate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await investment_service.purchase(db, customer, payload, ctx)
