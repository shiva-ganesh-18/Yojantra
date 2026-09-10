"""Regression tests for Part 9: Applicant Application Tracking.
Validates:
- Application status timeline
- Current status and assigned partner details
- Partner acknowledgement / review status
- Documents-required alerts and resolution flow
- Approval and rejection details with reasons
- Disbursement progress tracking
- Routing and audit history
- Clear next action determination
"""
import uuid
from decimal import Decimal
import pytest
from app.models import User, Scheme, Application, Institution, Document
from app.services.partner_routing_status_service import (
    PartnerRoutingStatus,
    PartnerAcknowledgementStatus,
    PartnerRoutingStatusService,
)
from app.core.security import create_access_token


def make_headers(user: User):
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}



@pytest.fixture
def tracking_test_data(test_db):
    """Fixture creating an applicant, partner officer, scheme, partner institution, and application."""
    # 1. Applicant user
    applicant = User(
        id=uuid.uuid4(),
        email="applicant.tracking@example.com",
        phone="+919876543210",
        full_name="Rajesh Patel",
        role="user",
        state="Gujarat",
        district="Ahmedabad",
        is_active=True
    )
    test_db.add(applicant)

    # 2. Unauthorized other user
    other_user = User(
        id=uuid.uuid4(),
        email="other.citizen@example.com",
        phone="+919876543211",
        full_name="Suresh Verma",
        role="user",
        state="Gujarat",
        district="Surat",
        is_active=True
    )
    test_db.add(other_user)

    # 3. Partner Officer
    partner_officer = User(
        id=uuid.uuid4(),
        email="officer.tracking@leadbank.in",
        phone="+919876543212",
        full_name="Officer Desai",
        role="partner_officer",
        state="Gujarat",
        district="Ahmedabad",
        is_active=True
    )
    test_db.add(partner_officer)

    # 4. Partner Institution
    institution = Institution(
        id=uuid.uuid4(),
        name="Bank of Baroda - Ahmedabad SME Hub",
        institution_type="public_sector_bank",
        code="BOB-AHM-01",
        state="Gujarat",
        district="Ahmedabad",
        status="active"
    )
    test_db.add(institution)

    # 5. Scheme
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Gujarat MSME Capital Subsidy Scheme",
        scheme_type="subsidy",
        ministry="Industries and Mines Department, Gujarat",
        description="Capital investment subsidy for small enterprises in Gujarat.",
        max_benefit_inr=Decimal("1500000.00"),
        status="active",
        documents_required=["aadhaar", "pan", "bank_passbook", "project_report"]
    )
    test_db.add(scheme)

    # 6. Initial Application in draft
    ref_code = "YOJ-2026-GUJ-778899"
    app_uuid = uuid.uuid4()
    app = Application(
        id=app_uuid,
        user_id=applicant.id,
        scheme_id=scheme.id,
        status="draft",
        current_step=1,
        total_steps=4,
        next_action="Complete checklist and submit dossier to channel partner",
        form_data={
            "partner_reference_code": ref_code,
            "requested_amount_inr": 850000.0,
            "partner_routing": {
                "scheme_category": "MSME Subsidy",
                "assigned_partner_id": str(institution.id),
                "assigned_partner_name": institution.name,
                "assigned_partner_type": "Public Sector Bank",
                "assigned_partner_location": "Ahmedabad Central",
                "distance_km": 4.2,
                "geographic_tier": "district",
                "routing_status": PartnerRoutingStatus.PARTNER_ASSIGNED.value,
                "partner_acknowledgement_status": PartnerAcknowledgementStatus.NOT_ROUTED.value
            },
            "routing_history": [
                {
                    "from_status": None,
                    "to_status": PartnerRoutingStatus.PARTNER_ASSIGNED.value,
                    "timestamp": "2026-09-08T10:00:00Z",
                    "partner_id": str(institution.id),
                    "partner_name": institution.name,
                    "reason": "Application draft initialized with assigned partner.",
                    "actor": "applicant.tracking@example.com",
                    "actor_role": "user",
                    "source": "citizen_portal"
                }
            ]
        }
    )
    test_db.add(app)
    test_db.commit()

    return {
        "applicant": applicant,
        "other_user": other_user,
        "partner_officer": partner_officer,
        "institution": institution,
        "scheme": scheme,
        "application": app,
        "ref_code": ref_code
    }


