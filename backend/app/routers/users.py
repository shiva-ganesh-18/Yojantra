"""User management router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import UserUpdate, UserResponse, BusinessCreate, BusinessResponse
from app.models import User, Business
from app.routers.locations import validate_state_and_district, is_valid_district_for_state

router = APIRouter(prefix="/users", tags=["Users"])


def calculate_profile_completion(user: User, business: Optional[Business] = None) -> int:
    """
    Calculate profile completion score (0-100%).
    Required fields:
    - full_name: 15%
    - phone: 15% (CRITICAL: Active Mobile Number is required for nodal SMS & verification.
                  If phone is missing, profile completion CANNOT exceed 70% and CAN NEVER BE 100%!)
    - state & district: 15% (7.5% state, 7.5% district, only if district is valid for state)
    - social_category: 10%
    - date_of_birth: 10%
    - gender: 5%
    - business_name & business_type: 15%
    - annual_turnover_inr or funding_needed_inr: 15%
    """
    score = 0
    if user.full_name and len(user.full_name.strip()) > 1:
        score += 15
    if user.phone and len(user.phone.strip()) >= 10:
        score += 15
    if user.state:
        score += 7
        if user.district and is_valid_district_for_state(user.state, user.district):
            score += 8
    if user.social_category:
        score += 10
    if user.date_of_birth:
        score += 10
    if user.gender:
        score += 5

    biz = business or getattr(user, "business", None)
    if biz:
        if biz.business_name and len(biz.business_name.strip()) > 1:
            score += 10
        if biz.business_type:
            score += 5
        if biz.annual_turnover_inr is not None or biz.funding_needed_inr is not None:
            score += 15

    # CRITICAL: Missing phone or location strictly caps profile completion at max 70%
    if not user.phone or len(user.phone.strip()) < 10:
        score = min(70, score)
    if not user.state or not user.district or not is_valid_district_for_state(user.state, user.district):
        score = min(70, score)

    return int(min(100, max(0, score)))


def build_user_response(user: User, db: Optional[Session] = None) -> UserResponse:
    """Build UserResponse with truthful location validation and profile completion percentage."""
    resp = UserResponse.model_validate(user)
    # Suppress invalid state/district combination (e.g. Patna, Tamil Nadu)
    if resp.state and resp.district and not is_valid_district_for_state(resp.state, resp.district):
        resp.district = ""

    biz = None
    if db:
        biz = db.query(Business).filter(Business.user_id == user.id).first()
    elif hasattr(user, "business") and user.business:
        biz = user.business

    resp.profile_completion_percentage = calculate_profile_completion(user, biz)
    return resp


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile."""
    return build_user_response(user, db)


@router.put("/me", response_model=UserResponse)
def update_me(update: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile with privilege escalation protection and location integrity."""
    dumped = update.model_dump(exclude_unset=True)

    # Validate state and district integrity
    cand_state = dumped.get("state", user.state)
    cand_dist = dumped.get("district", user.district)
    if ("state" in dumped or "district" in dumped) and (cand_state or cand_dist):
        is_valid, err_msg = validate_state_and_district(cand_state, cand_dist)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err_msg)

    PROTECTED_FIELDS = {"role", "is_active", "is_superuser", "id", "created_at", "updated_at", "firebase_uid"}
    for field, value in dumped.items():
        if field not in PROTECTED_FIELDS:
            if field == "phone" and value is not None:
                clean_phone = str(value).strip()
                if clean_phone and clean_phone != user.phone:
                    existing_user = db.query(User).filter(User.phone == clean_phone, User.id != user.id).first()
                    if existing_user:
                        raise HTTPException(status_code=400, detail="Mobile number already registered to another account")
                    user.phone = clean_phone
                elif not clean_phone:
                    user.phone = None
            else:
                setattr(user, field, value)

    # Automatically complete onboarding if essential profile fields are present,
    # or honor explicitly supplied onboarding_completed
    if update.onboarding_completed is not None:
        user.onboarding_completed = update.onboarding_completed
    elif (
        user.full_name 
        and user.state 
        and user.district 
        and is_valid_district_for_state(user.state, user.district)
        and user.gender 
        and user.social_category
    ):
        user.onboarding_completed = True

    db.commit()
    db.refresh(user)
    return build_user_response(user, db)


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
