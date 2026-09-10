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


def test_sms_gateway_api_key_authentication(monkeypatch):
    """Verify SMS Gateway prioritizes Twilio API Key authentication over legacy Auth Token and supports Messaging Service SID."""
    from app.services.sms_service import SMSGatewayService
    from app.core import config

    # Test Case 1: Only API Key configured with TWILIO_PHONE (No Auth Token required)
    svc = SMSGatewayService()
    svc.twilio_account_sid = "AC_mock_account_123"
    svc.twilio_api_key_sid = "SK_mock_key_sid_456"
    svc.twilio_api_key_secret = "mock_secret_789"
    svc.twilio_auth_token = ""
    svc.twilio_phone = "+15551234567"
    svc.twilio_messaging_service_sid = ""

    assert svc.is_production_gateway_configured() is True
    auth = svc.get_auth_credentials()
    assert auth == ("SK_mock_key_sid_456", "mock_secret_789")
    sender = svc.get_sender_parameter()
    assert sender == {"From": "+15551234567"}

    # Test Case 2: Messaging Service SID priority
    svc_mg = SMSGatewayService()
    svc_mg.twilio_account_sid = "AC_mock_account_123"
    svc_mg.twilio_api_key_sid = "SK_mock_key_sid_456"
    svc_mg.twilio_api_key_secret = "mock_secret_789"
    svc_mg.twilio_phone = "+15551234567"
    svc_mg.twilio_messaging_service_sid = "MG_mock_messaging_service_123"

    assert svc_mg.is_production_gateway_configured() is True
    sender_mg = svc_mg.get_sender_parameter()
    assert sender_mg == {"MessagingServiceSid": "MG_mock_messaging_service_123"}

    # Test Case 3: Sandbox fallback in non-production
    svc_empty = SMSGatewayService()
    svc_empty.twilio_account_sid = ""
    svc_empty.twilio_api_key_sid = ""
    svc_empty.twilio_api_key_secret = ""
    svc_empty.twilio_auth_token = ""
    svc_empty.twilio_phone = ""
    svc_empty.twilio_messaging_service_sid = ""

    assert svc_empty.is_production_gateway_configured() is False
    res = svc_empty.send_otp_sms("+919876543210", "123456")
    assert res["status"] == "dispatched_sandbox"
    assert "123456" not in str(res) # Zero OTP leakage in response

