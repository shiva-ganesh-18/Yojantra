"""Tests for Part 5: Channel Partner Response Workflow.
Verifies authorized partner/nodal actions (PARTNER_RECEIVED, UNDER_REVIEW, DOCUMENTS_REQUIRED, APPROVED, REJECTED),
security restrictions, mandatory reasons, audit trails, and applicant notifications.
"""
from datetime import datetime
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models import User, Scheme, Application, Institution, Notification
from app.services.partner_routing_status_service import (
    PartnerRoutingStatus,
    PartnerAcknowledgementStatus
)
from app.core.security import create_access_token


@pytest.fixture
def partner_workflow_fixture(test_db):
    """Fixture providing citizen, partner officer, nodal officer, admin, and a scheme."""
    citizen = User(
        id=uuid.uuid4(),
        phone="+919876543220",
        email="applicant.msme@example.in",
        full_name="Aarav Patel",
        role="user",
        is_active=True,
        state="Gujarat",
        district="Ahmedabad"
    )
    unauth_citizen = User(
        id=uuid.uuid4(),
        phone="+919876543221",
        email="stranger@example.in",
        full_name="Other Citizen",
        role="user",
        is_active=True,
        state="Gujarat",
        district="Ahmedabad"
    )
    partner_officer = User(
        id=uuid.uuid4(),
        phone="+919876543222",
        email="lead.officer@sbi.co.in",
        full_name="SBI Credit Appraisal Officer",
        role="partner_officer",
        is_active=True,
        state="Gujarat",
        district="Ahmedabad"
    )
    nodal_officer = User(
        id=uuid.uuid4(),
        phone="+919876543223",
        email="nodal.officer@dic.gujarat.gov.in",
        full_name="DIC Nodal Task Force",
        role="nodal_officer",
        is_active=True,
        state="Gujarat",
        district="Ahmedabad"
    )
    admin_user = User(
        id=uuid.uuid4(),
        phone="+919876543224",
        email="system.admin@yojantra.in",
        full_name="Admin Desk",
        role="admin",
        is_active=True
    )
    partner_bank = Institution(
        id=uuid.uuid4(),
        name="State Bank of India - Ahmedabad SME Branch",
        short_name="SBI-AHMD",
        institution_type="PSB",
        state="Gujarat",
        district="Ahmedabad",
        city="Ahmedabad",
        status="active"
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Credit Linked Capital Subsidy Scheme (CLCSS)",
        ministry="Ministry of MSME",
        description="Technology upgradation subsidy for micro & small enterprises",
        max_benefit_inr=Decimal("1500000"),
        status="active"
    )

    test_db.add_all([citizen, unauth_citizen, partner_officer, nodal_officer, admin_user, partner_bank, scheme])
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
        "partner": partner_bank,
        "scheme": scheme,
        "headers_citizen": {"Authorization": f"Bearer {tok_citizen}"},
        "headers_unauth": {"Authorization": f"Bearer {tok_unauth}"},
        "headers_partner": {"Authorization": f"Bearer {tok_partner}"},
        "headers_nodal": {"Authorization": f"Bearer {tok_nodal}"},
        "headers_admin": {"Authorization": f"Bearer {tok_admin}"}
    }


