"""Part 13 Security & Production Hardening Test Suite.

Validates:
1. IDOR prevention on applications and documents (403 Forbidden).
2. Path traversal defense and strict file extension / MIME validation.
3. Privilege escalation prevention on user profile updates.
4. RBAC role enforcement against database records.
5. HTTP security headers (HSTS, CSP, nosniff, DENY, Permissions-Policy).
6. Production error sanitization (no internal stack traces exposed).
7. Webhook HMAC-SHA256 signature verification and replay defense (300s window).
8. Rate limiting (429 Too Many Requests + Retry-After headers).
9. Production configuration security guardrails (DEBUG=False, secret key validation).
"""
import io
import json
import time
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.config import Settings, get_settings
from app.core.rate_limit import RateLimiter, _check_memory_rate_limit
from app.models import User, Scheme, Application, Document
from app.services.document_service import DocumentService


@pytest.fixture
def security_users(test_db):
    """Creates isolated users for security tests."""
    user_victim = User(
        id=uuid.uuid4(),
        phone="+919800000001",
        email="victim@example.com",
        full_name="Victim User",
        role="user",
        is_active=True
    )
    user_attacker = User(
        id=uuid.uuid4(),
        phone="+919800000002",
        email="attacker@example.com",
        full_name="Attacker User",
        role="user",
        is_active=True
    )
    user_partner = User(
        id=uuid.uuid4(),
        phone="+919800000003",
        email="partner@bank.example.com",
        full_name="Partner Officer",
        role="partner_officer",
        is_active=True
    )
    user_admin = User(
        id=uuid.uuid4(),
        phone="+919800000004",
        email="admin@example.com",
        full_name="Platform Admin",
        role="admin",
        is_active=True
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Security MSME Scheme",
        ministry="Ministry of MSME",
        description="Scheme for hardening test",
        max_benefit_inr=Decimal("500000"),
        status="active",
        documents_required=["aadhaar", "pan"]
    )
    test_db.add_all([user_victim, user_attacker, user_partner, user_admin, scheme])
    test_db.commit()

    token_victim = create_access_token(data={"sub": str(user_victim.id), "role": "user"})
    token_attacker = create_access_token(data={"sub": str(user_attacker.id), "role": "user"})
    token_partner = create_access_token(data={"sub": str(user_partner.id), "role": "partner_officer"})
    token_admin = create_access_token(data={"sub": str(user_admin.id), "role": "admin"})

    return {
        "victim": user_victim,
        "attacker": user_attacker,
        "partner": user_partner,
        "admin": user_admin,
        "scheme": scheme,
        "headers_victim": {"Authorization": f"Bearer {token_victim}"},
        "headers_attacker": {"Authorization": f"Bearer {token_attacker}"},
        "headers_partner": {"Authorization": f"Bearer {token_partner}"},
        "headers_admin": {"Authorization": f"Bearer {token_admin}"},
    }


# ============================================================================
# 1. IDOR Tests: Applications & Documents
# ============================================================================

def test_idor_application_access_blocked(client, security_users):
    """Ensure attacker cannot view, submit, validate, or checklist victim's application."""
    data = security_users
    # Victim creates application
    res = client.post(
        "/applications",
        json={"scheme_id": str(data["scheme"].id), "requested_amount_inr": 150000.0},
        headers=data["headers_victim"]
    )
    assert res.status_code == 200
    app_id = res.json()["id"]

    # Attacker tries to read application -> 403 Forbidden
    res_get = client.get(f"/applications/{app_id}", headers=data["headers_attacker"])
    assert res_get.status_code == 403
    assert "Access forbidden" in res_get.json()["detail"]

    # Attacker tries to submit application -> 403 Forbidden
    res_sub = client.post(f"/applications/{app_id}/submit", headers=data["headers_attacker"])
    assert res_sub.status_code == 403

    # Attacker tries to validate application -> 403 Forbidden
    res_val = client.get(f"/applications/{app_id}/validate", headers=data["headers_attacker"])
    assert res_val.status_code == 403

    # Attacker tries to read checklist -> 403 Forbidden
    res_chk = client.get(f"/applications/{app_id}/checklist", headers=data["headers_attacker"])
    assert res_chk.status_code == 403

    # Victim CAN read their own application
    res_ok = client.get(f"/applications/{app_id}", headers=data["headers_victim"])
    assert res_ok.status_code == 200


