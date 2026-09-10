"""Authentication and security utilities."""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import hashlib
import secrets
import string
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_secure_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(otp: str, salt: str = "") -> str:
    """Hash OTP for secure persistent verification."""
    combined = f"{otp}:{salt}:{settings.SECRET_KEY}"
    return hashlib.sha256(combined.encode()).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str, salt: str = "") -> bool:
    """Verify submitted OTP against stored hash."""
    return hash_otp(otp, salt) == otp_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_aadhaar(aadhaar: str) -> str:
    """SHA-256 hash of Aadhaar for storage without storing raw Aadhaar."""
    clean = aadhaar.replace(" ", "").replace("-", "")
    return hashlib.sha256(clean.encode()).hexdigest()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> User:
    """Extract authenticated user from Bearer header or fallback token."""
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required in Authorization header or query"
        )

    payload = verify_token(raw_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    sub_raw = payload["sub"]
    user_id = uuid.UUID(sub_raw) if isinstance(sub_raw, str) else sub_raw

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account disabled"
        )

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extract authenticated user if token provided, else None."""
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        return None

    payload = verify_token(raw_token)
    if not payload or not payload.get("sub"):
        return None

    sub_raw = payload["sub"]
    user_id = uuid.UUID(sub_raw) if isinstance(sub_raw, str) else sub_raw
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure authenticated user holds verified admin or super_admin privileges."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required"
        )
    return current_user


def get_current_partner_or_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure authenticated user holds verified partner_officer, nodal_officer, admin, or super_admin privileges."""
    if current_user.role not in ["admin", "super_admin", "partner_officer", "nodal_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Partner Officer, Nodal Officer, or Administrator privileges required"
        )
    return current_user


def check_resource_ownership(
    resource_user_id: uuid.UUID,
    current_user: User,
    resource_type: str = "resource"
) -> None:
    """Enforce IDOR protection: only resource owner or privileged officer/admin can access."""
    if resource_user_id != current_user.id and current_user.role not in [
        "admin", "super_admin", "partner_officer", "nodal_officer"
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized: Access forbidden. You do not have permission to access this {resource_type}."
        )