def _create_and_submit_test_application(client, f):
    """Helper to create and route an application to ROUTED_TO_PARTNER."""
    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online",
        "requested_amount_inr": 800000.0
    }, headers=f["headers_citizen"])
    assert create_res.status_code == 200
    app_id = create_res.json()["id"]

    sub_res = client.post(f"/applications/{app_id}/submit", headers=f["headers_citizen"])
    assert sub_res.status_code == 200
    assert sub_res.json()["routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert sub_res.json()["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.PENDING.value
    return app_id


def test_partner_officer_can_acknowledge_receipt(client, partner_workflow_fixture, test_db):
    """Test that an accredited partner officer can acknowledge dossier receipt (PARTNER_RECEIVED)."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    # Partner officer acknowledges receipt
    res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "PARTNER_RECEIVED",
        "reason": "Application dossier received and logged at branch SME desk.",
        "partner_id": str(f["partner"].id),
        "partner_name": f["partner"].name,
        "source": "partner_portal"
    }, headers=f["headers_partner"])

    assert res.status_code == 200
    data = res.json()
    assert data["current_routing_status"] == PartnerRoutingStatus.PARTNER_RECEIVED.value
    assert data["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.ACKNOWLEDGED.value

    # Check notification sent to applicant
    notif = test_db.query(Notification).filter(
        Notification.user_id == f["citizen"].id,
        Notification.title.like("%Acknowledged%")
    ).first()
    assert notif is not None
    assert f["partner"].name in notif.body


def test_nodal_officer_can_start_review_and_request_documents(client, partner_workflow_fixture, test_db):
    """Test full scrutiny cycle: PARTNER_RECEIVED -> UNDER_REVIEW -> DOCUMENTS_REQUIRED."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    # 1. Partner acknowledges receipt
    client.post(f"/applications/{app_id}/partner-response", json={
        "action": "PARTNER_RECEIVED",
        "reason": "Received.",
        "partner_name": f["partner"].name
    }, headers=f["headers_partner"])

    # 2. Nodal officer starts review
    review_res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "UNDER_REVIEW",
        "reason": "Reviewing plant machinery quotation and UDYAM certificate compliance.",
        "source": "nodal_portal"
    }, headers=f["headers_nodal"])
    assert review_res.status_code == 200
    assert review_res.json()["current_routing_status"] == PartnerRoutingStatus.UNDER_REVIEW.value

    # 3. Nodal officer raises compliance query requesting documents
    doc_req_res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "DOCUMENTS_REQUIRED",
        "reason": "Pollution control NOC and audited 3-year balance sheet missing.",
        "source": "nodal_portal"
    }, headers=f["headers_nodal"])
    assert doc_req_res.status_code == 200
    assert doc_req_res.json()["current_routing_status"] == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value

    # Verify notification with high priority
    notif = test_db.query(Notification).filter(
        Notification.user_id == f["citizen"].id,
        Notification.title.like("%Documents Requested%")
    ).first()
    assert notif is not None
    assert notif.priority == "high"
    assert "Pollution control NOC" in notif.body


def test_mandatory_reason_required_for_documents_required_and_rejected(client, partner_workflow_fixture):
    """Test that DOCUMENTS_REQUIRED and REJECTED strictly require a non-empty reason."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    # Acknowledge and move to under review
    client.post(f"/applications/{app_id}/partner-response", json={
        "action": "PARTNER_RECEIVED",
        "reason": "Docket received."
    }, headers=f["headers_partner"])

    client.post(f"/applications/{app_id}/partner-response", json={
        "action": "UNDER_REVIEW",
        "reason": "Commencing review."
    }, headers=f["headers_nodal"])

    # 1. Attempt DOCUMENTS_REQUIRED with empty reason: MUST FAIL 400
    fail_empty_res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "DOCUMENTS_REQUIRED",
        "reason": ""
    }, headers=f["headers_nodal"])
    assert fail_empty_res.status_code == 400
    assert "reason is strictly required" in fail_empty_res.json()["detail"].lower()

    # Attempt with whitespace reason: MUST FAIL 400
    fail_ws_res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "DOCUMENTS_REQUIRED",
        "reason": "   "
    }, headers=f["headers_nodal"])
    assert fail_ws_res.status_code == 400

    # 2. Attempt REJECTED with empty reason: MUST FAIL 400
    fail_rej_empty = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "REJECTED",
        "reason": ""
    }, headers=f["headers_nodal"])
    assert fail_rej_empty.status_code == 400
    assert "reason is strictly required" in fail_rej_empty.json()["detail"].lower()

    # 3. Successful rejection with valid reason
    ok_rej = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "REJECTED",
        "reason": "Enterprise investment in plant and machinery exceeds scheme ceiling of ₹15 Lakhs."
    }, headers=f["headers_nodal"])
    assert ok_rej.status_code == 200
    assert ok_rej.json()["current_routing_status"] == PartnerRoutingStatus.REJECTED.value


def test_applicant_blocked_from_submitting_partner_responses(client, partner_workflow_fixture):
    """Test that applicants cannot self-acknowledge, approve, reject, or call partner-response."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    # 1. Citizen calling /partner-response is blocked with 403
    cit_res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "APPROVED",
        "reason": "Beneficiary self-approval attempt."
    }, headers=f["headers_citizen"])
    assert cit_res.status_code == 403
    assert "Forbidden" in cit_res.json()["detail"]

    # 2. Citizen trying PARTNER_RECEIVED via /routing-status is blocked with 403
    recv_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": "PARTNER_RECEIVED",
        "reason": "Faking partner receipt."
    }, headers=f["headers_citizen"])
    assert recv_res.status_code == 403

    # 3. Citizen trying REJECTED via /routing-status is blocked with 403
    rej_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": "REJECTED",
        "reason": "Rejecting own application."
    }, headers=f["headers_citizen"])
    assert rej_res.status_code == 403

    # 4. Citizen trying APPROVED via /routing-status is blocked with 403
    appr_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": "APPROVED",
        "reason": "Approving own loan."
    }, headers=f["headers_citizen"])
    assert appr_res.status_code == 403


