"""Admin dashboard router with strict role-based access control."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import uuid
from app.core.database import get_db
from app.core.security import verify_token
from app.schemas import DashboardMetrics, SchemeCreate, SchemeResponse, UserResponse
from app.models import User, Scheme, Application, UserSchemeMatch, Business

router = APIRouter(prefix="/admin", tags=["Admin"])
security_bearer = HTTPBearer(auto_error=False)


def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Validate Bearer token and ensure user has admin or super_admin role."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    role = payload.get("role", "user")
    if role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin authorization required"
        )

    sub_val = payload.get("sub")
    try:
        user_uuid = uuid.UUID(sub_val) if isinstance(sub_val, str) else sub_val
    except Exception:
        user_uuid = None

    user = db.query(User).filter(User.id == user_uuid).first() if user_uuid else None
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or account disabled"
        )

    return user


@router.get("/analytics/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard metrics with real database counts."""
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.updated_at >= datetime.utcnow() - timedelta(days=1)
    ).count()
    total_schemes = db.query(Scheme).filter(Scheme.status == "active").count()
    total_matches = db.query(UserSchemeMatch).count()
    total_applications = db.query(Application).count()

    # Applications by status
    status_counts = db.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    applications_by_status = {s: c for s, c in status_counts}

    # Top schemes by match count
    top_schemes = db.query(
        Scheme.name, func.count(UserSchemeMatch.id)
    ).join(UserSchemeMatch, Scheme.id == UserSchemeMatch.scheme_id).group_by(Scheme.name).order_by(
        func.count(UserSchemeMatch.id).desc()
    ).limit(5).all()

    # User demographics
    gender_dist = db.query(
        User.gender, func.count(User.id)
    ).filter(User.gender.isnot(None)).group_by(User.gender).all()

    category_dist = db.query(
        User.social_category, func.count(User.id)
    ).filter(User.social_category.isnot(None)).group_by(User.social_category).all()

    return DashboardMetrics(
        total_users=total_users,
        active_users_today=active_today,
        total_schemes=total_schemes,
        total_matches=total_matches,
        total_applications=total_applications,
        applications_by_status=applications_by_status,
        top_schemes=[{"name": name, "matches": count} for name, count in top_schemes],
        user_demographics={
            "gender": {g or "Unspecified": c for g, c in gender_dist},
            "category": {c or "Unspecified": n for c, n in category_dist}
        }
    )


@router.get("/schemes", response_model=List[SchemeResponse])
def admin_list_schemes(
    page: int = 1,
    page_size: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all schemes for admin."""
    schemes = db.query(Scheme).offset((page - 1) * page_size).limit(page_size).all()
    return [SchemeResponse.model_validate(s) for s in schemes]


@router.post("/schemes", response_model=SchemeResponse)
def admin_create_scheme(
    scheme: SchemeCreate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new scheme (admin only)."""
    db_scheme = Scheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return SchemeResponse.model_validate(db_scheme)


@router.get("/users", response_model=List[UserResponse])
def admin_list_users(
    page: int = 1,
    page_size: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List registered entrepreneurs (admin only)."""
    users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/analytics/bias")
def get_bias_report(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get bias audit report across social categories."""
    results = db.query(
        User.social_category,
        func.avg(cast(UserSchemeMatch.match_score, Numeric)).label("avg_score"),
        func.count(UserSchemeMatch.id).label("count")
    ).join(User, UserSchemeMatch.user_id == User.id).group_by(User.social_category).all()

    return {
        "match_scores_by_category": [
            {
                "category": cat or "Not Specified",
                "avg_score": round(float(score), 2) if score is not None else 0.0,
                "count": count
            }
            for cat, score, count in results
        ]
    }


@router.post("/schemes/match-all")
def admin_match_all_schemes(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Trigger scheme matching for all onboarded entrepreneurs (admin only)."""
    from app.services.matching_engine import get_matching_engine

    users = db.query(User).filter(User.onboarding_completed == True).all()
    engine = get_matching_engine(db)
    total_processed = 0
    total_matches = 0

    for u in users:
        try:
            matches = engine.match_user(u.id, refresh=True)
            total_matches += len(matches)
            total_processed += 1
        except Exception:
            continue

    return {
        "status": "success",
        "users_processed": total_processed,
        "total_matches_generated": total_matches
    }

