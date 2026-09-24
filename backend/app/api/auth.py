from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import (
    AuthenticationError,
    authenticate_user,
    register_customer,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    try:
        user, customer = await register_customer(
            db,
            email=str(payload.email),
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RegisterResponse(
        user_id=user.id,
        customer_id=customer.id,
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    try:
        user = await authenticate_user(
            db,
            email=str(payload.email),
            password=payload.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return LoginResponse(
        access_token=create_access_token(user.id, user.role),
        user_id=user.id,
        role=user.role,
    )
