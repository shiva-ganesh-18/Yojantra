"""Tests for Admin Router, Analytics, and Scheme Match-All endpoints."""
import uuid
import pytest
from app.models import User, Scheme, UserSchemeMatch, Business
from app.core.security import create_access_token


@pytest.fixture
def admin_user(test_db):
    user = User(
        id=uuid.uuid4(),
        phone="+919999999999",
        full_name="Admin User",
        role="admin",
        state="Delhi",
        district="Central Delhi",
        is_active=True,
        onboarding_completed=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def normal_user(test_db):
    user = User(
        id=uuid.uuid4(),
        phone="+919876543210",
        full_name="Regular Entrepreneur",
        role="user",
        state="Maharashtra",
        district="Pune",
        is_active=True,
        onboarding_completed=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user):
    token = create_access_token({"sub": str(admin_user.id), "phone": admin_user.phone, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(normal_user):
    token = create_access_token({"sub": str(normal_user.id), "phone": normal_user.phone, "role": "user"})
    return {"Authorization": f"Bearer {token}"}


def test_admin_endpoints_require_admin_role(client, user_headers):
    # Missing token -> 401
    resp = client.get("/admin/analytics/dashboard")
    assert resp.status_code == 401

    # Normal user token -> 403 Forbidden
    resp = client.get("/admin/analytics/dashboard", headers=user_headers)
    assert resp.status_code == 403


def test_admin_dashboard_metrics(client, admin_headers, test_db, normal_user):
    resp = client.get("/admin/analytics/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_schemes" in data
    assert "total_matches" in data
    assert data["total_users"] >= 2  # admin + normal_user


def test_admin_list_and_create_schemes(client, admin_headers):
    # 1. Create scheme
    new_scheme = {
        "name": "Admin Test Innovation Scheme",
        "ministry": "Ministry of Electronics and IT",
        "description": "Grant for tech startups in tier 2/3 cities",
        "scheme_type": "grant",
        "status": "active"
    }
    create_resp = client.post("/admin/schemes", json=new_scheme, headers=admin_headers)
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["name"] == "Admin Test Innovation Scheme"

    # 2. List schemes
    list_resp = client.get("/admin/schemes", headers=admin_headers)
    assert list_resp.status_code == 200
    schemes = list_resp.json()
    assert len(schemes) >= 1
    assert any(s["name"] == "Admin Test Innovation Scheme" for s in schemes)


def test_admin_list_users(client, admin_headers, normal_user):
    resp = client.get("/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 2


def test_admin_bias_report(client, admin_headers):
    resp = client.get("/admin/analytics/bias", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "match_scores_by_category" in data


def test_admin_match_all_schemes(client, admin_headers, test_db, normal_user):
    # Add scheme to match against
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Universal Mudra Scheme",
        ministry="Ministry of Finance",
        description="Mudra loan for small businesses",
        scheme_type="loan",
        status="active"
    )
    test_db.add(scheme)
    test_db.commit()

    resp = client.post("/admin/schemes/match-all", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "users_processed" in data
    assert "total_matches_generated" in data