def test_applicant_tracking_timeline_and_assigned_partner(client, tracking_test_data):
    """Test applicant tracking returns full timeline, assigned partner, and next action."""
    applicant = tracking_test_data["applicant"]
    app = tracking_test_data["application"]
    inst = tracking_test_data["institution"]
    headers = make_headers(applicant)

    res = client.get(f"/applications/{app.id}/tracking", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["application_id"] == str(app.id)
    assert data["scheme_name"] == "Gujarat MSME Capital Subsidy Scheme"
    assert data["partner_reference_code"] == tracking_test_data["ref_code"]
    assert data["status"] == "draft"
    assert data["routing_status"] == PartnerRoutingStatus.PARTNER_ASSIGNED.value

    # Assigned partner verification
    assert data["assigned_partner"] is not None
    assert data["assigned_partner"]["partner_name"] == inst.name
    assert data["assigned_partner"]["distance_km"] == 4.2
    assert data["assigned_partner"]["geographic_tier"] == "district"

    # Timeline verification: 4 distinct steps
    timeline = data["timeline"]
    assert len(timeline) == 4
    step_numbers = [s["step"] for s in timeline]
    assert step_numbers == [1, 2, 3, 4]

    # Clear next action
    assert data["clear_next_action"] is not None
    assert data["clear_next_action"]["is_applicant_action_required"] is True
    assert data["clear_next_action"]["action_type"] == "SUBMIT_APPLICATION"


def test_applicant_tracking_authorization_security(client, tracking_test_data):
    """Test RBAC security: unauthorized user blocked; owner and officer permitted."""
    app = tracking_test_data["application"]
    other_user = tracking_test_data["other_user"]
    officer = tracking_test_data["partner_officer"]

    # Other citizen blocked
    other_headers = make_headers(other_user)
    res_other = client.get(f"/applications/{app.id}/tracking", headers=other_headers)
    assert res_other.status_code in [403, 404]

    # Officer permitted
    officer_headers = make_headers(officer)
    res_officer = client.get(f"/applications/{app.id}/tracking", headers=officer_headers)
    assert res_officer.status_code == 200
    assert res_officer.json()["application_id"] == str(app.id)


def test_documents_required_alert_and_resolution(client, test_db, tracking_test_data):
    """Test DOCUMENTS_REQUIRED alert generation and applicant resolution flow."""
    applicant = tracking_test_data["applicant"]
    officer = tracking_test_data["partner_officer"]
    app = tracking_test_data["application"]
    headers = make_headers(applicant)
    officer_headers = make_headers(officer)

    # First transition through state machine: PARTNER_ASSIGNED -> ROUTED_TO_PARTNER -> PARTNER_RECEIVED -> DOCUMENTS_REQUIRED
    status_service = PartnerRoutingStatusService(test_db)
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        reason="Dossier submitted and transmitted to partner",
        actor=applicant,
        source="citizen_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.PARTNER_RECEIVED.value,
        reason="Official receipt acknowledged by Bank Desk",
        actor=officer,
        source="partner_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.DOCUMENTS_REQUIRED.value,
        reason="Please submit audited DPR and balance sheet for FY 2024-25",
        actor=officer,
        source="partner_portal"
    )

    # Check applicant tracking view
    res = client.get(f"/applications/{app.id}/tracking", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["routing_status"] == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value
    assert data["documents_required_alert"] is not None
    assert data["documents_required_alert"]["is_active"] is True
    assert "audited DPR and balance sheet" in data["documents_required_alert"]["reason"]
    assert data["clear_next_action"]["action_type"] == "UPLOAD_DOCS"
    assert data["clear_next_action"]["is_applicant_action_required"] is True

    # Check timeline step 3 indicates action required / failed state
    step3 = next(s for s in data["timeline"] if s["step"] == 3)
    assert step3["status"] == "failed"
    assert "Compliance query raised" in step3["note"]

    # Applicant resolves document request
    resolve_res = client.post(
        f"/applications/{app.id}/resolve-document-request",
        json={"comments": "Audited project report and FY25 financials uploaded to document vault."},
        headers=headers
    )
    assert resolve_res.status_code == 200
    resolved_data = resolve_res.json()

    assert resolved_data["routing_status"] == PartnerRoutingStatus.UNDER_REVIEW.value
    assert resolved_data["documents_required_alert"] is None
    assert resolved_data["clear_next_action"]["action_type"] == "AWAIT_REVIEW"
    assert resolved_data["clear_next_action"]["is_applicant_action_required"] is False

    # Check audit trail recorded resolution
    history = resolved_data["routing_history"]
    latest_event = history[-1]
    assert latest_event["from_status"] == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value
    assert latest_event["to_status"] == PartnerRoutingStatus.UNDER_REVIEW.value
    assert "Audited project report" in latest_event["reason"]


def test_approval_details_and_disbursement_progress(client, test_db, tracking_test_data):
    """Test approval details and DBT disbursement progress lifecycle."""
    applicant = tracking_test_data["applicant"]
    officer = tracking_test_data["partner_officer"]
    app = tracking_test_data["application"]
    headers = make_headers(applicant)

    # Transition through state machine to APPROVED
    status_service = PartnerRoutingStatusService(test_db)
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        reason="Dossier submitted",
        actor=applicant,
        source="citizen_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.PARTNER_RECEIVED.value,
        reason="Docket received by partner desk",
        actor=officer,
        source="partner_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.UNDER_REVIEW.value,
        reason="Scrutiny underway",
        actor=officer,
        source="partner_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.APPROVED.value,
        reason="Sanction approved by District MSME Level Committee with 15% capital subsidy",
        actor=officer,
        source="partner_portal"
    )

    app_res = client.get(f"/applications/{app.id}/tracking", headers=headers)
    assert app_res.status_code == 200
    app_data = app_res.json()

    assert app_data["routing_status"] == PartnerRoutingStatus.APPROVED.value
    assert app_data["approval_details"] is not None
    assert app_data["approval_details"]["is_approved"] is True
    assert "District MSME Level Committee" in app_data["approval_details"]["reason_or_remarks"]
    assert "SANC-" in app_data["approval_details"]["sanction_reference"]
    assert app_data["disbursement_progress"]["status"] == "NOT_STARTED"

    # Transition to DISBURSEMENT_PROCESSING
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value,
        reason="Payment batch dispatched to PFMS Aadhaar bridge",
        actor=officer,
        source="partner_portal"
    )

    proc_res = client.get(f"/applications/{app.id}/tracking", headers=headers)
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["routing_status"] == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value
    assert proc_data["disbursement_progress"]["status"] == "PROCESSING"

    # Transition to DISBURSED
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.DISBURSED.value,
        reason="DBT credit confirmed to Aadhaar linked savings account",
        actor=officer,
        source="partner_portal"
    )

    disb_res = client.get(f"/applications/{app.id}/tracking", headers=headers)
    assert disb_res.status_code == 200
    disb_data = disb_res.json()

    assert disb_data["routing_status"] == PartnerRoutingStatus.DISBURSED.value
    assert disb_data["disbursement_progress"]["status"] == "DISBURSED"
    assert "PFMS-DBT-" in disb_data["disbursement_progress"]["reference_number"]
    assert disb_data["clear_next_action"]["action_type"] == "COMPLETED"

    # Step 4 in timeline completed
    step4 = next(s for s in disb_data["timeline"] if s["step"] == 4)
    assert step4["status"] == "completed"


