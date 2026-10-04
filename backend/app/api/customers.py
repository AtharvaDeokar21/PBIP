from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequestContext, get_current_customer, get_request_context
from app.models.identity import Customer
from app.schemas.customer import CustomerResponse, CustomerSummary, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/me", response_model=CustomerResponse)
async def get_my_profile(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    return await customer_service.get_profile(db, customer)


@router.patch("/me", response_model=CustomerResponse)
async def update_my_profile(
    payload: CustomerUpdate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    return await customer_service.update_profile(db, customer, payload, ctx)


@router.get("/me/summary", response_model=CustomerSummary)
async def get_my_financial_summary(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> CustomerSummary:
    return await customer_service.get_financial_summary(db, customer)
