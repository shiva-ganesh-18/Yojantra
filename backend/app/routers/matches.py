"""Scheme matching router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import SchemeMatchResponse, MatchRequest
from app.models import User, UserSchemeMatch
from app.services.matching_engine import get_matching_engine

router = APIRouter(prefix="/schemes", tags=["Matching"])


@router.post("/match", response_model=List[SchemeMatchResponse])
def match_schemes(
    request: MatchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find matching schemes for current user."""
    engine = get_matching_engine(db)
    matches = engine.match_user(user.id, refresh=request.refresh)
    return matches


@router.get("/recommended", response_model=List[SchemeMatchResponse])
def get_recommended(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top recommended schemes for user."""
    engine = get_matching_engine(db)
    matches = db.query(UserSchemeMatch).filter(
        UserSchemeMatch.user_id == user.id,
        UserSchemeMatch.is_recommended == True
    ).order_by(UserSchemeMatch.match_score.desc()).all()

    if not matches and user.onboarding_completed:
        engine.match_user(user.id, refresh=True)
        matches = db.query(UserSchemeMatch).filter(
            UserSchemeMatch.user_id == user.id,
            UserSchemeMatch.is_recommended == True
        ).order_by(UserSchemeMatch.match_score.desc()).all()

    return [engine._match_to_response(m) for m in matches]


@router.post("/{scheme_id}/bookmark")
def bookmark_scheme(
    scheme_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bookmark a scheme."""
    match = db.query(UserSchemeMatch).filter(
        UserSchemeMatch.user_id == user.id,
        UserSchemeMatch.scheme_id == scheme_id
    ).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found. Please run matching first.")

    match.is_bookmarked = not match.is_bookmarked
    db.commit()

    return {
        "message": f"Scheme {'bookmarked' if match.is_bookmarked else 'unbookmarked'} successfully",
        "is_bookmarked": match.is_bookmarked
    }
