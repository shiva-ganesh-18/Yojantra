"""Tests for Applications lifecycle and Document management."""
import pytest
import io
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models import User, Scheme, Application, Document


@pytest.fixture
def users_and_scheme(test_db):
    user_a = User(id=uuid.uuid4(), phone="+919876500010", full_name="User A", is_active=True)
    user_b = User(id=uuid.uuid4(), phone="+919876500020", full_name="User B", is_active=True)
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Test Subsidy Scheme",
        ministry="Ministry of MSME",
        description="Subsidy for micro units",
        max_benefit_inr=Decimal("500000"),
        status="active"
    )
    test_db.add_all([user_a, user_b, scheme])
    test_db.commit()

    token_a = create_access_token(data={"sub": str(user_a.id), "role": "user"})
    token_b = create_access_token(data={"sub": str(user_b.id), "role": "user"})

    return {
        "user_a": user_a,
        "user_b": user_b,
        "scheme": scheme,
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"}
    }


def test_application_lifecycle_and_ownership(client, users_and_scheme):
    data = users_and_scheme
    # 1. User A creates application
    create_payload = {
        "scheme_id": str(data["scheme"].id),
        "requested_amount_inr": 250000.0,
        "application_data": {"purpose": "Equipment purchase"}
    }
    res = client.post("/applications", json=create_payload, headers=data["headers_a"])
    assert res.status_code == 200
    app_id = res.json()["id"]
    assert res.json()["status"] == "draft"

    # 2. User A lists applications: sees application
    list_res_a = client.get("/applications", headers=data["headers_a"])
    assert list_res_a.status_code == 200
    assert len(list_res_a.json()) == 1
    assert list_res_a.json()[0]["id"] == app_id

    # 3. Ownership security: User B cannot access User A's application
    get_res_b = client.get(f"/applications/{app_id}", headers=data["headers_b"])
    assert get_res_b.status_code in (403, 404)

    # 4. User B lists applications: sees 0 applications
    list_res_b = client.get("/applications", headers=data["headers_b"])
    assert list_res_b.status_code == 200
    assert len(list_res_b.json()) == 0

    # 5. User A submits application
    submit_res = client.post(f"/applications/{app_id}/submit", headers=data["headers_a"])
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "submitted"


