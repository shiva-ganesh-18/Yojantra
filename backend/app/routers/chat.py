"""AI Chat router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.schemas import ChatMessageRequest, ChatMessageResponse
from app.models import User
from app.services.chat_service import get_chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatMessageResponse)
def chat_message(
    request: ChatMessageRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Send a message to AI assistant."""
    service = get_chat_service(db)
    response = service.process_message(user.id if user else None, request)
    return response


@router.post("/voice")
def chat_voice(
    # In production: accept audio file, transcribe with Whisper
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Upload voice message and get AI response."""
    # TODO: Implement voice processing
    return {
        "transcript": "Voice processing not yet implemented",
        "reply_audio_url": None,
        "reply_text": "Please use text chat for now. Voice support is coming soon!"
    }
