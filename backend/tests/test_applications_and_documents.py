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
    assert get_res_b.status_code == 404

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
