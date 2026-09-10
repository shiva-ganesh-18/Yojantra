"""Part 15 Regression Tests: UI & API Error Fixes, Channel Partner Filters, Application Idempotency, and CSC Disclosures."""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.core.database import get_db, SessionLocal
from app.models import User, Scheme, Application, Institution, CSCCenter
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_user(db_session):
    unique_suffix = uuid4().hex[:8]
    test_email = f"citizen_p15_{unique_suffix}@example.com"
    test_phone = f"+9198{uuid4().int % 100000000:08d}"
    user = User(
        id=uuid4(),
        email=test_email,
        full_name="Priya Sharma",
        phone=test_phone,
        state="Tamil Nadu",
        district="Chennai",
        role="citizen",
        onboarding_completed=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def sample_scheme(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.status == "active").first()
    assert scheme is not None, "At least one active scheme must exist in catalog"
    return scheme


# --- 1. Channel Partner Locator Fixes ---

def test_institutions_list_filters_including_city(client, auth_user):
    """Verify GET /institutions handles state, district, city, and institution_type filters without 500 error."""
    # Query with state and district
    res = client.get(
        "/institutions",
        params={"state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "institution_type": "PSB"}
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    for inst in data:
        assert "id" in inst
        assert "name" in inst
        assert "state" in inst
        assert "district" in inst
        assert "navigation_url" in inst


def test_partner_recommendations_with_city_and_scheme(client, auth_user, sample_scheme):
    """Verify GET /institutions/recommendations executes successfully with scheme_id, state, district, and city."""
    res = client.get(
        "/institutions/recommendations",
        params={
            "scheme_id": str(sample_scheme.id),
            "state": "Tamil Nadu",
            "district": "Chennai",
            "city": "Chennai",
            "institution_type": "PSB"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "selected_scheme_id" in data
    assert "total_partners_found" in data
    assert "partners" in data
    assert "banking_integration_status" in data
    assert data["total_partners_found"] >= 0

    if data["partners"]:
        best = data["partners"][0]
        assert "recommendation_rank" in best
        assert "geographic_tier" in best
        assert best["recommendation_rank"] == 1
        assert best["is_best_partner"] is True


def test_partner_recommendations_graceful_fallback(client, auth_user, sample_scheme):
    """Verify that searching for a city with no partners falls back gracefully without 500."""
    res = client.get(
        "/institutions/recommendations",
        params={
            "scheme_id": str(sample_scheme.id),
            "state": "Tamil Nadu",
            "district": "Chennai",
            "city": "NonExistentCityX123"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "partners" in data


# --- 2. Application Creation & Idempotency (Prevent Duplicates on Retry) ---

def test_application_creation_and_idempotency_retry(client, auth_user, sample_scheme, db_session):
    """Verify Apply Now creates application correctly and retrying does not create duplicate applications."""
    headers = auth_user["headers"]
    user = auth_user["user"]

    # First submission
    res1 = client.post(
        "/applications",
        json={"scheme_id": str(sample_scheme.id), "channel": "online"},
        headers=headers
    )
    assert res1.status_code == 200
    app1_data = res1.json()
    app1_id = app1_data["id"]
    assert app1_data["scheme_id"] == str(sample_scheme.id)
    assert app1_data["status"] == "draft"

    # Second submission (user retries or clicks Apply Now again)
    res2 = client.post(
        "/applications",
        json={"scheme_id": str(sample_scheme.id), "channel": "online"},
        headers=headers
    )
    assert res2.status_code == 200
    app2_data = res2.json()
    app2_id = app2_data["id"]

    # Must return the SAME application, not create a duplicate
    assert app2_id == app1_id

    # Verify directly in DB that only 1 application exists for this user and scheme
    app_count = db_session.query(Application).filter(
        Application.user_id == user.id,
        Application.scheme_id == sample_scheme.id
    ).count()
    assert app_count == 1


# --- 3. CSC Locator Fixes & Hyderabad Data Unavailable Disclosure ---

def test_csc_locator_hyderabad_clean_disclosure(client):
    """Verify searching for Hyderabad returns 200 with count 0 and official portal link without fabricating data."""
    res = client.get("/csc/by-district", params={"district": "Hyderabad", "state": "Telangana"})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 0
    assert data["centers"] == []
    assert data["verified_coverage_available"] is False
    assert "official_portal_url" in data
    assert "findmycsc.nic.in" in data["official_portal_url"]
    assert "1800-3000-3468" in data["official_helpline"]


def test_csc_locator_optional_params(client):
    """Verify GET /csc/by-district without parameters returns 200 without 422 error."""
    res = client.get("/csc/by-district")
    assert res.status_code == 200
    data = res.json()
    assert "centers" in data
    assert "count" in data


def test_csc_locator_indexed_district_returns_coordinates(client, db_session):
    """Verify indexed CSC centers return full attributes including latitude, longitude, and district."""
    res = client.get("/csc/by-district", params={"district": "Chennai"})
    assert res.status_code == 200
    data = res.json()
    if data["count"] > 0:
        center = data["centers"][0]
        assert "latitude" in center
        assert "longitude" in center
        assert "address" in center
        assert "district" in center
        assert "csc_id" in center


# --- 4. Verified Catalog Count Integrity ---

def test_catalog_scheme_count_integrity(client, db_session):
    """Verify exactly 63 verified active schemes exist in the catalog."""
    total_active_schemes = db_session.query(Scheme).filter(Scheme.status == "active").count()
    assert total_active_schemes == 63, f"Expected 63 verified schemes in catalog, found {total_active_schemes}"
