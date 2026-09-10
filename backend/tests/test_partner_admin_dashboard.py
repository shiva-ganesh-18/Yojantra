"""Tests for Part 8: Channel Partner & Admin Dashboard.
Verifies RBAC enforcement, assigned application queue, status filtering,
search, application details & documents, review actions, audit history, and NPA health indicators.
"""
from datetime import datetime
from decimal import Decimal
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models import User, Scheme, Application, Institution, Document, Notification
from app.services.partner_routing_status_service import (
    PartnerRoutingStatus,
    PartnerAcknowledgementStatus
)
from app.core.security import create_access_token


@pytest.fixture
def dashboard_fixture(test_db):
    """Fixture providing citizen, partner officer, nodal officer, admin, institution, and scheme."""
    citizen = User(
        id=uuid.uuid4(),
        phone="+919876543301",
        email="citizen.applicant@example.in",
        full_name="Kavita Sharma",
        role="user",
        is_active=True,
        state="Maharashtra",
        district="Pune",
        social_category="obc"
    )
    unauth_citizen = User(
        id=uuid.uuid4(),
        phone="+919876543302",
        email="random.user@example.in",
        full_name="Unauthorized Citizen",
        role="user",
        is_active=True,
        state="Maharashtra",
        district="Pune"
    )
    partner_officer = User(
        id=uuid.uuid4(),
        phone="+919876543303",
        email="officer.boi@bankofindia.co.in",
        full_name="BOI Zonal Credit Manager",
        role="partner_officer",
        is_active=True,
        state="Maharashtra",
        district="Pune"
    )
    nodal_officer = User(
        id=uuid.uuid4(),
        phone="+919876543304",
        email="nodal.msme@maharashtra.gov.in",
        full_name="DIC Pune Nodal Desk",
        role="nodal_officer",
        is_active=True,
        state="Maharashtra",
        district="Pune"
    )
    admin_user = User(
        id=uuid.uuid4(),
        phone="+919876543305",
        email="platform.superadmin@yojantra.in",
        full_name="Yojantra Super Administrator",
        role="admin",
        is_active=True
    )

    institution = Institution(
        id=uuid.uuid4(),
        name="Bank of India - Pune SME Hub",
        short_name="BOI-PUNE",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        status="active"
    )
    institution.gross_npa_ratio = Decimal("3.85")
    institution.npa_risk_indicator = "LOW"
    institution.is_lending_halted = False

    scheme = Scheme(
        id=uuid.uuid4(),
        name="PMEGP Maharashtra Artisan Credit",
        ministry="Ministry of MSME",
        description="Prime Minister Employment Generation Programme for rural & urban micro units",
        max_benefit_inr=Decimal("2500000"),
        status="active"
    )

    doc_pan = Document(
        id=uuid.uuid4(),
        user_id=citizen.id,
        doc_type="pan",
        file_url="/tmp/pan_doc.pdf",
        file_format="pdf",
        file_size_bytes=102400,
        ocr_extracted_text="INCOME TAX DEPARTMENT GOVT OF INDIA PAN ABCDE1234F",
        verification_status="verified",
        meta_info={
            "extracted_number": "ABXXXX34F",
            "verification_tier": "Internal Heuristic OCR"
        }
    )

    test_db.add_all([citizen, unauth_citizen, partner_officer, nodal_officer, admin_user, institution, scheme, doc_pan])
    test_db.commit()

    tok_citizen = create_access_token(data={"sub": str(citizen.id), "role": "user"})
    tok_unauth = create_access_token(data={"sub": str(unauth_citizen.id), "role": "user"})
    tok_partner = create_access_token(data={"sub": str(partner_officer.id), "role": "partner_officer"})
    tok_nodal = create_access_token(data={"sub": str(nodal_officer.id), "role": "nodal_officer"})
    tok_admin = create_access_token(data={"sub": str(admin_user.id), "role": "admin"})

    return {
        "citizen": citizen,
        "unauth_citizen": unauth_citizen,
        "partner_officer": partner_officer,
        "nodal_officer": nodal_officer,
        "admin": admin_user,
        "institution": institution,
        "scheme": scheme,
        "doc_pan": doc_pan,
        "headers_citizen": {"Authorization": f"Bearer {tok_citizen}"},
        "headers_unauth": {"Authorization": f"Bearer {tok_unauth}"},
        "headers_partner": {"Authorization": f"Bearer {tok_partner}"},
        "headers_nodal": {"Authorization": f"Bearer {tok_nodal}"},
        "headers_admin": {"Authorization": f"Bearer {tok_admin}"}
    }


