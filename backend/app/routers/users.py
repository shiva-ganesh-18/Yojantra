"""User management router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import UserUpdate, UserResponse, BusinessCreate, BusinessResponse
from app.models import User, Business

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_me(update: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile."""
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    # Mark onboarding complete if essential fields are filled
    if user.full_name and user.state and user.district and user.gender and user.social_category:
        user.onboarding_completed = True

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/me/business", response_model=BusinessResponse)
def create_business(business: BusinessCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create or update business profile."""
    existing = db.query(Business).filter(Business.user_id == user.id).first()

    if existing:
        for field, value in business.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return BusinessResponse.model_validate(existing)

    new_business = Business(user_id=user.id, **business.model_dump())
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    return BusinessResponse.model_validate(new_business)


@router.get("/me/business", response_model=Optional[BusinessResponse])
def get_business(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's business profile."""
    business = db.query(Business).filter(Business.user_id == user.id).first()
    if business:
        return BusinessResponse.model_validate(business)
    return None
