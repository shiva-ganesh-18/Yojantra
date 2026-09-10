"""Tests for Part 4: Application Partner Routing Status, State Machine, Audit Trails, and Security."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models import User, Scheme, Application, Institution, Document, Business
from app.services.partner_routing_status_service import (
    PartnerRoutingStatus,
    PartnerAcknowledgementStatus,
    PartnerRoutingStatusService,
    ALLOWED_ROUTING_TRANSITIONS
)
from app.core.security import create_access_token


@pytest.fixture
def routing_fixture(test_db):
    """Fixture providing citizen user, nodal officer, bank partner, scheme, and auth tokens."""
    citizen = User(
        id=uuid.uuid4(),
        phone="+919876543210",
        email="citizen@example.in",
        full_name="Rajesh Kumar",
        role="user",
        is_active=True,
        state="Maharashtra",
        district="Pune"
    )
    unauthorized_citizen = User(
        id=uuid.uuid4(),
        phone="+919876543211",
        email="other@example.in",
        full_name="Sunita Sharma",
        role="user",
        is_active=True,
        state="Maharashtra",
        district="Pune"
    )
    nodal_officer = User(
        id=uuid.uuid4(),
        phone="+919876543212",
        email="officer@dic.gov.in",
        full_name="District Nodal Officer",
        role="nodal_officer",
        is_active=True,
        state="Maharashtra",
        district="Pune"
    )
    admin_user = User(
        id=uuid.uuid4(),
        phone="+919876543213",
        email="admin@yojantra.in",
        full_name="Platform Admin",
        role="admin",
        is_active=True
    )
    partner = Institution(
        id=uuid.uuid4(),
        name="Bank of Maharashtra - Pune Camp Branch",
        short_name="BOM-PUNE",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        status="active"
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Prime Minister's Employment Generation Programme (PMEGP)",
        ministry="Ministry of MSME",
        description="Credit-linked subsidy programme for micro enterprises",
        max_benefit_inr=Decimal("2500000"),
        status="active"
    )
    test_db.add_all([citizen, unauthorized_citizen, nodal_officer, admin_user, partner, scheme])
    test_db.commit()

    token_citizen = create_access_token(data={"sub": str(citizen.id), "role": "user"})
    token_unauth = create_access_token(data={"sub": str(unauthorized_citizen.id), "role": "user"})
    token_officer = create_access_token(data={"sub": str(nodal_officer.id), "role": "nodal_officer"})
    token_admin = create_access_token(data={"sub": str(admin_user.id), "role": "admin"})

    return {
        "citizen": citizen,
        "unauthorized_citizen": unauthorized_citizen,
        "nodal_officer": nodal_officer,
        "admin": admin_user,
        "partner": partner,
        "scheme": scheme,
        "headers_citizen": {"Authorization": f"Bearer {token_citizen}"},
        "headers_unauth": {"Authorization": f"Bearer {token_unauth}"},
        "headers_officer": {"Authorization": f"Bearer {token_officer}"},
        "headers_admin": {"Authorization": f"Bearer {token_admin}"}
    }


def test_initial_application_creation_routing_status(client, routing_fixture):
    """Test that creating an application assigns initial routing status and initial audit trail."""
    f = routing_fixture
    create_payload = {
        "scheme_id": str(f["scheme"].id),
        "channel": "online",
        "requested_amount_inr": 500000.0,
        "application_data": {"project_type": "Manufacturing"}
    }
    res = client.post("/applications", json=create_payload, headers=f["headers_citizen"])
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "draft"
    assert data["routing_status"] in [PartnerRoutingStatus.PARTNER_ASSIGNED.value, PartnerRoutingStatus.NOT_ROUTED.value]
    assert data["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.NOT_ROUTED.value
    assert len(data["routing_history"]) >= 1
    assert data["routing_history"][0]["actor"] == f["citizen"].email
    assert data["routing_history"][0]["source"] == "citizen_portal"


def test_full_lifecycle_state_machine_transitions(client, routing_fixture):
    """
    Test valid step-by-step lifecycle transition through the 10 routing states:
    NOT_ROUTED / PARTNER_ASSIGNED -> ROUTED_TO_PARTNER -> PARTNER_RECEIVED -> 
    UNDER_REVIEW -> DOCUMENTS_REQUIRED -> UNDER_REVIEW -> APPROVED -> 
    DISBURSEMENT_PROCESSING -> DISBURSED
    """
    f = routing_fixture

    # 1. Create application
    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online",
        "requested_amount_inr": 400000.0
    }, headers=f["headers_citizen"])
    assert create_res.status_code == 200
    app_id = create_res.json()["id"]

    # 2. Citizen routes dossier: PARTNER_ASSIGNED -> ROUTED_TO_PARTNER
    route_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        "reason": "Applicant uploaded required documents and routed dossier to accredited bank.",
        "partner_id": str(f["partner"].id),
        "partner_name": f["partner"].name,
        "source": "citizen_portal"
    }, headers=f["headers_citizen"])
    assert route_res.status_code == 200
    route_data = route_res.json()
    assert route_data["current_routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    # Transparency check: acknowledgement must be PENDING (no fake receipt)
    assert route_data["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.PENDING.value

    # 3. Nodal Officer acknowledges receipt: ROUTED_TO_PARTNER -> PARTNER_RECEIVED
    recv_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.PARTNER_RECEIVED.value,
        "reason": "Dossier physical/digital docket received and logged at DIC nodal center.",
        "partner_id": str(f["partner"].id),
        "partner_name": f["partner"].name,
        "source": "partner_api"
    }, headers=f["headers_officer"])
    assert recv_res.status_code == 200
    recv_data = recv_res.json()
    assert recv_data["current_routing_status"] == PartnerRoutingStatus.PARTNER_RECEIVED.value
    assert recv_data["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.ACKNOWLEDGED.value

    # 4. Officer starts formal scrutiny: PARTNER_RECEIVED -> UNDER_REVIEW
    review_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.UNDER_REVIEW.value,
        "reason": "Scrutiny of financial viability and borrower KYC under PMEGP guidelines.",
        "source": "nodal_portal"
    }, headers=f["headers_officer"])
    assert review_res.status_code == 200
    assert review_res.json()["current_routing_status"] == PartnerRoutingStatus.UNDER_REVIEW.value

    # 5. Officer requests clarification: UNDER_REVIEW -> DOCUMENTS_REQUIRED
    doc_req_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.DOCUMENTS_REQUIRED.value,
        "reason": "Quotation for machinery and rent agreement copy missing.",
        "source": "nodal_portal"
    }, headers=f["headers_officer"])
    assert doc_req_res.status_code == 200
    assert doc_req_res.json()["current_routing_status"] == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value

    # 6. Citizen provides documents: DOCUMENTS_REQUIRED -> UNDER_REVIEW
    doc_sub_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.UNDER_REVIEW.value,
        "reason": "Applicant re-uploaded valid machinery proforma invoice and lease deed.",
        "source": "citizen_portal"
    }, headers=f["headers_citizen"])
    assert doc_sub_res.status_code == 200
    assert doc_sub_res.json()["current_routing_status"] == PartnerRoutingStatus.UNDER_REVIEW.value

    # 7. Officer approves loan sanction: UNDER_REVIEW -> APPROVED
    appr_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.APPROVED.value,
        "reason": "Sanction letter approved by District Task Force Committee.",
        "source": "nodal_portal"
    }, headers=f["headers_officer"])
    assert appr_res.status_code == 200
    assert appr_res.json()["current_routing_status"] == PartnerRoutingStatus.APPROVED.value

    # 8. Disbursement process initiated: APPROVED -> DISBURSEMENT_PROCESSING
    proc_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value,
        "reason": "PFMS batch file generated for margin money subsidy credit.",
        "source": "dbt_gateway"
    }, headers=f["headers_officer"])
    assert proc_res.status_code == 200
    assert proc_res.json()["current_routing_status"] == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value

    # 9. Final disbursement: DISBURSEMENT_PROCESSING -> DISBURSED
    disb_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.DISBURSED.value,
        "reason": "Subsidy credited to beneficiary Aadhaar-linked account via PFMS.",
        "source": "pfms_webhook"
    }, headers=f["headers_officer"])
    assert disb_res.status_code == 200
    disb_data = disb_res.json()
    assert disb_data["current_routing_status"] == PartnerRoutingStatus.DISBURSED.value
    assert disb_data["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.ACKNOWLEDGED.value
    assert disb_data["allowed_next_transitions"] == []

    # Verify audit history length and entries
    assert len(disb_data["history"]) >= 9
    latest_event = disb_data["history"][-1]
    assert latest_event["from_status"] == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value
    assert latest_event["to_status"] == PartnerRoutingStatus.DISBURSED.value
    assert latest_event["actor"] == f["nodal_officer"].email
    assert latest_event["source"] == "pfms_webhook"


def test_invalid_status_transitions_are_blocked(client, routing_fixture):
    """Test that invalid jumps between routing statuses are strictly rejected with HTTP 400."""
    f = routing_fixture

    # Create draft application
    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online"
    }, headers=f["headers_citizen"])
    app_id = create_res.json()["id"]

    # 1. Cannot jump from PARTNER_ASSIGNED directly to DISBURSED
    jump_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.DISBURSED.value,
        "reason": "Attempting illegal jump to disbursed."
    }, headers=f["headers_officer"])
    assert jump_res.status_code == 400
    assert "Invalid routing status transition" in jump_res.json()["detail"]

    # 2. Cannot jump from PARTNER_ASSIGNED directly to APPROVED
    jump_res2 = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.APPROVED.value,
        "reason": "Attempting illegal jump to approved."
    }, headers=f["headers_officer"])
    assert jump_res2.status_code == 400

    # 3. Invalid status string rejected
    invalid_name_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": "SUPER_APPROVED",
        "reason": "Invalid non-existent status."
    }, headers=f["headers_officer"])
    assert invalid_name_res.status_code == 400
    assert "Invalid routing status 'SUPER_APPROVED'" in invalid_name_res.json()["detail"]


def test_terminal_states_cannot_transition(client, routing_fixture):
    """Test that terminal states (DISBURSED, REJECTED) cannot be transitioned to any other state."""
    f = routing_fixture

    # Create application
    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online"
    }, headers=f["headers_citizen"])
    app_id = create_res.json()["id"]

    # Route and reject
    client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        "reason": "Routed."
    }, headers=f["headers_citizen"])

    rej_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.REJECTED.value,
        "reason": "Project report unviable."
    }, headers=f["headers_officer"])
    assert rej_res.status_code == 200

    # Attempt transition from REJECTED
    attempt_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.UNDER_REVIEW.value,
        "reason": "Attempting transition from terminal rejected state."
    }, headers=f["headers_officer"])
    assert attempt_res.status_code == 400
    assert "Invalid routing status transition from 'REJECTED'" in attempt_res.json()["detail"]


def test_security_citizen_cannot_self_approve_or_disburse(client, routing_fixture):
    """Test that beneficiaries (role='user') are blocked with 403 if attempting to self-verify or self-approve."""
    f = routing_fixture

    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online"
    }, headers=f["headers_citizen"])
    app_id = create_res.json()["id"]

    # Citizen tries to directly transition to APPROVED or PARTNER_RECEIVED
    res_appr = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.APPROVED.value,
        "reason": "Self approving my own application."
    }, headers=f["headers_citizen"])
    assert res_appr.status_code == 403
    assert "Beneficiaries cannot self-verify, approve, disburse" in res_appr.json()["detail"]

    res_recv = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.PARTNER_RECEIVED.value,
        "reason": "Faking partner receipt."
    }, headers=f["headers_citizen"])
    assert res_recv.status_code == 403


def test_security_unauthorized_user_blocked(client, routing_fixture):
    """Test that a user cannot access or transition another user's application."""
    f = routing_fixture

    # User A creates application
    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online"
    }, headers=f["headers_citizen"])
    app_id = create_res.json()["id"]

    # User B (unauthorized citizen) tries to GET routing status
    get_res = client.get(f"/applications/{app_id}/routing-status", headers=f["headers_unauth"])
    assert get_res.status_code == 403
    assert "Not authorized" in get_res.json()["detail"]

    # User B tries to POST transition
    post_res = client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        "reason": "Unauthorized access attempt."
    }, headers=f["headers_unauth"])
    assert post_res.status_code == 403


