from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FraudAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fraud_event_id: UUID
    customer_id: UUID
    status: str
    priority: str
    assigned_to: UUID | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class FraudAlertUpdate(BaseModel):
    status: str
    resolution_notes: str | None = None


class FraudRiskResponse(BaseModel):
    customer_id: UUID
    fraud_risk_score: Decimal
    risk_level: str