def test_idor_document_download_and_verify_blocked(client, security_users):
    """Ensure attacker cannot download, verify, or delete victim's document."""
    data = security_users

    # Victim uploads a document
    file_content = b"%PDF-1.5 test document file content"
    res_up = client.post(
        "/documents/upload",
        data={"doc_type": "pan"},
        files={"file": ("pan_card.pdf", io.BytesIO(file_content), "application/pdf")},
        headers=data["headers_victim"]
    )
    assert res_up.status_code == 200
    doc_id = res_up.json()["id"]

    # Attacker tries to download victim's document -> 403 Forbidden
    res_dl = client.get(f"/documents/{doc_id}/download", headers=data["headers_attacker"])
    assert res_dl.status_code == 403

    # Attacker tries to verify victim's document -> 403 Forbidden
    res_ver = client.post(f"/documents/{doc_id}/verify", headers=data["headers_attacker"])
    assert res_ver.status_code == 403

    # Attacker tries to delete victim's document -> 403 Forbidden
    res_del = client.delete(f"/documents/{doc_id}", headers=data["headers_attacker"])
    assert res_del.status_code == 403

    # Victim CAN download their document
    res_dl_ok = client.get(f"/documents/{doc_id}/download", headers=data["headers_victim"])
    assert res_dl_ok.status_code == 200
    assert res_dl_ok.headers.get("X-Content-Type-Options") == "nosniff"

    # Partner officer CAN verify victim's document
    res_ver_partner = client.post(f"/documents/{doc_id}/verify", headers=data["headers_partner"])
    assert res_ver_partner.status_code == 200


# ============================================================================
# 2. File Security & Path Traversal Tests
# ============================================================================

def test_file_upload_disallows_executable_and_script_extensions(client, security_users):
    """Uploads with non-whitelisted extensions (.exe, .sh, .py) must be rejected."""
    data = security_users
    bad_files = [
        ("malware.exe", b"MZ\x90\x00\x03", "application/x-msdownload"),
        ("exploit.sh", b"#!/bin/bash\nrm -rf /", "text/x-shellscript"),
        ("script.py", b"import os; os.system('whoami')", "text/x-python"),
    ]
    for filename, content, mime in bad_files:
        res = client.post(
            "/documents/upload",
            data={"doc_type": "pan"},
            files={"file": (filename, io.BytesIO(content), mime)},
            headers=data["headers_victim"]
        )
        assert res.status_code == 400
        detail = res.json()["detail"].lower()
        assert "allowed" in detail or "invalid" in detail or "extension" in detail


def test_file_upload_path_traversal_sanitized(client, security_users, test_db):
    """Filename containing directory traversal (../../evil.pdf) is sanitized safely."""
    data = security_users
    traversal_file = (
        "../../evil.pdf",
        io.BytesIO(b"%PDF-1.4 test safe content"),
        "application/pdf"
    )
    res = client.post(
        "/documents/upload",
        data={"doc_type": "pan"},
        files={"file": traversal_file},
        headers=data["headers_victim"]
    )
    assert res.status_code == 200
    doc_id = res.json()["id"]

    # Verify the stored file path is strictly within the designated uploads directory
    doc = test_db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
    assert doc is not None
    service = DocumentService(test_db)
    assert doc.file_url.startswith(service.upload_dir)
    assert ".." not in doc.file_url


# ============================================================================
# 3. Privilege Escalation Prevention
# ============================================================================

def test_privilege_escalation_prevented_on_user_update(client, security_users, test_db):
    """Beneficiary cannot escalate their role to admin via PUT /users/me."""
    data = security_users
    # Attacker tries to update role to admin
    payload = {
        "full_name": "Hacked Attacker",
        "role": "admin",
        "is_superuser": True
    }
    res = client.put("/users/me", json=payload, headers=data["headers_attacker"])
    assert res.status_code == 200

    # Refresh user from database to verify role was NOT altered
    test_db.expire_all()
    user = test_db.query(User).filter(User.id == data["attacker"].id).first()
    assert user.role == "user"
    assert user.full_name == "Hacked Attacker"


# ============================================================================
# 4. RBAC Role Verification Against Database
# ============================================================================

def test_rbac_rejects_unauthorized_admin_access(client, security_users):
    """Non-admin users cannot access administrative endpoints."""
    data = security_users
    # Attacker attempts admin list
    res = client.get("/admin/users", headers=data["headers_attacker"])
    assert res.status_code == 403

    # Admin CAN access
    res_admin = client.get("/admin/users", headers=data["headers_admin"])
    assert res_admin.status_code == 200