def test_audit_event_recording_and_integrity(client, routing_fixture):
    """Test that each routing transition captures timestamp, partner, reason, actor, and source."""
    f = routing_fixture

    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online"
    }, headers=f["headers_citizen"])
    app_id = create_res.json()["id"]

    # Transition to ROUTED_TO_PARTNER
    client.post(f"/applications/{app_id}/routing-status", json={
        "to_status": PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        "reason": "Audit verification submission.",
        "partner_id": str(f["partner"].id),
        "partner_name": f["partner"].name,
        "source": "citizen_portal"
    }, headers=f["headers_citizen"])

    # Query status summary endpoint
    sum_res = client.get(f"/applications/{app_id}/routing-status", headers=f["headers_citizen"])
    assert sum_res.status_code == 200
    summary = sum_res.json()

    assert summary["application_id"] == app_id
    assert summary["current_routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert summary["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.PENDING.value
    assert summary["assigned_partner_name"] == f["partner"].name

    # Check history entries
    history = summary["history"]
    assert len(history) >= 2

    last_entry = history[-1]
    assert last_entry["from_status"] == PartnerRoutingStatus.PARTNER_ASSIGNED.value
    assert last_entry["to_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert last_entry["reason"] == "Audit verification submission."
    assert last_entry["actor"] == f["citizen"].email
    assert last_entry["actor_role"] == "user"
    assert last_entry["source"] == "citizen_portal"
    assert last_entry["partner_name"] == f["partner"].name
    assert last_entry["timestamp"] is not None


def test_existing_application_submit_flow_integration(client, routing_fixture, test_db):
    """Test that the existing /applications/{id}/submit endpoint transitions routing status seamlessly."""
    f = routing_fixture

    # Create application
    create_res = client.post("/applications", json={
        "scheme_id": str(f["scheme"].id),
        "channel": "online"
    }, headers=f["headers_citizen"])
    app_id = create_res.json()["id"]

    # Submit application via existing submit endpoint
    sub_res = client.post(f"/applications/{app_id}/submit", headers=f["headers_citizen"])
    assert sub_res.status_code == 200
    sub_data = sub_res.json()

    assert sub_data["status"] == "submitted"
    assert sub_data["routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert sub_data["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.PENDING.value

    # Verify via GET /applications/{id}
    app_res = client.get(f"/applications/{app_id}", headers=f["headers_citizen"])
    assert app_res.status_code == 200
    app_details = app_res.json()

    assert app_details["status"] == "submitted"
    assert app_details["current_step"] == 2
    assert app_details["routing_status"] == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
    assert app_details["partner_acknowledgement_status"] == PartnerAcknowledgementStatus.PENDING.value
    assert len(app_details["routing_history"]) >= 2