def test_document_upload_and_validation(client, users_and_scheme):
    data = users_and_scheme

    # Test invalid document type
    dummy_file = ("test.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")
    res_bad_type = client.post(
        "/documents/upload",
        data={"doc_type": "invalid_type"},
        files={"file": dummy_file},
        headers=data["headers_a"]
    )
    assert res_bad_type.status_code == 400

    # Test empty file rejection
    empty_file = ("empty.pdf", io.BytesIO(b""), "application/pdf")
    res_empty = client.post(
        "/documents/upload",
        data={"doc_type": "pan"},
        files={"file": empty_file},
        headers=data["headers_a"]
    )
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["detail"].lower()

    # Test valid document upload
    valid_file = ("pan_card.png", io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."), "image/png")
    res_valid = client.post(
        "/documents/upload",
        data={"doc_type": "pan"},
        files={"file": valid_file},
        headers=data["headers_a"]
    )
    assert res_valid.status_code == 200
    doc_id = res_valid.json()["id"]
    assert res_valid.json()["verification_status"] == "pending"

    # Test verify document
    res_verify = client.post(f"/documents/{doc_id}/verify", headers=data["headers_a"])
    assert res_verify.status_code == 200
    assert res_verify.json()["verification_status"] == "verified"
    assert "heuristic ocr" in res_verify.json()["verification_tier"].lower()


def test_document_readiness_and_checklist(client, users_and_scheme):
    data = users_and_scheme
    
    # 1. Initial readiness score for user B (no documents uploaded)
    res_init = client.get("/documents/readiness", headers=data["headers_b"])
    assert res_init.status_code == 200
    init_data = res_init.json()
    assert init_data["readiness_score"] == 0
    assert init_data["is_ready_to_apply"] is False
    assert len(init_data["checklist"]) > 0
    assert init_data["total_uploaded"] == 0

    # 2. Upload Aadhaar for User B
    aadhaar_file = ("aadhaar.png", io.BytesIO(b"\x89PNG\r\nAadhaar Card 9876 5432 4821 Sample"), "image/png")
    res_aadhaar = client.post(
        "/documents/upload",
        data={"doc_type": "aadhaar"},
        files={"file": aadhaar_file},
        headers=data["headers_b"]
    )
    assert res_aadhaar.status_code == 200
    aadhaar_data = res_aadhaar.json()
    assert aadhaar_data["extracted_fields"]["doc_number_masked"] == "XXXX-XXXX-4821"

    # 3. Upload duplicate Aadhaar file -> duplicate warning check
    aadhaar_dup_file = ("aadhaar_dup.png", io.BytesIO(b"\x89PNG\r\nAadhaar Card 9876 5432 4821 Sample"), "image/png")
    res_dup = client.post(
        "/documents/upload",
        data={"doc_type": "aadhaar"},
        files={"file": aadhaar_dup_file},
        headers=data["headers_b"]
    )
    assert res_dup.status_code == 200
    assert res_dup.json()["duplicate_warning"] is not None

    # 4. Upload PAN and Bank Passbook for User B
    pan_file = ("pan.png", io.BytesIO(b"\x89PNG\r\nPAN ABCDE8911C"), "image/png")
    client.post("/documents/upload", data={"doc_type": "pan"}, files={"file": pan_file}, headers=data["headers_b"])

    passbook_file = ("passbook.png", io.BytesIO(b"\x89PNG\r\nBank Passbook SBIN0001234"), "image/png")
    client.post("/documents/upload", data={"doc_type": "bank_passbook"}, files={"file": passbook_file}, headers=data["headers_b"])

    # 5. Check readiness score again (should now have high readiness score >= 70%)
    res_ready = client.get("/documents/readiness", headers=data["headers_b"])
    assert res_ready.status_code == 200
    ready_data = res_ready.json()
    assert ready_data["readiness_score"] >= 70
    assert ready_data["is_ready_to_apply"] is True
    assert ready_data["missing_mandatory_count"] == 0

    # 6. Test Profile Auto-Fill from extracted documents
    res_autofill = client.post("/documents/auto-fill", headers=data["headers_b"])
    assert res_autofill.status_code == 200
    autofill_data = res_autofill.json()
    assert autofill_data["success"] is True
    assert len(autofill_data["updated_fields"]) > 0
    assert autofill_data["user_profile"]["gender"] is not None


def test_enhanced_application_validation_and_checklists(client, users_and_scheme):
    data = users_and_scheme
    scheme = data["scheme"]
    
    # 1. Create application
    res_create = client.post(
        "/applications",
        json={"scheme_id": str(scheme.id), "requested_amount_inr": 400000.0},
        headers=data["headers_a"]
    )
    assert res_create.status_code == 200
    app_data = res_create.json()
    app_id = app_data["id"]
    assert "YOJ-" in app_data["partner_reference_code"]
    assert len(app_data["timeline"]) == 4

    # 2. Check Pre-submission validation endpoint
    res_validate = client.get(f"/applications/{app_id}/validate", headers=data["headers_a"])
    assert res_validate.status_code == 200
    val_data = res_validate.json()
    assert "is_ready_to_submit" in val_data
    assert "readiness_score" in val_data
    assert len(val_data["checks"]) >= 3
    assert val_data["partner_reference_code"] == app_data["partner_reference_code"]
    assert "disclaimer" in val_data

    # 3. Check Scheme-specific application checklist endpoint
    res_checklist = client.get(f"/applications/{app_id}/checklist", headers=data["headers_a"])
    assert res_checklist.status_code == 200
    chk_data = res_checklist.json()
    assert chk_data["total_items"] >= 2
    assert "completion_percentage" in chk_data
    assert chk_data["scheme_name"] == scheme.name


def test_application_checklist_handles_dict_and_str_documents(client, test_db):
    """Ensure get_application_checklist does not crash with AttributeError if documents_required contains dicts."""
    user = User(id=uuid.uuid4(), phone="+919876588888", full_name="Checklist User", is_active=True)
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Complex Document Scheme",
        ministry="Ministry of MSME",
        description="Scheme with diverse required document structure formats.",
        documents_required=[
            {"name": "aadhaar", "type": "identity"},
            {"name": "udyam_registration", "type": "registration"},
            "pan"
        ],
        status="active"
    )
    test_db.add_all([user, scheme])
    test_db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    res_create = client.post("/applications", json={"scheme_id": str(scheme.id)}, headers=headers)
    assert res_create.status_code == 200
    app_id = res_create.json()["id"]

    res_chk = client.get(f"/applications/{app_id}/checklist", headers=headers)
    assert res_chk.status_code == 200
    chk_data = res_chk.json()
    assert chk_data["total_items"] >= 3


