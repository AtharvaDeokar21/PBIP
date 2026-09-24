from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
