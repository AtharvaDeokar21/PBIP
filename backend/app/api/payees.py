from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequestContext, get_current_customer, get_request_context
from app.models.identity import Customer
from app.schemas.payee import PayeeCreate, PayeeResponse, PayeeUpdate
from app.services import payee_service

router = APIRouter(prefix="/payees", tags=["Payees"])


@router.post("", response_model=PayeeResponse, status_code=status.HTTP_201_CREATED)
async def create_payee(
    payload: PayeeCreate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await payee_service.create_payee(db, customer, payload, ctx)


@router.get("", response_model=list[PayeeResponse])
async def list_payees(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await payee_service.list_payees(db, customer)


@router.patch("/{payee_id}", response_model=PayeeResponse)
async def update_payee(
    payee_id: UUID,
    payload: PayeeUpdate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await payee_service.update_payee(db, customer, payee_id, payload, ctx)


@router.delete("/{payee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payee(
    payee_id: UUID,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await payee_service.deactivate_payee(db, customer, payee_id, ctx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
