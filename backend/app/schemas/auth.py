from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TokenResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginResponse(TokenResponse):
    role: str
