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
from app.schemas.loan import (
    LoanApplicationCreate,
    LoanApplicationResponse,
    LoanEligibilityRequest,
    LoanEligibilityResponse,
    LoanProductResponse,
)
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get(
    "/products",
    response_model=list[LoanProductResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_loan_products(
    loan_type: str | None = Query(default=None, max_length=50),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.list_products(db, loan_type=loan_type)


@router.get(
    "/products/{product_id}",
    response_model=LoanProductResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_loan_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    return await loan_service.get_product(db, product_id)


@router.post("/eligibility", response_model=LoanEligibilityResponse)
async def check_eligibility(
    payload: LoanEligibilityRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.check_eligibility(db, customer, payload)


@router.post(
    "/applications",
    response_model=LoanApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_loan(
    payload: LoanApplicationCreate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.apply(db, customer, payload, ctx)


@router.get("/applications", response_model=list[LoanApplicationResponse])
async def get_loan_applications(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.list_applications(db, customer)


@router.get("/applications/{application_id}", response_model=LoanApplicationResponse)
async def get_loan_application(
    application_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.get_application(db, customer, application_id)
