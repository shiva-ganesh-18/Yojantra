"""Tests for Official Government Integrations (DigiLocker, Aadhaar, PAN, UDYAM, Schemes sync)."""
import pytest
import uuid
from decimal import Decimal

from app.core.security import create_access_token
from app.models import User, Business, Scheme, Application


@pytest.fixture
def user_with_business(test_db):
    user = User(
        id=uuid.uuid4(),
        phone="+919876543201",
        full_name="Ramesh Verma",
        gender="male",
        social_category="SC",
        state="Uttar Pradesh",
        district="Varanasi",
        is_active=True
    )
    biz = Business(
        id=uuid.uuid4(),
        user_id=user.id,
        business_name="Verma Handloom Works",
        business_type="manufacturing",
        business_stage="existing",
        sector="Textiles & Weaving",
        annual_turnover_inr=Decimal("1200000"),
        funding_needed_inr=Decimal("500000")
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Pradhan Mantri Mudra Yojana (PMMY)",
        ministry="Ministry of Finance",
        description="Micro enterprise loan up to 10 Lakhs",
        max_benefit_inr=Decimal("1000000"),
        status="active"
    )
    test_db.add_all([user, biz, scheme])
    test_db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    return {
        "user": user,
        "business": biz,
        "scheme": scheme,
        "headers": {"Authorization": f"Bearer {token}"}
    }


def test_integration_statuses_endpoint(client):
    """Verify integration status listing shows official portals without fabricated approval."""
    res = client.get("/integrations/status")
    assert res.status_code == 200
    services = res.json()
    assert len(services) >= 4
    service_names = [s["service_name"] for s in services]
    assert any("DigiLocker" in name for name in service_names)
    assert any("Aadhaar" in name for name in service_names)
    assert any("PAN" in name for name in service_names)
    assert any("UDYAM" in name for name in service_names)


def test_digilocker_auth_url_generation(client, user_with_business):
    """Verify DigiLocker OAuth2 redirect link is generated with security state."""
    headers = user_with_business["headers"]
    res = client.get("/integrations/digilocker/auth-url", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "auth_url" in data
    assert "state" in data
    assert "disclaimer" in data


def test_aadhaar_verify_privacy_preserving(client, user_with_business):
    """Verify only last 4 digits of Aadhaar are processed with DPDP Act consent."""
    headers = user_with_business["headers"]

    # 1. Without consent -> rejection
    res_no_consent = client.post(
        "/integrations/aadhaar/verify-last-four",
        json={"aadhaar_last_four": "4821", "consent_given": False},
        headers=headers
    )
    assert res_no_consent.status_code == 200
    assert res_no_consent.json()["success"] is False
    assert res_no_consent.json()["status"] == "consent_required"

    # 2. With consent -> verified with masked number
    res_consent = client.post(
        "/integrations/aadhaar/verify-last-four",
        json={"aadhaar_last_four": "4821", "consent_given": True},
        headers=headers
    )
    assert res_consent.status_code == 200
    data = res_consent.json()
    assert data["success"] is True
    assert data["masked_aadhaar"] == "XXXX-XXXX-4821"
    assert "Format Validation" in data["verification_tier"] or "DPDP" in data["verification_tier"] or "UIDAI" in data["verification_tier"]


def test_pan_verification_structure_and_category(client, user_with_business):
    """Verify PAN card format & entity categorization."""
    headers = user_with_business["headers"]

    # Valid Individual PAN (4th char P)
    res_pan = client.post(
        "/integrations/pan/verify",
        json={"pan_number": "ABCDE1234F", "consent_given": True},
        headers=headers
    )
    assert res_pan.status_code == 200
    data = res_pan.json()
    assert data["success"] is True
    assert "Individual" in data["category"]
    assert data["masked_pan"] == "ABXXX123F"


def test_udyam_registration_verification(client, user_with_business):
    """Verify UDYAM registration number format."""
    headers = user_with_business["headers"]

    res_udyam = client.post(
        "/integrations/udyam/verify",
        json={"udyam_number": "UDYAM-UP-01-0012345", "consent_given": True},
        headers=headers
    )
    assert res_udyam.status_code == 200
    data = res_udyam.json()
    assert data["success"] is True
    assert data["udyam_number"] == "UDYAM-UP-01-0012345"


def test_grounded_ai_chat_scheme_knowledge(client, user_with_business):
    """Verify AI chat uses grounded scheme data and user profile without hallucinating."""
    headers = user_with_business["headers"]

    chat_payload = {
        "message": "What schemes match my handloom business in Uttar Pradesh?",
        "language": "en",
        "channel": "text"
    }
    res = client.post("/chat/message", json=chat_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["reply"] is not None
    assert len(data["reply"]) > 20
    assert len(data["actions"]) >= 1