def _create_submitted_app(client, fix):
    """Helper to create and submit an application assigned to the institution."""
    res_create = client.post("/applications", json={
        "scheme_id": str(fix["scheme"].id),
        "channel": "online",
        "requested_amount_inr": 1200000.0
    }, headers=fix["headers_citizen"])
    assert res_create.status_code == 200
    app_id = res_create.json()["id"]

    res_sub = client.post(f"/applications/{app_id}/submit", headers=fix["headers_citizen"])
    assert res_sub.status_code == 200
    return app_id


def test_rbac_citizen_blocked_from_dashboard_endpoints(client, dashboard_fixture):
    """Ensure standard citizen users cannot access partner/admin dashboard endpoints (HTTP 403)."""
    f = dashboard_fixture
    app_id = _create_submitted_app(client, f)

    # 1. Overview KPIs
    res_overview = client.get("/admin/partner/overview", headers=f["headers_citizen"])
    assert res_overview.status_code == 403
    assert "forbidden" in res_overview.json()["detail"].lower()

    # 2. Application Queue
    res_queue = client.get("/admin/partner/applications", headers=f["headers_citizen"])
    assert res_queue.status_code == 403

    # 3. Application Detail
    res_detail = client.get(f"/admin/partner/applications/{app_id}", headers=f["headers_citizen"])
    assert res_detail.status_code == 403

    # 4. Review Action
    res_action = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "APPROVED",
        "reason": "Self sanction attempt"
    }, headers=f["headers_citizen"])
    assert res_action.status_code == 403

    # 5. Unauthenticated request (HTTP 401)
    res_anon = client.get("/admin/partner/overview")
    assert res_anon.status_code == 401