def test_unauthorized_user_blocked_from_partner_response(client, partner_workflow_fixture):
    """Test that unauthorized random citizens cannot respond to another applicant's application."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "APPROVED",
        "reason": "Unauthorized access."
    }, headers=f["headers_unauth"])
    assert res.status_code == 403


def test_partner_approval_workflow_and_audit_trail(client, partner_workflow_fixture, test_db):
    """Test complete approved workflow: ROUTED -> RECEIVED -> UNDER_REVIEW -> APPROVED with audit check."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    # Step 1: Partner Received
    client.post(f"/applications/{app_id}/partner-response", json={
        "action": "PARTNER_RECEIVED",
        "reason": "Branch received application dossier.",
        "partner_name": f["partner"].name,
        "source": "partner_portal"
    }, headers=f["headers_partner"])

    # Step 2: Under Review
    client.post(f"/applications/{app_id}/partner-response", json={
        "action": "UNDER_REVIEW",
        "reason": "Credit officer appraisal complete; viability approved.",
        "source": "partner_portal"
    }, headers=f["headers_partner"])

    # Step 3: Approved
    appr_res = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "APPROVED",
        "reason": "Sanction letter approved for ₹8 Lakhs term loan with 15% upfront capital subsidy.",
        "partner_name": f["partner"].name,
        "source": "nodal_portal"
    }, headers=f["headers_nodal"])
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["current_routing_status"] == PartnerRoutingStatus.APPROVED.value

    # Check notification
    notif = test_db.query(Notification).filter(
        Notification.user_id == f["citizen"].id,
        Notification.title.like("%Approved%")
    ).first()
    assert notif is not None
    assert notif.priority == "high"
    assert "Sanction letter approved" in notif.body

    # Check audit trail entries
    assert len(appr_data["history"]) >= 4
    approved_entry = appr_data["history"][-1]
    assert approved_entry["from_status"] == PartnerRoutingStatus.UNDER_REVIEW.value
    assert approved_entry["to_status"] == PartnerRoutingStatus.APPROVED.value
    assert approved_entry["actor"] == f["nodal_officer"].email
    assert approved_entry["actor_role"] == "nodal_officer"
    assert approved_entry["source"] == "nodal_portal"
    assert "Sanction letter approved" in approved_entry["reason"]


def test_invalid_partner_transitions_blocked(client, partner_workflow_fixture):
    """Test that invalid jumps (e.g. ROUTED_TO_PARTNER directly to APPROVED) are blocked with 400."""
    f = partner_workflow_fixture
    app_id = _create_and_submit_test_application(client, f)

    # Attempt to approve without receiving and review: MUST FAIL 400
    jump_appr = client.post(f"/applications/{app_id}/partner-response", json={
        "action": "APPROVED",
        "reason": "Direct jump from routed to approved."
    }, headers=f["headers_nodal"])
    assert jump_appr.status_code == 400
    assert "Invalid routing status transition" in jump_appr.json()["detail"]
