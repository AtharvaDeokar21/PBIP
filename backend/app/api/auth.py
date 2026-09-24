from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Temporary development user. Replace with database-backed auth in the next step.
DEV_USERS = {
    "admin@pbip.local": {
        "password_hash": "$2b$12$LQv3c1yqBWXQy3Qyq3JY2eYxXQ7Jq0qJ4nZQ8YxV2yQ5xP7uKqX7K",
        "role": "ADMIN",
    }
}


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    user = DEV_USERS.get(payload.email.lower())
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return LoginResponse(
        access_token=create_access_token(payload.email, user["role"]),
        role=user["role"],
    )
