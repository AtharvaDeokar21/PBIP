from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AIChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None


class AIChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    response: str
    tool_used: str | None = None


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    tool_name: str | None = None
    created_at: datetime