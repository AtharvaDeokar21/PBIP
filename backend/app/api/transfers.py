from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.transfer import TransferCreate


router = APIRouter(
    prefix="/transfers",
    tags=["Transfers"],
)


@router.post("")
async def create_transfer(
    payload: TransferCreate,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Transfer creation will be implemented here",
        "data": payload,
    }


@router.get("")
async def get_transfers(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Transfer listing will be implemented here"
    }