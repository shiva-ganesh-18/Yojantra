"""Tests for Firebase Google Authentication and Account Linking."""
from datetime import timedelta
import pytest
from unittest.mock import patch
from app.core.firebase import FirebaseNotConfiguredError, InvalidFirebaseTokenError
from app.core.security import verify_token, create_access_token, hash_otp
from app.models import User, OTPVerification


def test_get_auth_config(client):
    """Test public auth configuration endpoint returns google_auth, phone_auth=False and dev_otp_allowed=False."""
    res = client.get("/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert "google_auth" in data
    assert data["phone_auth"] is False
    assert data["dev_otp_allowed"] is False


def test_google_login_when_unconfigured(client):
    """Test that Google login returns 503 gracefully when Firebase credentials are not configured."""
    with patch("app.routers.auth.verify_firebase_token", side_effect=FirebaseNotConfiguredError("Not configured")):
        res = client.post("/auth/google", json={"id_token": "dummy-token-12345"})
        assert res.status_code == 503
        data = res.json()
        assert "not configured" in data["detail"].lower()


def test_google_login_invalid_token(client):
    """Test that invalid/expired Firebase ID tokens return 401 Unauthorized."""
    with patch("app.routers.auth.verify_firebase_token", side_effect=InvalidFirebaseTokenError("Signature invalid")):
        res = client.post("/auth/google", json={"id_token": "invalid-token-format"})
        assert res.status_code == 401
        data = res.json()
        assert "authentication failed" in data["detail"].lower()


def test_google_login_new_user_creation(client, test_db):
    """Test that a new Google user is correctly registered as beneficiary (role='user')."""
    mock_payload = {
        "uid": "firebase_uid_new_123",
        "email": "priya.sharma@example.com",
        "email_verified": True,
        "name": "Priya Sharma",
        "picture": "https://example.com/priya.jpg",
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        res = client.post("/auth/google", json={"id_token": "mock-valid-google-id-token"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        user_info = data["user"]
        assert user_info["email"] == "priya.sharma@example.com"
        assert user_info["full_name"] == "Priya Sharma"
        assert user_info["auth_provider"] == "google"
        assert user_info["role"] == "user"  # CRITICAL: Always default to beneficiary, never admin!

        # Verify JWT payload
        jwt_payload = verify_token(data["access_token"])
        assert jwt_payload is not None
        assert jwt_payload["role"] == "user"

        # Verify in DB
        db_user = test_db.query(User).filter(User.firebase_uid == "firebase_uid_new_123").first()
        assert db_user is not None
        assert db_user.email == "priya.sharma@example.com"
        assert db_user.role == "user"


def test_google_login_existing_user(client, test_db):
    """Test that existing Google user logs in smoothly without duplicating accounts."""
    mock_payload = {
        "uid": "firebase_uid_existing_456",
        "email": "existing.entrepreneur@example.com",
        "email_verified": True,
        "name": "Sunita Devi",
        "picture": "https://example.com/sunita.jpg",
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        # 1st call: creates user
        res1 = client.post("/auth/google", json={"id_token": "mock-token-call-1"})
        assert res1.status_code == 200
        uid1 = res1.json()["user"]["id"]

        # 2nd call: logs in existing user
        res2 = client.post("/auth/google", json={"id_token": "mock-token-call-2"})
        assert res2.status_code == 200
        uid2 = res2.json()["user"]["id"]

        assert uid1 == uid2

        # Verify no duplicates
        users_count = test_db.query(User).filter(User.firebase_uid == "firebase_uid_existing_456").count()
        assert users_count == 1


def test_google_account_linking_by_verified_email(client, test_db):
    """Test safe account linking when an existing user with email logs in with matching verified Google email."""
    phone_user = User(
        phone="+919876543299",
        email="linked.artisan@example.com",
        full_name="Ramesh Kumar",
        role="user",
        auth_provider="google",
        onboarding_completed=True
    )
    test_db.add(phone_user)
    test_db.commit()
    test_db.refresh(phone_user)
    original_id = phone_user.id

    mock_payload = {
        "uid": "firebase_uid_ramesh_789",
        "email": "linked.artisan@example.com",
        "email_verified": True,
        "name": "Ramesh Kumar",
        "picture": "https://example.com/ramesh.jpg",
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        res = client.post("/auth/google", json={"id_token": "mock-token-linking"})
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["id"] == str(original_id)
        assert data["user"]["email"] == "linked.artisan@example.com"

        # Check DB
        test_db.expire_all()
        db_user = test_db.query(User).filter(User.id == original_id).first()
        assert db_user.firebase_uid == "firebase_uid_ramesh_789"


def test_link_google_account_authenticated(client, test_db):
    """Test authenticated user explicitly linking Google account from profile."""
    # Create authenticated user
    import uuid
    user = User(
        id=uuid.uuid4(),
        phone="+919123456780",
        full_name="Anita Roy",
        role="user",
        auth_provider="google",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    token = create_access_token({"sub": str(user.id), "phone": user.phone, "role": user.role})

    mock_payload = {
        "uid": "firebase_uid_linked_manually_111",
        "email": "manual.link@example.com",
        "email_verified": True,
        "name": "Anita Roy",
        "picture": "https://example.com/anita.jpg",
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        res_link = client.post(
            "/auth/link/google",
            headers={"Authorization": f"Bearer {token}"},
            json={"id_token": "mock-valid-link-token"}
        )
        assert res_link.status_code == 200
        data = res_link.json()
        assert data["avatar_url"] == "https://example.com/anita.jpg"


def test_google_login_expired_firebase_token(client):
    """Test that expired Firebase tokens are rejected with 401."""
    with patch("app.routers.auth.verify_firebase_token", side_effect=InvalidFirebaseTokenError("Firebase ID token has expired")):
        res = client.post("/auth/google", json={"id_token": "expired-token"})
        assert res.status_code == 401
        assert "authentication failed" in res.json()["detail"].lower()


def test_google_login_missing_firebase_token(client):
    """Test that missing or empty ID token returns 422 Unprocessable Entity."""
    res = client.post("/auth/google", json={})
    assert res.status_code == 422


def test_google_login_beneficiary_role_isolation(client, test_db):
    """Test that even if a Google account attempts to provide admin claims, the backend role is strictly 'user'."""
    mock_payload = {
        "uid": "firebase_uid_hacker_attempt",
        "email": "infiltrator@example.com",
        "email_verified": True,
        "name": "Super Admin Attempter",
        "role": "admin",  # Client-side forged claim
        "is_admin": True,
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        res = client.post("/auth/google", json={"id_token": "mock-token-admin-attempt"})
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["role"] == "user"  # Strict beneficiary default!
        
        # Verify in DB
        db_user = test_db.query(User).filter(User.email == "infiltrator@example.com").first()
        assert db_user.role == "user"


def test_google_account_linking_conflict_different_owner(client, test_db):
    """Test that attempting to link a Google account already owned by someone else returns 409 Conflict."""
    import uuid
    # User 1 has already linked this Google UID
    user1 = User(
        id=uuid.uuid4(),
        phone="+919876543201",
        email="owner1@example.com",
        firebase_uid="shared_firebase_uid_conflict",
        role="user",
        auth_provider="google",
        is_active=True
    )
    test_db.add(user1)

    # User 2
    user2 = User(
        id=uuid.uuid4(),
        phone="+919876543202",
        email="owner2@example.com",
        role="user",
        auth_provider="google",
        is_active=True
    )
    test_db.add(user2)
    test_db.commit()

    user2_token = create_access_token({"sub": str(user2.id), "phone": user2.phone, "role": user2.role})

    mock_payload = {
        "uid": "shared_firebase_uid_conflict",
        "email": "owner1@example.com",
        "email_verified": True,
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        res = client.post(
            "/auth/link/google",
            headers={"Authorization": f"Bearer {user2_token}"},
            json={"id_token": "mock-token-conflict"}
        )
        assert res.status_code == 409
        assert "already linked" in res.json()["detail"].lower()


def test_auth_logout(client, test_db):
    """Test user logout from backend session."""
    import uuid
    user = User(
        id=uuid.uuid4(),
        phone="+919876543203",
        role="user",
        auth_provider="google",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    token = create_access_token({"sub": str(user.id), "phone": user.phone, "role": user.role})

    res = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert "logged out" in res.json()["message"].lower()


def test_expired_application_jwt_rejected(client):
    """Test that an expired application JWT is rejected by protected endpoints."""
    # Create an expired token (expired 1 hour ago)
    expired_token = create_access_token(
        data={"sub": "some-user-uuid", "phone": "+919876543204", "role": "user"},
        expires_delta=timedelta(minutes=-60)
    )
    res = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert res.status_code == 401


def test_firebase_token_clock_skew_tolerance(monkeypatch, client, test_db):
    """Regression test: verify verify_firebase_token passes clock_skew_seconds=10 to auth.verify_id_token."""
    from app.core import firebase
    import firebase_admin.auth

    recorded_kwargs = {}

    def mock_verify_id_token(id_token, **kwargs):
        recorded_kwargs.update(kwargs)
        return {
            "uid": "skew_user_uid_123",
            "email": "skew.tolerance@example.com",
            "email_verified": True,
            "name": "Skew User",
            "picture": "",
            "auth_time": 1788967290
        }

    monkeypatch.setattr(firebase, "is_firebase_configured", lambda: True)
    monkeypatch.setattr(firebase_admin.auth, "verify_id_token", mock_verify_id_token)

    res = client.post("/auth/google", json={"id_token": "mock-token-skew-3s-ahead"})
    assert res.status_code == 200
    assert recorded_kwargs.get("clock_skew_seconds") == 10
    data = res.json()
    assert data["user"]["email"] == "skew.tolerance@example.com"

