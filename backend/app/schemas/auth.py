from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TokenResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)


class RegisterResponse(BaseModel):
    user_id: UUID
    customer_id: UUID
    email: EmailStr
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginResponse(TokenResponse):
    user_id: UUID
    role: str


class CurrentUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    mfa_enabled: bool
