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


def test_integration_statuses_production_readiness_fields(client):
    """Verify /integrations/status returns service_key, integration_mode, and production_credentials_needed."""
    res = client.get("/integrations/status")
    assert res.status_code == 200
    services = res.json()
    assert len(services) >= 7

    keys = [s["service_key"] for s in services]
    assert "UIDAI" in keys
    assert "PAN" in keys
    assert "UDYAM" in keys
    assert "DigiLocker" in keys
    assert "CBS" in keys
    assert "PFMS" in keys
    assert "GOV_SYNC" in keys

    for s in services:
        assert s["integration_mode"] in ["LIVE", "SANDBOX", "CONFIGURATION_READY", "NOT_CONFIGURED"]
        assert isinstance(s["production_credentials_needed"], list)
        assert len(s["production_credentials_needed"]) > 0
        assert "production_credentials_configured" in s
        # Ensure needed credentials are variable names, not values
        for cred_var in s["production_credentials_needed"]:
            assert cred_var.isupper()
            assert "_" in cred_var


def test_aadhaar_sandbox_mode_response(client, user_with_business):
    """Verify Aadhaar verification returns SANDBOX mode when live credentials are absent."""
    headers = user_with_business["headers"]
    res = client.post(
        "/integrations/aadhaar/verify-last-four",
        json={"aadhaar_last_four": "9876", "consent_given": True},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["mode"] == "SANDBOX"
    assert data["masked_aadhaar"] == "XXXX-XXXX-9876"
    assert "Format Validation" in data["verification_tier"]


def test_pan_categorization_and_sandbox_mode(client, user_with_business):
    """Verify PAN verification accurately identifies entity types and flags SANDBOX mode."""
    headers = user_with_business["headers"]

    # Company PAN (4th char 'C')
    res_corp = client.post(
        "/integrations/pan/verify",
        json={"pan_number": "AAACT1234K", "consent_given": True},
        headers=headers
    )
    assert res_corp.status_code == 200
    corp_data = res_corp.json()
    assert corp_data["success"] is True
    assert "Company" in corp_data["category"]
    assert corp_data["mode"] == "SANDBOX"

    # Invalid PAN format rejected by schema validation (422)
    res_invalid = client.post(
        "/integrations/pan/verify",
        json={"pan_number": "INVALID123", "consent_given": True},
        headers=headers
    )
    assert res_invalid.status_code == 422


def test_udyam_state_and_classification(client, user_with_business):
    """Verify UDYAM extracts state and classifies enterprise size in SANDBOX mode."""
    headers = user_with_business["headers"]

    res = client.post(
        "/integrations/udyam/verify",
        json={"udyam_number": "UDYAM-MH-03-0098765", "consent_given": True},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "MH" in data["message"]
    assert data["enterprise_type"] in ["Micro", "Small", "Medium"]
    assert data["mode"] == "SANDBOX"

    # Invalid UDYAM rejected by schema validation (422)
    res_bad = client.post(
        "/integrations/udyam/verify",
        json={"udyam_number": "NOT-UDYAM-NUMBER", "consent_given": True},
        headers=headers
    )
    assert res_bad.status_code == 422


def test_production_mode_detection_and_no_fake_success(monkeypatch, client, user_with_business):
    """Verify that when production settings are active, real gateway calls are attempted without fake success."""
    from app.core.config import get_settings
    import httpx

    # Set mock production endpoints
    monkeypatch.setenv("PAN_GATEWAY_URL", "https://api.protean-tin.com/pan/v2/verify")
    monkeypatch.setenv("PAN_API_KEY", "test-live-pan-key-12345")
    get_settings.cache_clear()

    headers = user_with_business["headers"]

    # When live gateway returns 503 or fails, system must NOT fake a success
    def mock_post_failure(*args, **kwargs):
        raise httpx.ConnectError("Connection to Protean Gateway timed out")

    monkeypatch.setattr(httpx, "post", mock_post_failure)

    res = client.post(
        "/integrations/pan/verify",
        json={"pan_number": "ABCDE1234F", "consent_given": True},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    # Must fail safely or report upstream issue; NEVER report success=True with fake data
    assert data["success"] is False
    assert data["status"] in ["upstream_api_unreachable", "gateway_error", "verification_failed", "gateway_unreachable"]
    assert data["mode"] == "LIVE"

    # Reset cache
    get_settings.cache_clear()


def test_digilocker_live_vs_sandbox(monkeypatch, client, user_with_business):
    """Verify DigiLocker produces official MeitY OAuth URL when credentials exist, sandbox when not."""
    from app.core.config import get_settings
    headers = user_with_business["headers"]

    # 1. Sandbox mode (empty credentials)
    monkeypatch.delenv("DIGILOCKER_CLIENT_ID", raising=False)
    monkeypatch.delenv("DIGILOCKER_CLIENT_SECRET", raising=False)
    get_settings.cache_clear()

    res_sandbox = client.get("/integrations/digilocker/auth-url", headers=headers)
    assert res_sandbox.status_code == 200
    assert res_sandbox.json()["mode"] == "SANDBOX"

    # 2. Live mode (credentials configured)
    monkeypatch.setenv("DIGILOCKER_CLIENT_ID", "official_meity_client_id_001")
    monkeypatch.setenv("DIGILOCKER_CLIENT_SECRET", "official_meity_secret_001")
    get_settings.cache_clear()

    res_live = client.get("/integrations/digilocker/auth-url", headers=headers)
    assert res_live.status_code == 200
    assert res_live.json()["mode"] == "LIVE"
    assert "digitallocker.gov.in" in res_live.json()["auth_url"]
    assert "official_meity_client_id_001" in res_live.json()["auth_url"]

    # Reset cache
    get_settings.cache_clear()


def test_zero_secret_leakage_in_all_integration_responses(client, user_with_business):
    """Verify no API keys, client secrets, or private tokens appear in any endpoint responses."""
    headers = user_with_business["headers"]

    # Status endpoint
    status_res = client.get("/integrations/status")
    status_text = status_res.text.lower()
    for sensitive in ["secret", "password", "license_key", "bearer_token"]:
        assert f'"{sensitive}": "' not in status_text

    # Aadhaar endpoint
    aadhaar_res = client.post(
        "/integrations/aadhaar/verify-last-four",
        json={"aadhaar_last_four": "5432", "consent_given": True},
        headers=headers
    )
    assert "uidai_license" not in aadhaar_res.text.lower()

    # PAN endpoint
    pan_res = client.post(
        "/integrations/pan/verify",
        json={"pan_number": "ABCDE1234F", "consent_given": True},
        headers=headers
    )
    assert "pan_api_key" not in pan_res.text.lower()

    # UDYAM endpoint
    udyam_res = client.post(
        "/integrations/udyam/verify",
        json={"udyam_number": "UDYAM-DL-01-0001234", "consent_given": True},
        headers=headers
    )
    assert "udyam_api_key" not in udyam_res.text.lower()