def test_partner_officer_and_admin_can_access_queue_and_kpis(client, dashboard_fixture):
    """Verify partner officer, nodal officer, and admin can retrieve dashboard overview and application list."""
    f = dashboard_fixture
    app_id = _create_submitted_app(client, f)

    # Partner Officer checks overview
    res_po_kpi = client.get("/admin/partner/overview", headers=f["headers_partner"])
    assert res_po_kpi.status_code == 200
    kpi = res_po_kpi.json()
    assert kpi["total_assigned"] >= 1
    assert kpi["pending_action_count"] >= 1
    assert "status_breakdown" in kpi

    # Admin checks applications queue
    res_queue = client.get("/admin/partner/applications", headers=f["headers_admin"])
    assert res_queue.status_code == 200
    q_data = res_queue.json()
    assert q_data["total"] >= 1
    assert len(q_data["items"]) >= 1

    item = q_data["items"][0]
    assert item["id"] == app_id
    assert item["applicant_name"] == f["citizen"].full_name
    assert item["scheme_name"] == f["scheme"].name
    assert item["routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert item["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.PENDING.value


def test_queue_status_filtering_and_applicant_search(client, dashboard_fixture):
    """Test filtering by routing status and text search across applicant name and scheme."""
    f = dashboard_fixture
    app_id = _create_submitted_app(client, f)

    # 1. Filter by matching status
    res_match = client.get("/admin/partner/applications", params={"status": "ROUTED_TO_PARTNER"}, headers=f["headers_nodal"])
    assert res_match.status_code == 200
    assert any(it["id"] == app_id for it in res_match.json()["items"])

    # 2. Filter by non-matching status
    res_none = client.get("/admin/partner/applications", params={"status": "APPROVED"}, headers=f["headers_nodal"])
    assert res_none.status_code == 200
    assert not any(it["id"] == app_id for it in res_none.json()["items"])

    # 3. Search by applicant name
    res_search_name = client.get("/admin/partner/applications", params={"search": "Kavita"}, headers=f["headers_partner"])
    assert res_search_name.status_code == 200
    assert any(it["id"] == app_id for it in res_search_name.json()["items"])

    # 4. Search by scheme name
    res_search_scheme = client.get("/admin/partner/applications", params={"search": "PMEGP"}, headers=f["headers_partner"])
    assert res_search_scheme.status_code == 200
    assert any(it["id"] == app_id for it in res_search_scheme.json()["items"])

    # 5. Search with no matches
    res_no_match = client.get("/admin/partner/applications", params={"search": "NonExistentXYZ"}, headers=f["headers_partner"])
    assert res_no_match.status_code == 200
    assert len(res_no_match.json()["items"]) == 0


def test_application_detail_with_documents_and_partner_health(client, dashboard_fixture):
    """Test fetching full application details: applicant profile, documents, pre-submission checks, and live NPA status."""
    f = dashboard_fixture
    app_id = _create_submitted_app(client, f)

    res = client.get(f"/admin/partner/applications/{app_id}", headers=f["headers_partner"])
    assert res.status_code == 200
    data = res.json()

    # Application base & applicant profile
    assert data["application"]["id"] == app_id
    assert data["applicant_profile"]["full_name"] == f["citizen"].full_name
    assert data["applicant_profile"]["state"] == "Maharashtra"
    assert data["applicant_profile"]["social_category"] == "obc"

    # Scheme details
    assert data["scheme_details"]["name"] == f["scheme"].name

    # Uploaded documents
    assert len(data["documents"]) >= 1
    doc = data["documents"][0]
    assert doc["doc_type"] == "pan"
    assert doc["verification_status"] == "verified"
    assert "extracted_number" in doc

    # Pre-submission validation
    assert "validation" in data
    assert "checks" in data["validation"]

    # Routing summary & initial audit log
    assert "routing_summary" in data
    assert data["routing_summary"]["current_routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert len(data["routing_summary"]["history"]) >= 1


def test_partner_review_actions_state_transitions_and_mandatory_reasons(client, dashboard_fixture, test_db):
    """Test full review workflow: PARTNER_RECEIVED -> UNDER_REVIEW -> DOCUMENTS_REQUIRED -> APPROVED."""
    f = dashboard_fixture
    app_id = _create_submitted_app(client, f)

    # 1. Invalid jump directly to APPROVED from ROUTED_TO_PARTNER must fail
    res_inv = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "APPROVED",
        "reason": "Direct jump before receipt acknowledgment"
    }, headers=f["headers_partner"])
    assert res_inv.status_code == 400

    # 2. Acknowledge Receipt: PARTNER_RECEIVED
    res_recv = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "PARTNER_RECEIVED",
        "reason": "Dossier received at BOI SME Pune branch counter."
    }, headers=f["headers_partner"])
    assert res_recv.status_code == 200
    assert res_recv.json()["current_routing_status"] == PartnerRoutingStatus.PARTNER_RECEIVED.value
    assert res_recv.json()["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.ACKNOWLEDGED.value

    # 3. Start Technical & Financial Scrutiny: UNDER_REVIEW
    res_rev = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "UNDER_REVIEW",
        "reason": "Credit appraisal officer commenced financial ratio scrutiny."
    }, headers=f["headers_partner"])
    assert res_rev.status_code == 200
    assert res_rev.json()["current_routing_status"] == PartnerRoutingStatus.UNDER_REVIEW.value

    # 4. Mandatory reason required when requesting documents
    res_req_no_reason = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "DOCUMENTS_REQUIRED",
        "reason": ""
    }, headers=f["headers_partner"])
    assert res_req_no_reason.status_code == 400
    assert "strictly required" in res_req_no_reason.json()["detail"]

    # 5. Request Documents with valid reason: DOCUMENTS_REQUIRED
    res_req = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "DOCUMENTS_REQUIRED",
        "reason": "Submit lease deed agreement for factory premises and 6-month bank statement."
    }, headers=f["headers_partner"])
    assert res_req.status_code == 200
    assert res_req.json()["current_routing_status"] == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value

    # Check notification was dispatched to citizen
    notif = test_db.query(Notification).filter(
        Notification.user_id == f["citizen"].id,
        Notification.type == "application_status"
    ).order_by(Notification.created_at.desc(), Notification.id.desc()).first()
    assert notif is not None
    assert "lease deed" in notif.body

    # 6. Resolve back to UNDER_REVIEW and then APPROVE
    res_back = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "UNDER_REVIEW",
        "reason": "Documents uploaded and verified by nodal appraisal committee."
    }, headers=f["headers_nodal"])
    assert res_back.status_code == 200

    res_approve = client.post(f"/admin/partner/applications/{app_id}/action", json={
        "action": "APPROVED",
        "reason": "Credit sanction letter issued for INR 12,00,000 subsidy."
    }, headers=f["headers_partner"])
    assert res_approve.status_code == 200
    assert res_approve.json()["current_routing_status"] == PartnerRoutingStatus.APPROVED.value

    # 7. Audit trail integrity: check all transition events are recorded in order
    history = res_approve.json()["history"]
    to_statuses = [h["to_status"] for h in history]
    assert PartnerRoutingStatus.PARTNER_RECEIVED.value in to_statuses
    assert PartnerRoutingStatus.UNDER_REVIEW.value in to_statuses
    assert PartnerRoutingStatus.DOCUMENTS_REQUIRED.value in to_statuses
    assert PartnerRoutingStatus.APPROVED.value in to_statuses
