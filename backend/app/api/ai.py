from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.ai import AIChatRequest


router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"],
)


@router.post("/chat")
async def chat(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "AI assistant will be implemented here",
        "user_message": payload.message,
    }


@router.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Conversations will be implemented here"
    }