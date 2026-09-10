"""
Part 15 Regression Tests:
1. Document Readiness Truthfulness:
   - Document type normalization across aliases
   - Score capping at <= 65% when mandatory documents are missing
   - Distinction between General Enterprise vs Scheme-Specific mandatory documents
   - Elimination of false "all mandatory documents uploaded" messages
2. Scheme-Specific Checklist Calculation:
   - Accurate completed_items / total_items computation
   - True Uploaded vs Missing status (documents do not falsely complete other items)
   - Official scheme portal link strictly sourced from scheme.official_url
3. Profile Completion & Geographic Integrity:
   - Active mobile number required (profile capped at <= 70% without phone)
   - State to district validation (rejecting Patna, Tamil Nadu with HTTP 400)
   - Legacy inconsistent district scrubbing
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models import User, Business, Scheme, Application, Document
from app.core.security import create_access_token
from app.services.document_service import normalize_document_type, DocumentService
from app.routers.locations import is_valid_district_for_state, validate_state_and_district
from app.routers.users import calculate_profile_completion, build_user_response


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
def test_user(db_session):
    unique = uuid4().hex[:8]
    user = User(
        id=uuid4(),
        email=f"doc_test_{unique}@example.com",
        full_name="Ananya Raman",
        phone=f"+9198{uuid4().int % 100000000:08d}",
        state="Tamil Nadu",
        district="Chennai",
        role="citizen",
        social_category="OBC",
        date_of_birth="1992-05-15",
        gender="female",
        onboarding_completed=True
    )
    user.udyam_number = f"UDYAM-TN-02-{uuid4().int % 1000000:06d}"
    db_session.add(user)

    business = Business(
        id=uuid4(),
        user_id=user.id,
        business_name="Raman Agri Bio",
        business_type="Micro",
        sector="Agriculture",
        annual_turnover_inr=1500000
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"user": user, "business": business, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def sample_scheme(db_session):
    scheme = db_session.query(Scheme).filter(Scheme.status == "active").first()
    assert scheme is not None, "At least one active scheme must exist"
    return scheme


# =========================================================================
# 1. Document Type Normalization Tests
# =========================================================================

def test_normalize_document_type():
    """Verify alias mapping to canonical document keys."""
    assert normalize_document_type("PAN Card") == "pan"
    assert normalize_document_type("pan_card") == "pan"
    assert normalize_document_type("Business PAN") == "business_pan"
    assert normalize_document_type("Aadhaar Card") == "aadhaar"
    assert normalize_document_type("UDYAM Registration Certificate") == "udyam"
    assert normalize_document_type("Detailed Project Report (DPR)") == "project_report"
    assert normalize_document_type("Project Report") == "project_report"
    assert normalize_document_type("Bank Passbook / Account Details") == "bank_passbook"
    assert normalize_document_type("Bank Statement (6 Months)") == "bank_statement"
    assert normalize_document_type("Caste / Community Certificate") == "caste_certificate"
    assert normalize_document_type("Passport Photograph") == "photo"
    assert normalize_document_type("GST Registration Certificate") == "gst"
    assert normalize_document_type("FSSAI License / Registration") == "fssai_license"


# =========================================================================
# 2. Document Readiness Truthfulness Tests
# =========================================================================

def test_readiness_score_capped_when_mandatory_missing(db_session, test_user):
    """When mandatory documents are missing, readiness score must be capped at <= 65% and not ready."""
    doc_service = DocumentService(db_session)
    user = test_user["user"]

    # User has 0 uploaded documents
    readiness = doc_service.calculate_readiness_score(user.id)
    assert readiness["is_ready_to_apply"] is False
    assert readiness["readiness_score"] <= 65
    assert readiness["missing_mandatory_count"] > 0
    assert "missing" in readiness["summary"].lower()
    assert "all mandatory" not in readiness["summary"].lower()

    # User uploads ONLY an optional/general document (e.g. photo)
    doc = Document(
        id=uuid4(),
        user_id=user.id,
        doc_type="photo",
        file_url="/mock/photo.jpg",
        verification_status="verified"
    )
    db_session.add(doc)
    db_session.commit()

    readiness = doc_service.calculate_readiness_score(user.id)
    assert readiness["is_ready_to_apply"] is False
    assert readiness["readiness_score"] <= 65
    assert readiness["missing_mandatory_count"] > 0
    # Summary must explicitly list missing mandatory items
    assert len(readiness["missing_mandatory_docs"]) > 0


def test_readiness_score_complete_when_mandatory_uploaded(db_session, test_user):
    """When mandatory documents (Aadhaar, PAN, Bank Passbook) are uploaded, user is ready."""
    user = test_user["user"]

    for doc_type in ["aadhaar", "pan", "bank_passbook"]:
        d = Document(
            id=uuid4(),
            user_id=user.id,
            doc_type=doc_type,
            file_url=f"/mock/{doc_type}.pdf",
            verification_status="verified"
        )
        db_session.add(d)
    db_session.commit()

    doc_service = DocumentService(db_session)
    readiness = doc_service.calculate_readiness_score(user.id)
    assert readiness["is_ready_to_apply"] is True
    assert readiness["missing_mandatory_count"] == 0
    assert readiness["readiness_score"] >= 75


# =========================================================================
# 3. Profile Completion & State/District Validation Tests
# =========================================================================

def test_profile_completion_capped_without_phone(db_session, test_user):
    """Profile completion cannot reach 100% and is capped at <= 70% if phone is missing."""
    user = test_user["user"]
    business = test_user["business"]

    user.phone = None
    score = calculate_profile_completion(user, business)
    assert score <= 70

    user.phone = ""
    score = calculate_profile_completion(user, business)
    assert score <= 70

    user.phone = "+919876543210"
    score = calculate_profile_completion(user, business)
    assert score == 100


def test_state_and_district_validation_logic():
    """Verify state-district relationship validator."""
    assert is_valid_district_for_state("Tamil Nadu", "Chennai") is True
    assert is_valid_district_for_state("Tamil Nadu", "Coimbatore") is True
    assert is_valid_district_for_state("Tamil Nadu", "Patna") is False
    assert is_valid_district_for_state("Bihar", "Patna") is True
    assert is_valid_district_for_state("Telangana", "Hyderabad") is True
    assert is_valid_district_for_state("Telangana", "Chennai") is False


def test_user_update_rejects_patna_in_tamil_nadu(client, test_user):
    """PUT /users/me with mismatched district and state must fail with HTTP 400."""
    response = client.put(
        "/users/me",
        headers=test_user["headers"],
        json={
            "state": "Tamil Nadu",
            "district": "Patna"
        }
    )
    assert response.status_code == 400
    assert "Patna" in response.json()["detail"] and "Tamil Nadu" in response.json()["detail"]


def test_user_update_accepts_valid_location(client, test_user):
    """PUT /users/me with valid district and state succeeds."""
    response = client.put(
        "/users/me",
        headers=test_user["headers"],
        json={
            "state": "Tamil Nadu",
            "district": "Coimbatore"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "Tamil Nadu"
    assert data["district"] == "Coimbatore"


def test_legacy_inconsistent_district_scrubbed_in_response(db_session, test_user):
    """If DB has Patna in Tamil Nadu, build_user_response clears the inconsistent district."""
    user = test_user["user"]
    user.state = "Tamil Nadu"
    user.district = "Patna"
    db_session.commit()

    resp = build_user_response(user, db_session)
    assert resp.state == "Tamil Nadu"
    assert resp.district == ""  # Scrubbed to prevent "Patna, Tamil Nadu"
    assert resp.profile_completion_percentage <= 85


# =========================================================================
# 4. Scheme Checklist Accuracy Tests
# =========================================================================

def test_scheme_checklist_accurate_counts_and_matching(client, db_session, test_user, sample_scheme):
    """
    Verify /applications/{id}/checklist computes actual items accurately.
    Missing documents remain missing.
    Uploading PAN does NOT mark DPR completed.
    """
    user = test_user["user"]

    # Create application for sample_scheme
    app_record = Application(
        id=uuid4(),
        user_id=user.id,
        scheme_id=sample_scheme.id,
        status="draft",
        channel="online",
        form_data={"requested_amount_inr": 500000}
    )
    db_session.add(app_record)
    db_session.commit()

    # 1. Fetch checklist with no uploaded documents
    res = client.get(f"/applications/{app_record.id}/checklist", headers=test_user["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["total_items"] > 0
    # Profile check and enterprise check may be completed depending on user/biz
    assert data["completed_items"] <= 2
    assert data["completion_percentage"] < 60
    # Official URL must match scheme.official_url
    assert data["official_portal_url"] == sample_scheme.official_url

    # Check document items: all should be is_completed=False
    doc_items = [it for it in data["items"] if it["id"].startswith("doc_")]
    assert len(doc_items) > 0
    for doc_item in doc_items:
        assert doc_item["is_completed"] is False, f"{doc_item['title']} must be uncompleted"

    # 2. Upload only PAN Card
    pan_doc = Document(
        id=uuid4(),
        user_id=user.id,
        doc_type="pan",
        file_url="/mock/pan.pdf",
        verification_status="verified"
    )
    db_session.add(pan_doc)
    db_session.commit()

    res2 = client.get(f"/applications/{app_record.id}/checklist", headers=test_user["headers"])
    assert res2.status_code == 200
    data2 = res2.json()

    # PAN should now be completed if required, but other docs (like DPR / Bank Statement) must NOT be completed
    for item in data2["items"]:
        if "pan" in item["id"].lower():
            assert item["is_completed"] is True
        elif any(k in item["id"].lower() for k in ["project_report", "caste_certificate", "bank_statement", "aadhaar"]):
            # Must remain false because only PAN was uploaded
            assert item["is_completed"] is False, f"{item['title']} should remain uncompleted!"

    # Completed items should increase by exactly 1 if scheme requires PAN
    pan_required = any("pan" in it["id"].lower() for it in data["items"])
    if pan_required:
        assert data2["completed_items"] == data["completed_items"] + 1
