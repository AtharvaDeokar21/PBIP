from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import Customer, User
from app.schemas.auth import CurrentUserResponse

router = APIRouter(prefix="/me", tags=["Authentication"])


@router.get("", response_model=CurrentUserResponse)
async def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
    )
