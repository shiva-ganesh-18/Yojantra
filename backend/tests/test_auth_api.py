"""Tests for Authentication & RBAC Authorization."""
import pytest
from datetime import datetime, timedelta, timezone
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_otp
from app.models import User, OTPVerification


def test_send_otp_success(test_db, client):
    """Test sending OTP to a valid Indian phone number."""
    response = client.post("/auth/otp/send", json={"phone": "+919876543210"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # Verify OTP was stored in DB
    otp_record = test_db.query(OTPVerification).filter(OTPVerification.phone == "+919876543210").first()
    assert otp_record is not None
    assert otp_record.is_verified is False


def test_send_otp_invalid_phone(client):
    """Test validation rejection on invalid phone format."""
    response = client.post("/auth/otp/send", json={"phone": "12345"})
    assert response.status_code == 422


def test_verify_otp_success_and_jwt_generation(test_db, client):
    """Test verifying a valid OTP returns a valid JWT with user info."""
    phone = "+919876543211"
    # Seed OTP
    otp_code = "654321"
    otp_record = OTPVerification(
        phone=phone,
        otp_hash=hash_otp(otp_code, salt=phone),
        attempts=0,
        max_attempts=5,
        is_verified=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    test_db.add(otp_record)
    test_db.commit()

    response = client.post("/auth/otp/verify", json={"phone": phone, "otp": otp_code})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["phone"] == phone


def test_verify_otp_invalid_code(test_db, client):
    """Test invalid OTP code increments attempt count and rejects with 400."""
    phone = "+919876543212"
    otp_record = OTPVerification(
        phone=phone,
        otp_hash=hash_otp("111111", salt=phone),
        attempts=0,
        max_attempts=5,
        is_verified=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    test_db.add(otp_record)
    test_db.commit()

    response = client.post("/auth/otp/verify", json={"phone": phone, "otp": "999999"})
    assert response.status_code == 400
    assert "Invalid OTP" in response.json()["detail"]

    test_db.refresh(otp_record)
    assert otp_record.attempts == 1


def test_verify_otp_max_attempts_lockout(test_db, client):
    """Test that reaching max attempts locks out verification."""
    phone = "+919876543213"
    otp_record = OTPVerification(
        phone=phone,
        otp_hash=hash_otp("111111", salt=phone),
        attempts=5,
        max_attempts=5,
        is_verified=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    test_db.add(otp_record)
    test_db.commit()

    response = client.post("/auth/otp/verify", json={"phone": phone, "otp": "111111"})
    assert response.status_code == 429
    assert "Maximum OTP verification attempts exceeded" in response.json()["detail"]


def test_unauthorized_access_protection(client):
    """Test that accessing protected endpoint without token returns 401."""
    response = client.get("/users/me")
    assert response.status_code == 401


def test_rbac_admin_endpoint_forbidden_for_regular_user(test_db, client):
    """Test that a regular user (role='user') receives 403 Forbidden on admin endpoints."""
    regular_user = User(
        id=uuid.uuid4(),
        phone="+919876543214",
        full_name="Regular User",
        role="user",
        is_active=True
    )
    test_db.add(regular_user)
    test_db.commit()

    token = create_access_token(data={"sub": str(regular_user.id), "role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/admin/analytics/dashboard", headers=headers)
    assert response.status_code == 403
    assert "Admin" in response.json()["detail"]


def test_rbac_admin_endpoint_allowed_for_admin_user(test_db, client):
    """Test that an admin user (role='admin') can successfully access admin endpoints."""
    admin_user = User(
        id=uuid.uuid4(),
        phone="+919999999999",
        full_name="Admin Officer",
        role="admin",
        is_active=True
    )
    test_db.add(admin_user)
    test_db.commit()

    token = create_access_token(data={"sub": str(admin_user.id), "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/admin/analytics/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_schemes" in data
