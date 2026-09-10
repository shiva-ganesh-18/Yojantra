"""Authentication router - Google Firebase Authentication."""
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    verify_token,
    get_current_user
)
from app.core.firebase import (
    verify_firebase_token,
    is_firebase_configured,
    FirebaseNotConfiguredError,
    InvalidFirebaseTokenError
)
from app.core.rate_limit import RateLimiter
from app.models import User
from app.schemas import (
    GoogleAuthRequest,
    TokenResponse,
    UserResponse
)
from app.routers.users import build_user_response

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
auth_rate_limiter = RateLimiter(requests=20, window_seconds=60, key_prefix="rl_auth")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/config")
def get_auth_config():
    """Return available authentication providers configuration."""
    return {
        "google_auth": is_firebase_configured(),
        "phone_auth": False,
        "dev_otp_allowed": False
    }


@router.post("/google", response_model=TokenResponse, dependencies=[Depends(auth_rate_limiter)])
def authenticate_google(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate user via verified Firebase Google ID Token.
    Validates token via Firebase Admin SDK (never trusting client metadata).
    Links accounts by verified email if matching, or creates new beneficiary user.
    Always defaults new accounts to role='user' (beneficiary).
    """
    try:
        token_data = verify_firebase_token(request.id_token)
    except FirebaseNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server. Please contact administrator."
        )
    except InvalidFirebaseTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication failed: {str(exc)}"
        )

    firebase_uid = token_data.get("uid")
    email = token_data.get("email")
    email_verified = token_data.get("email_verified", False)
    name = token_data.get("name") or ""
    picture = token_data.get("picture") or ""

    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential: Missing UID."
        )

    # 1. Search for existing user with this firebase_uid
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if user:
        # Existing user logging in via Google
        if not user.full_name and name:
            user.full_name = name
        if not user.avatar_url and picture:
            user.avatar_url = picture
        db.commit()
    else:
        # 2. Check if an existing user has the exact verified email (Safe Account Linking)
        existing_by_email = None
        if email and email_verified:
            existing_by_email = db.query(User).filter(User.email == email).first()

        if existing_by_email:
            user = existing_by_email
            user.firebase_uid = firebase_uid
            user.auth_provider = "google"
            if not user.avatar_url and picture:
                user.avatar_url = picture
            if not user.full_name and name:
                user.full_name = name
            db.commit()
        else:
            # 3. Create a brand new user
            user = User(
                firebase_uid=firebase_uid,
                email=email if email else None,
                full_name=name,
                avatar_url=picture,
                auth_provider="google",
                role="user",  # CRITICAL: Always default to beneficiary ('user'), never admin
                is_active=True,
                onboarding_completed=False,
                state="",
                district=""
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support."
        )

    # Generate standard Yojantra JWT
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email or "",
        "role": user.role or "user"
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=build_user_response(user, db)
    )


@router.post("/link/google", response_model=UserResponse)
def link_google_account(
    request: GoogleAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link a Google account to the currently authenticated user session.
    Verifies Firebase token and ensures no other account is already bound to this Google UID.
    """
    try:
        token_data = verify_firebase_token(request.id_token)
    except FirebaseNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server."
        )
    except InvalidFirebaseTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google credentials: {str(exc)}"
        )

    firebase_uid = token_data.get("uid")
    picture = token_data.get("picture")

    # Check if another user already owns this Google UID
    existing_owner = db.query(User).filter(
        User.firebase_uid == firebase_uid,
        User.id != current_user.id
    ).first()

    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Google account is already linked to another Yojantra profile."
        )

    current_user.firebase_uid = firebase_uid
    current_user.auth_provider = "google"
    if picture and not current_user.avatar_url:
        current_user.avatar_url = picture
    db.commit()
    db.refresh(current_user)

    return build_user_response(current_user, db)


@router.post("/refresh")
def refresh_token(token: str, db: Session = Depends(get_db)):
    """Refresh JWT token and verify user status."""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    new_token = create_access_token({
        "sub": str(user.id),
        "email": user.email or "",
        "role": user.role or "user"
    })
    return {"access_token": new_token, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Log out current user and acknowledge session termination."""
    return {"message": "Successfully logged out from Yojantra", "status": "success"}