def test_income_certificate_upload_json_serialization(client, users_and_scheme):
    """Regression test: Income certificate OCR extraction with Decimal amounts must serialize to JSON safely."""
    data = users_and_scheme
    income_file = (
        "Income_certificate.png",
        io.BytesIO(b"\x89PNG\r\nINCOME CERTIFICATE Annual Income Rs. 180000 Tahsildar Office"),
        "image/png"
    )
    res = client.post(
        "/documents/upload",
        data={"doc_type": "income_certificate"},
        files={"file": income_file},
        headers=data["headers_a"]
    )
    assert res.status_code == 200
    doc_data = res.json()
    assert doc_data["doc_type"] == "income_certificate"
    extracted = doc_data.get("extracted_fields") or {}
    assert "income_annual_inr" in extracted
    assert isinstance(extracted["income_annual_inr"], (int, float))
    assert extracted["income_annual_inr"] == 180000


def test_application_checklist_acronym_and_clean_title_preservation(client, test_db):
    """Regression test: Government acronyms like (TA), (IA), (DSR), and PAN must not be lowercased to (Ta), (Ia), (Dsr)."""
    user = User(id=uuid.uuid4(), phone="+919876577777", full_name="Acronym User", is_active=True)
    scheme = Scheme(
        id=uuid.uuid4(),
        name="SFURTI Traditional Scheme",
        ministry="Ministry of MSME",
        description="Scheme for Funds Regeneration of Traditional Industries",
        documents_required=[
            {"name": "Technical Agency (TA) Consent", "mandatory": True},
            {"name": "Implementing Agency (IA) Registration Details", "mandatory": True},
            {"name": "Cluster Diagnostic Study Report (DSR)", "mandatory": True},
            {"name": "pan", "mandatory": True}
        ],
        status="active"
    )
    test_db.add_all([user, scheme])
    test_db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    res_create = client.post("/applications", json={"scheme_id": str(scheme.id)}, headers=headers)
    assert res_create.status_code == 200
    app_id = res_create.json()["id"]

    res_chk = client.get(f"/applications/{app_id}/checklist", headers=headers)
    assert res_chk.status_code == 200
    items = res_chk.json()["items"]
    titles = [it["title"] for it in items]

    # Verify acronyms are preserved
    assert any("(TA)" in t for t in titles), f"(TA) not found in {titles}"
    assert any("(IA)" in t for t in titles), f"(IA) not found in {titles}"
    assert any("(DSR)" in t for t in titles), f"(DSR) not found in {titles}"
    assert any("PAN Card" in t for t in titles), f"PAN Card not found in {titles}"
    # Verify no redundant "(Ta) Consent Copy"
    assert not any("(Ta)" in t for t in titles)
    assert not any("(Ia)" in t for t in titles)


def test_csc_by_district_optional_state(client, test_db):
    """Regression test: CSC lookup by district works even if state is not specified."""
    res = client.get("/csc/by-district", params={"district": "Coimbatore"})
    assert res.status_code == 200
    data = res.json()
    assert "centers" in data




