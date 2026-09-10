"""Part 14: Final Production Readiness & End-to-End Audit Test Suite.

Verifies:
1. Complete Citizen-to-DBT Lifecycle:
   Login -> Profile -> Business -> Scheme Matching -> Loan Simulation ->
   Document Upload -> Readiness -> Application Creation -> Pre-submission Validation ->
   Submit & Partner Routing -> Partner Review -> Document Request -> Citizen Resolution ->
   Partner Approval -> PFMS DBT Settlement Webhook -> Disbursed Tracking.
2. Partner & Admin RBAC Isolation.
3. Zero Fake Data / Zero Fabrication Guarantee for unconfigured Banking & PFMS gateways.
4. All 63 Scheme Catalog Records & Verified Official URLs.
5. Multilingual Localization (12 Scheduled Languages) & Accessibility.
6. Standalone EMI & Amortization Calculator Route (/schemes/calculate-emi).
"""
import io
import json
import time
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import User, Business, Scheme, EligibilityRule, Institution, Application, Document, Notification
from app.core.security import create_access_token
from app.core.config import get_settings, Settings
from scripts.schemes_data import ALL_SCHEMES


@pytest.fixture
def e2e_fixture(test_db):
    """Sets up an end-to-end environment with citizen, partner officer, admin, and test scheme."""
    citizen = User(
        id=uuid.uuid4(),
        phone="+919876543210",
        email="ananya.patel@example.com",
        full_name="Ananya Patel",
        role="user",
        state="Gujarat",
        district="Ahmedabad",
        is_active=True
    )
    partner_officer = User(
        id=uuid.uuid4(),
        phone="+919876543211",
        email="officer.sharma@bank.example.com",
        full_name="Nodal Officer Sharma",
        role="partner_officer",
        state="Gujarat",
        district="Ahmedabad",
        is_active=True
    )
    admin = User(
        id=uuid.uuid4(),
        phone="+919876543212",
        email="admin@yojantra.gov.in",
        full_name="Chief Admin",
        role="admin",
        is_active=True
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Scheme for Women and SC/ST",
        ministry="Ministry of Finance",
        description="Bank term loans from 10 lakh to 1 crore for greenfield enterprises",
        scheme_type="loan",
        max_benefit_inr=Decimal("10000000"),
        min_benefit_inr=Decimal("1000000"),
        max_loan_amount_inr=Decimal("10000000"),
        interest_rate=Decimal("8.50"),
        official_url="https://www.standupmitra.in",
        status="active",
        documents_required=["aadhaar", "pan", "project_report"]
    )
    partner = Institution(
        id=uuid.uuid4(),
        name="State Bank of India - Ahmedabad Lead Branch",
        institution_type="PSB",
        state="Gujarat",
        district="Ahmedabad",
        city="Ahmedabad",
        address="Ashram Road, Ahmedabad",
        latitude=23.0225,
        longitude=72.5714,
        status="active"
    )
    test_db.add_all([citizen, partner_officer, admin, scheme, partner])
    test_db.commit()

    token_citizen = create_access_token(data={"sub": str(citizen.id), "role": "user"})
    token_partner = create_access_token(data={"sub": str(partner_officer.id), "role": "partner_officer"})
    token_admin = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    return {
        "citizen": citizen,
        "partner_officer": partner_officer,
        "admin": admin,
        "scheme": scheme,
        "partner": partner,
        "headers_citizen": {"Authorization": f"Bearer {token_citizen}"},
        "headers_partner": {"Authorization": f"Bearer {token_partner}"},
        "headers_admin": {"Authorization": f"Bearer {token_admin}"}
    }


