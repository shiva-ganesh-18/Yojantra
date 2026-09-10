"""AI Chat router grounded in verified government scheme knowledge and multi-provider architecture."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.schemas import (
    ChatMessageRequest, 
    ChatMessageResponse,
    ChatStatusResponse,
    EligibilityExplanationRequest,
    EligibilityExplanationResponse,
    LoanEMICalculationRequest,
    LoanEMICalculationResponse
)
from app.models import User
from app.services.chat_service import get_chat_service
from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/chat", tags=["Chat"])
chat_limiter = RateLimiter(requests=30, window_seconds=60, key_prefix="rl_chat")


@router.get("/status", response_model=ChatStatusResponse)
def get_chat_status(
    db: Session = Depends(get_db)
):
    """
    Get current AI/RAG provider configuration, live model availability, indexed scheme count,
    and official statutory limitations.
    """
    service = get_chat_service(db)
    return service.get_provider_status()


@router.post("/message", response_model=ChatMessageResponse, dependencies=[Depends(chat_limiter)])
def chat_message(
    request: ChatMessageRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Send natural-language scheme queries to AI assistant.
    Features grounded retrieval from 63-scheme registry, eligibility insights, loan terms,
    verified source citations, next actions, and mandatory statutory non-approval disclaimer.
    """
    service = get_chat_service(db)
    response = service.process_message(user.id if user else None, request)
    return response


@router.post("/explain-eligibility", response_model=EligibilityExplanationResponse)
def explain_eligibility(
    request: EligibilityExplanationRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Provide detailed, explainable breakdown of why an applicant qualifies or is disqualified for a scheme.
    Details satisfied conditions, missing requirements, affirmative margin benefits, and regulatory document purposes.
    """
    service = get_chat_service(db)
    try:
        return service.explain_eligibility(
            scheme_id=request.scheme_id,
            user_id=user.id if user else None,
            custom_profile=request.custom_profile
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/calculate-loan", response_model=LoanEMICalculationResponse)
def calculate_loan(
    request: LoanEMICalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate indicative monthly EMI, total repayment, capital subsidy margin, and project moratorium period.
    Explicitly clarifies that final terms depend on financing bank credit appraisal.
    """
    service = get_chat_service(db)
    try:
        return service.calculate_loan_emi(
            scheme_id=request.scheme_id,
            loan_amount_inr=request.loan_amount_inr,
            tenure_months=request.tenure_months
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/voice")
def chat_voice(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Upload voice message and get AI response."""
    return {
        "transcript": "Voice processing not yet implemented",
        "reply_audio_url": None,
        "reply_text": "Please use text chat for now. Multilingual voice synthesis is currently configuration-ready!"
    }

