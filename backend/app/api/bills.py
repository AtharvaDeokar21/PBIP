from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import (
    RequestContext,
    get_current_customer,
    get_current_user,
    get_request_context,
)
from app.models.identity import Customer
from app.schemas.bill import BillerResponse, BillPaymentCreate, BillPaymentResponse
from app.schemas.common import Page
from app.services import payment_service

router = APIRouter(tags=["Bills"])


@router.get(
    "/billers",
    response_model=list[BillerResponse],
    dependencies=[Depends(get_current_user)],
)
async def list_billers(
    category: str | None = Query(default=None, max_length=80),
    provider_code: str | None = Query(default=None, max_length=50),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.list_billers(db, category=category, provider_code=provider_code)


@router.post("/bills/pay", response_model=BillPaymentResponse, status_code=status.HTTP_201_CREATED)
async def pay_bill(
    payload: BillPaymentCreate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.pay_bill(db, customer, payload, ctx)


@router.get("/bills/history", response_model=Page[BillPaymentResponse])
async def bill_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=settings.max_page_size),
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.bill_history(db, customer, page=page, page_size=page_size)
