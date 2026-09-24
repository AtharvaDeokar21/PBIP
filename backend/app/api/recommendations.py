from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get("")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Recommendations will be implemented here"
    }