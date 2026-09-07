"""Authentication router - Secure OTP-based login with role support."""
from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    generate_secure_otp,
    hash_otp,
    verify_otp_hash,
    verify_token
)
from app.models import User, OTPVerification
from app.schemas import OTPSendRequest, OTPVerifyRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/otp/send", status_code=status.HTTP_200_OK)
def send_otp(request: OTPSendRequest, db: Session = Depends(get_db)):
    """Send secure random OTP to user's phone number with rate-limiting."""
    now = datetime.utcnow()

    # Rate limiting: check recent OTP sent within 60 seconds
    recent_otp = db.query(OTPVerification).filter(
        OTPVerification.phone == request.phone,
        OTPVerification.created_at >= now - timedelta(seconds=60)
    ).first()

    if recent_otp:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please wait 60 seconds before requesting another OTP."
        )

    # Invalidate old unused OTPs for this phone
    db.query(OTPVerification).filter(
        OTPVerification.phone == request.phone,
        OTPVerification.is_verified == False
    ).delete()

    # Determine OTP code: secure random by default, or dev OTP if explicitly enabled
    if settings.ALLOW_DEV_OTP:
        otp = settings.DEV_OTP_CODE
    else:
        otp = generate_secure_otp(6)

    # Hash OTP with phone salt
    otp_record = OTPVerification(
        phone=request.phone,
        otp_hash=hash_otp(otp, salt=request.phone),
        attempts=0,
        max_attempts=settings.MAX_OTP_ATTEMPTS,
        is_verified=False,
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    )
    db.add(otp_record)
    db.commit()

    # Masked log for security
    masked_phone = request.phone[:3] + "******" + request.phone[-2:]
    if settings.DEBUG or settings.ALLOW_DEV_OTP:
        print(f"[AUTH] Dev OTP for {masked_phone}: {otp}")
    else:
        print(f"[AUTH] Secure OTP generated and dispatched for {masked_phone}")

    response_data = {
        "message": "OTP sent successfully",
        "phone": request.phone
    }
    if settings.ALLOW_DEV_OTP or settings.DEBUG:
        response_data["dev_otp"] = otp

    return response_data


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP against stored hash and return JWT access token with role."""
    now = datetime.utcnow()

    # Find latest unverified OTP record
    record = db.query(OTPVerification).filter(
        OTPVerification.phone == request.phone,
        OTPVerification.is_verified == False
    ).order_by(OTPVerification.created_at.desc()).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found or already used. Please request a new one."
        )

    if now > record.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please request a new one."
        )

    if record.attempts >= record.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum OTP verification attempts exceeded. Please request a new OTP."
        )

    # Check OTP verification
    is_valid = verify_otp_hash(request.otp, record.otp_hash, salt=request.phone)
    if not is_valid and settings.ALLOW_DEV_OTP and request.otp == settings.DEV_OTP_CODE:
        is_valid = True

    if not is_valid:
        record.attempts += 1
        db.commit()
        remaining = record.max_attempts - record.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining."
        )

    # Mark OTP as verified
    record.is_verified = True
    db.commit()

    # Find or create user
    user = db.query(User).filter(User.phone == request.phone).first()

    if not user:
        user = User(
            phone=request.phone,
            full_name="",
            state="",
            district="",
            role="user",
            onboarding_completed=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create token with identity and role
    token = create_access_token({
        "sub": str(user.id),
        "phone": user.phone,
        "role": user.role or "user"
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


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
        "phone": user.phone,
        "role": user.role or "user"
    })
    return {"access_token": new_token, "token_type": "bearer"}
