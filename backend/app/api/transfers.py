from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import RequestContext, get_current_customer, get_request_context
from app.models.identity import Customer
from app.schemas.common import Page
from app.schemas.transfer import TransferCreate, TransferResponse, TransferStatus
from app.services import payment_service

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferCreate,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.create_transfer(db, customer, payload, ctx)


@router.get("", response_model=Page[TransferResponse])
async def list_transfers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=settings.max_page_size),
    transfer_status: TransferStatus | None = Query(default=None, alias="status"),
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.list_transfers(
        db, customer, page=page, page_size=page_size, status=transfer_status
    )


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.get_transfer(db, customer, transfer_id)


@router.post("/{transfer_id}/cancel", response_model=TransferResponse)
async def cancel_transfer(
    transfer_id: UUID,
    customer: Customer = Depends(get_current_customer),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.cancel_transfer(db, customer, transfer_id, ctx)
