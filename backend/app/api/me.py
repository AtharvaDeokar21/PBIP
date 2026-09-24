from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user

router = APIRouter(prefix="/me", tags=["Authentication"])


@router.get("")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
