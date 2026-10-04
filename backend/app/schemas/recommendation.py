from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_type: str
    product_id: UUID
    recommendation_type: str
    score: Decimal
    reason: str | None = None
    status: str
    created_at: datetime
    expires_at: datetime | None = None