def test_complete_citizen_to_dbt_lifecycle_e2e(client, e2e_fixture, test_db):
    """Full E2E verification of complete citizen journey from login to DBT disbursement."""
    data = e2e_fixture
    scheme = data["scheme"]

    # 1. Citizen updates Profile & Onboarding
    profile_res = client.put(
        "/users/me",
        json={
            "full_name": "Ananya Patel",
            "gender": "female",
            "social_category": "General",
            "state": "Gujarat",
            "district": "Ahmedabad",
            "preferred_language": "gu",
            "onboarding_completed": True
        },
        headers=data["headers_citizen"]
    )
    assert profile_res.status_code == 200
    assert profile_res.json()["preferred_language"] == "gu"
    assert profile_res.json()["onboarding_completed"] is True

    # 2. Citizen registers Business Profile
    biz_res = client.post(
        "/users/me/business",
        json={
            "business_name": "Patel Green Bio-Tech Solutions",
            "entity_type": "private_limited",
            "sector": "Green Technology",
            "enterprise_type": "micro",
            "annual_turnover_inr": 1500000.0,
            "investment_plant_machinery_inr": 2500000.0,
            "women_ownership_percentage": 100.0,
            "number_of_employees": 6
        },
        headers=data["headers_citizen"]
    )
    assert biz_res.status_code == 200
    assert biz_res.json()["business_name"] == "Patel Green Bio-Tech Solutions"

    # 3. Scheme Matching Execution
    match_res = client.post("/schemes/match", json={"refresh": True}, headers=data["headers_citizen"])
    assert match_res.status_code == 200
    matches = match_res.json()
    assert len(matches) >= 1
    top_match = next((m for m in matches if m["scheme_id"] == str(scheme.id)), matches[0])
    assert "match_score" in top_match
    assert "why_you_match" in top_match

    # 4. Loan Simulation (Grounded in Scheme Rates & Moratorium)
    sim_res = client.post(
        f"/schemes/{scheme.id}/simulate-loan",
        json={
            "principal_amount": 2500000.0,
            "tenure_months": 84,
            "moratorium_months": 12,
            "include_schedule": True
        },
        headers=data["headers_citizen"]
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert float(sim_data["monthly_emi"]) > 0
    assert sim_data["moratorium_months"] == 12
    assert len(sim_data["monthly_schedule"]) == 84

    # 5. Standalone EMI Calculator
    calc_res = client.post(
        "/schemes/calculate-emi",
        json={
            "principal_amount": 500000.0,
            "tenure_months": 36,
            "interest_rate_percent": 9.0,
            "include_schedule": False
        },
        headers=data["headers_citizen"]
    )
    assert calc_res.status_code == 200
    assert float(calc_res.json()["monthly_emi"]) > 0

    # 6. Document Upload & Aadhaar Masking
    aadhaar_file = ("aadhaar.png", io.BytesIO(b"\x89PNG\r\nAadhaar Card 9988 7766 5544 Sample"), "image/png")
    upload_res = client.post(
        "/documents/upload",
        data={"doc_type": "aadhaar"},
        files={"file": aadhaar_file},
        headers=data["headers_citizen"]
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]
    assert upload_res.json()["extracted_fields"]["doc_number_masked"].startswith("XXXX-XXXX-")

    # Upload remaining required documents for Stand-Up India (pan, project_report)
    pan_file = ("pan.png", io.BytesIO(b"\x89PNG\r\nPAN ABCDE1234F"), "image/png")
    client.post(
        "/documents/upload",
        data={"doc_type": "pan"},
        files={"file": pan_file},
        headers=data["headers_citizen"]
    )
    dpr_file = ("dpr.pdf", io.BytesIO(b"%PDF-1.4 Detailed Project Report"), "application/pdf")
    client.post(
        "/documents/upload",
        data={"doc_type": "project_report"},
        files={"file": dpr_file},
        headers=data["headers_citizen"]
    )

    # 7. Document Readiness Check
    readiness_res = client.get("/documents/readiness", headers=data["headers_citizen"])
    assert readiness_res.status_code == 200
    assert "readiness_score" in readiness_res.json()

    # 8. Create Application
    create_app_res = client.post(
        "/applications",
        json={
            "scheme_id": str(scheme.id),
            "requested_amount_inr": 2500000.0,
            "application_data": {
                "purpose": "Plant setup and clean machinery",
                "attached_documents": [doc_id]
            }
        },
        headers=data["headers_citizen"]
    )
    assert create_app_res.status_code == 200
    app_id = create_app_res.json()["id"]
    assert create_app_res.json()["status"] == "draft"

    # 9. Pre-Submission Validation & Checklist
    val_res = client.get(f"/applications/{app_id}/validate", headers=data["headers_citizen"])
    assert val_res.status_code == 200
    assert "is_ready_to_submit" in val_res.json()

    chk_res = client.get(f"/applications/{app_id}/checklist", headers=data["headers_citizen"])
    assert chk_res.status_code == 200
    assert chk_res.json()["total_items"] >= 1

    # 10. Submit Application (Triggers Automatic Partner Routing)
    submit_res = client.post(f"/applications/{app_id}/submit", headers=data["headers_citizen"])
    assert submit_res.status_code == 200
    app_submitted = submit_res.json()
    assert app_submitted["status"] == "submitted"
    assert app_submitted["partner_reference_code"] is not None
    assert app_submitted["routing_status"] in ["ROUTED_TO_PARTNER", "PARTNER_ASSIGNED"]

    # 11. Partner Officer Views Assigned Applications
    partner_apps_res = client.get("/admin/partner/applications", headers=data["headers_partner"])
    assert partner_apps_res.status_code == 200
    p_apps = partner_apps_res.json()["items"]
    assert any(a["id"] == str(app_id) for a in p_apps)

    # 12. Partner Officer Acknowledges Receipt
    ack_res = client.post(
        f"/admin/partner/applications/{app_id}/action",
        json={"action": "PARTNER_RECEIVED", "reason": "Dossier received by Ahmedabad Lead Branch."},
        headers=data["headers_partner"]
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["current_routing_status"] == "PARTNER_RECEIVED"

    # 13. Partner Officer Requests Additional Document
    req_doc_res = client.post(
        f"/admin/partner/applications/{app_id}/action",
        json={
            "action": "DOCUMENTS_REQUIRED",
            "reason": "Please upload signed copy of detailed project report."
        },
        headers=data["headers_partner"]
    )
    assert req_doc_res.status_code == 200
    assert req_doc_res.json()["current_routing_status"] == "DOCUMENTS_REQUIRED"

    # 14. Citizen Checks Tracking & Resolves Document Request
    track_res = client.get(f"/applications/{app_id}/tracking", headers=data["headers_citizen"])
    assert track_res.status_code == 200
    assert track_res.json()["routing_status"] == "DOCUMENTS_REQUIRED"

    resolve_res = client.post(
        f"/applications/{app_id}/resolve-document-request",
        json={
            "uploaded_doc_ids": [str(doc_id)],
            "comments": "Signed DPR uploaded."
        },
        headers=data["headers_citizen"]
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["routing_status"] == "UNDER_REVIEW"

    # 15. Partner Officer Approves Sanction
    approve_res = client.post(
        f"/admin/partner/applications/{app_id}/action",
        json={
            "action": "APPROVED",
            "reason": "Credit facility and subsidy sanctioned."
        },
        headers=data["headers_partner"]
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["current_routing_status"] == "APPROVED"

    # 16. Inbound PFMS Webhook Dispatches DBT Settlement
    secret = "pfms-webhook-production-secret-key-32chars"
    with patch("app.services.integrations_service.get_settings", return_value=Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        SECRET_KEY="dev-secret-key-32chars-minimum-length",
        PFMS_WEBHOOK_SECRET=secret
    )):
        webhook_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "PFMS_DISBURSEMENT_SETTLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "application_id": str(app_id),
                "partner_reference_code": app_submitted["partner_reference_code"],
                "transaction_utr": "PFMS2026091000987",
                "amount_inr": 2500000.0
            },
            "source": "pfms_dbt_gateway"
        }
        body_bytes = json.dumps(webhook_payload).encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        wh_res = client.post(
            "/integrations/webhooks/pfms",
            content=body_bytes,
            headers={"Content-Type": "application/json", "X-Signature": sig}
        )
        assert wh_res.status_code == 200
        assert wh_res.json()["success"] is True

    # 17. Citizen Checks Disbursed Status
    final_track_res = client.get(f"/applications/{app_id}/tracking", headers=data["headers_citizen"])
    assert final_track_res.status_code == 200
    final_data = final_track_res.json()
    assert final_data["status"] == "disbursed"
    assert final_data["routing_status"] == "DISBURSED"
    assert final_data["disbursement_progress"]["status"] == "DISBURSED"
    assert "PFMS" in final_data["disbursement_progress"]["reference_number"]


def test_unconfigured_gateways_never_fabricate_banking_or_pfms_data(client, e2e_fixture):
    """Verify banking and PFMS endpoints return CONFIGURATION_READY and never fake records."""
    data = e2e_fixture
    partner_id = data["partner"].id

    # 1. CBS Metrics (unconfigured)
    cbs_res = client.get(f"/integrations/banking/partner/{partner_id}/metrics", headers=data["headers_partner"])
    assert cbs_res.status_code == 200
    cbs = cbs_res.json()
    assert cbs["sync_status"].lower() == "configuration_ready"
    assert cbs["is_authenticated_live"] is False
    assert "fabricated" in cbs["disclosure"].lower()

    # 2. NPA & Fund Utilization (unconfigured)
    npa_res = client.get(f"/integrations/banking/partner/{partner_id}/npa-utilization", headers=data["headers_partner"])
    assert npa_res.status_code == 200
    npa = npa_res.json()
    assert npa["sync_status"].lower() == "configuration_ready"
    assert npa["gross_npa_ratio"] is None
    assert "fabricated" in npa["disclosure"].lower()

    # 3. Lending Capacity (unconfigured)
    cap_res = client.get(f"/integrations/banking/partner/{partner_id}/lending-capacity", headers=data["headers_partner"])
    assert cap_res.status_code == 200
    cap = cap_res.json()
    assert cap["sync_status"].lower() == "configuration_ready"
    assert cap["available_lending_capacity_inr"] is None
    assert "fabricated" in cap["disclosure"].lower()

    # 4. PFMS DBT Status Query (unconfigured)
    pfms_res = client.post(
        "/integrations/pfms/dbt-status",
        json={"partner_reference_code": "YOJ-2026-TEST-001", "beneficiary_account_last_four": "5544"},
        headers=data["headers_citizen"]
    )
    assert pfms_res.status_code == 200
    pfms = pfms_res.json()
    assert pfms["dbt_status"] in ["NOT_FOUND", "CONFIGURATION_READY"]
    assert "fabricated" in pfms["disclosure"].lower()


def test_partner_and_admin_rbac_isolation(client, e2e_fixture):
    """Ensure strict separation of roles between Citizen, Partner Officer, and Admin."""
    data = e2e_fixture

    # 1. Citizen cannot access Admin endpoints -> 403
    assert client.get("/admin/users", headers=data["headers_citizen"]).status_code == 403
    assert client.get("/admin/analytics/bias", headers=data["headers_citizen"]).status_code == 403

    # 2. Citizen cannot access Partner Overview -> 403
    assert client.get("/admin/partner/overview", headers=data["headers_citizen"]).status_code == 403

    # 3. Partner Officer cannot access Super Admin User List -> 403
    assert client.get("/admin/users", headers=data["headers_partner"]).status_code == 403

    # 4. Admin CAN access all administrative resources
    assert client.get("/admin/users", headers=data["headers_admin"]).status_code == 200
    assert client.get("/admin/partner/overview", headers=data["headers_admin"]).status_code == 200


def test_scheme_catalog_data_integrity_and_valid_official_urls():
    """Verify all 63 schemes have non-empty official URLs pointing to legitimate portals."""
    assert len(ALL_SCHEMES) == 63, f"Expected 63 schemes, found {len(ALL_SCHEMES)}"

    valid_domains = [".gov.in", ".nic.in", ".org.in", ".bank.in", "sbi.co.in", "vcfsc.in", "cgtmse.in", "standupmitra.in", "udyamimitra.in", "nidhi-eir.in", "scsthub.in", "meitystartuphub.in", "nmdfc.org"]
    for s in ALL_SCHEMES:
        name = s.get("name")
        url = s.get("official_url")
        assert url is not None and len(url) > 0, f"Scheme {name} has missing official_url"
        assert url.startswith("https://") or url.startswith("http://"), f"Scheme {name} URL not HTTP(S): {url}"
        assert any(d in url.lower() for d in valid_domains), f"Scheme {name} URL '{url}' not in recognized official portal domains"


def test_multilingual_and_accessibility_readiness(client):
    """Verify 12 Scheduled Indian languages registry and accessibility security headers."""
    res = client.get("/locales")
    assert res.status_code == 200
    locales = res.json()["supported_languages"]
    assert len(locales) == 12

    # Check Hindi dictionary
    hi_res = client.get("/locales/hi")
    assert hi_res.status_code == 200
    assert "messages" in hi_res.json()

    # Verify accessibility & security headers
    h_res = client.get("/health")
    assert h_res.headers.get("X-Content-Type-Options") == "nosniff"
    assert h_res.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in h_res.headers