def test_rejection_details_and_reason(client, test_db, tracking_test_data):
    """Test rejection details with reason and alternative recommendation callout."""
    applicant = tracking_test_data["applicant"]
    officer = tracking_test_data["partner_officer"]
    app = tracking_test_data["application"]
    headers = make_headers(applicant)

    # Transition through state machine to REJECTED
    status_service = PartnerRoutingStatusService(test_db)
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        reason="Dossier submitted",
        actor=applicant,
        source="citizen_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.PARTNER_RECEIVED.value,
        reason="Receipt acknowledged",
        actor=officer,
        source="partner_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.UNDER_REVIEW.value,
        reason="Scrutiny underway",
        actor=officer,
        source="partner_portal"
    )
    status_service.transition_routing_status(
        application=app,
        to_status=PartnerRoutingStatus.REJECTED.value,
        reason="Ineligible sector: Real estate and speculative trading are excluded from manufacturing subsidy.",
        actor=officer,
        source="partner_portal"
    )

    res = client.get(f"/applications/{app.id}/tracking", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["routing_status"] == PartnerRoutingStatus.REJECTED.value
    assert data["rejection_details"] is not None
    assert data["rejection_details"]["is_rejected"] is True
    assert "Real estate and speculative trading are excluded" in data["rejection_details"]["reason"]
    assert data["rejection_details"]["can_reapply"] is True

    # Next action directs applicant to check alternatives
    assert data["clear_next_action"]["action_type"] == "REVIEW_REJECTION"
    assert data["clear_next_action"]["action_url"] == "/matches"
