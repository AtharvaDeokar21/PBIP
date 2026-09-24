from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User


router = APIRouter(
    prefix="/investments",
    tags=["Investments"],
)


@router.get("/products")
async def get_investment_products(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Investment products will be implemented here"
    }


@router.get("")
async def get_investments(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Customer investments will be implemented here"
    }