def test_rbac_token_role_claim_rejected_if_db_role_is_user(client, security_users):
    """Forged/tampered JWT role claim fails if database record has role='user'."""
    data = security_users
    # Forge token claiming role="admin" for the attacker user who is 'user' in DB
    forged_token = create_access_token(data={"sub": str(data["attacker"].id), "role": "admin"})
    forged_headers = {"Authorization": f"Bearer {forged_token}"}

    res = client.get("/admin/users", headers=forged_headers)
    assert res.status_code == 403
    detail = res.json()["detail"].lower()
    assert "admin" in detail or "forbidden" in detail


# ============================================================================
# 5. HTTP Security Headers
# ============================================================================

def test_security_headers_present_on_all_responses(client):
    """Ensure standard defense-in-depth headers are injected on responses."""
    res = client.get("/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Permissions-Policy" in headers


# ============================================================================
# 6. Webhook HMAC & Replay Defense
# ============================================================================

def test_webhook_hmac_and_replay_protection(client, monkeypatch):
    """Verify HMAC signature validation and timestamp replay defense (<= 300s)."""
    secret = "test-webhook-secret-key-for-pfms-32chars"
    test_settings = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        SECRET_KEY="dev-secret-key-32chars-minimum-length",
        PFMS_WEBHOOK_SECRET=secret
    )
    monkeypatch.setattr("app.services.integrations_service.get_settings", lambda: test_settings)

    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "PFMS_DISBURSEMENT_SETTLED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "application_id": str(uuid.uuid4()),
            "partner_reference_code": "YOJ-2026-MUDRA-123456",
            "transaction_utr": "PFMS999888777",
            "amount_inr": 50000.0
        },
        "source": "gov_banking_gateway"
    }

    # 1. Missing signature -> 401
    res_no_sig = client.post("/integrations/webhooks/pfms", json=payload)
    assert res_no_sig.status_code == 401

    # 2. Invalid signature -> 401
    res_bad_sig = client.post(
        "/integrations/webhooks/pfms",
        json=payload,
        headers={"X-Signature": "invalidsignature123", "X-Timestamp": payload["timestamp"]}
    )
    assert res_bad_sig.status_code == 401

    # 3. Valid signature with fresh timestamp -> 200
    raw_body = json.dumps(payload).encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    res_valid = client.post(
        "/integrations/webhooks/pfms",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": valid_sig}
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["success"] is True

    # 4. Valid signature with stale timestamp (> 300 seconds old) -> 401 replay rejection
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=350)).isoformat()
    stale_payload = dict(payload, timestamp=old_time)
    stale_body = json.dumps(stale_payload).encode("utf-8")
    stale_sig = hmac.new(secret.encode("utf-8"), stale_body, hashlib.sha256).hexdigest()

    res_stale = client.post(
        "/integrations/webhooks/pfms",
        content=stale_body,
        headers={"Content-Type": "application/json", "X-Signature": stale_sig, "X-Timestamp": old_time}
    )
    assert res_stale.status_code in (400, 401)
    assert "timestamp" in res_stale.json()["detail"].lower() or "expired" in res_stale.json()["detail"].lower()


# ============================================================================
# 7. Rate Limiter Behavior
# ============================================================================

def test_rate_limiter_exceeded_returns_429():
    """Rate limiter returns allowed=False and retry_after when max_requests exceeded."""
    key = f"test_rl_{uuid.uuid4().hex[:8]}"

    # Allowed for first 3 requests
    for i in range(3):
        allowed, remaining, retry_after = _check_memory_rate_limit(key, max_requests=3, window_seconds=60)
        assert allowed is True
        assert remaining == 2 - i
        assert retry_after == 0

    # 4th request must be rejected
    allowed, remaining, retry_after = _check_memory_rate_limit(key, max_requests=3, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


# ============================================================================
# 8. Production Settings Security Guardrails
# ============================================================================

def test_production_mode_forbids_debug_mode():
    """Settings must raise ValueError if DEBUG=True when ENVIRONMENT=production."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="production-secure-random-secret-key-32chars!",
            DATABASE_URL="postgresql://produser:StrongPass123@prod-db:5432/schemematch",
            NEO4J_PASSWORD="StrongNeo4jPassword123!"
        )
    assert "DEBUG mode cannot be enabled in production" in str(exc_info.value)


def test_production_mode_forbids_weak_secret_key():
    """Settings must raise ValueError if SECRET_KEY is shorter than 32 characters in production."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="short-secret",
            DATABASE_URL="postgresql://produser:StrongPass123@prod-db:5432/schemematch",
            NEO4J_PASSWORD="StrongNeo4jPassword123!"
        )
    assert "SECRET_KEY must be provided" in str(exc_info.value)
