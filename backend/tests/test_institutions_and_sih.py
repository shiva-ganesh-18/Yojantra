"""Tests for All-India Locations and Partner Institutions discovery workflows."""
import pytest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models import User, Institution, Document, Notification
from app.core.security import create_access_token


@pytest.fixture
def auth_users(test_db):
    user_a = User(
        id=uuid.uuid4(),
        phone="+919811111111",
        email="usera@example.com",
        full_name="Aarav Mehta",
        role="user",
        state="Maharashtra",
        district="Pune"
    )
    user_b = User(
        id=uuid.uuid4(),
        phone="+919822222222",
        email="userb@example.com",
        full_name="Bhavna Nair",
        role="user",
        state="Karnataka",
        district="Bengaluru Urban"
    )
    admin_user = User(
        id=uuid.uuid4(),
        phone="+919833333333",
        email="admin@yojantra.in",
        full_name="Chief Admin",
        role="admin",
        state="Delhi",
        district="New Delhi"
    )
    test_db.add_all([user_a, user_b, admin_user])
    test_db.commit()

    token_a = create_access_token({"sub": str(user_a.id), "phone": user_a.phone, "role": user_a.role})
    token_b = create_access_token({"sub": str(user_b.id), "phone": user_b.phone, "role": user_b.role})
    token_admin = create_access_token({"sub": str(admin_user.id), "phone": admin_user.phone, "role": admin_user.role})

    return {
        "user_a": user_a,
        "user_b": user_b,
        "admin": admin_user,
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "headers_admin": {"Authorization": f"Bearer {token_admin}"},
    }


@pytest.fixture
def sample_institution(test_db):
    inst = Institution(
        id=uuid.uuid4(),
        name="State Channelizing Agency Pune",
        short_name="SCA Pune",
        code="SCA-41523",
        institution_type="State Channelizing Agency",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        status="active"
    )
    test_db.add(inst)
    test_db.commit()
    return inst


def test_locations_states_and_districts(client):
    # 1. Test states endpoint
    res_states = client.get("/locations/states")
    assert res_states.status_code == 200
    states = res_states.json()
    assert len(states) == 36
    state_names = [s["name"] for s in states]
    assert "Maharashtra" in state_names
    assert "Delhi" in state_names
    assert "Tamil Nadu" in state_names

    # 2. Test districts endpoint
    res_districts = client.get("/locations/districts?state=Maharashtra")
    assert res_districts.status_code == 200
    districts = res_districts.json()
    assert len(districts) > 0
    assert any(d["name"] == "Pune" for d in districts)

    # 3. Test invalid state
    res_invalid = client.get("/locations/districts?state=NonExistentStateXYZ")
    assert res_invalid.status_code == 404


def test_institutions_list_and_filter(client, sample_institution):
    # List all
    res = client.get("/institutions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1

    # Filter by state
    res_state = client.get("/institutions?state=Maharashtra")
    assert res_state.status_code == 200
    assert any(i["name"] == "State Channelizing Agency Pune" for i in res_state.json())

    # Search by keyword
    res_search = client.get("/institutions?q=SCA Pune")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1
    assert res_search.json()[0]["code"] == "SCA-41523"

    # Detail
    res_detail = client.get(f"/institutions/{sample_institution.id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["name"] == "State Channelizing Agency Pune"

    # Partner recommendations with scheme eligibility and proximity
    res_recs = client.get("/institutions/recommendations?state=Maharashtra&district=Pune&lat=18.52&lng=73.85")
    assert res_recs.status_code == 200
    recs_data = res_recs.json()
    assert recs_data["total_partners_found"] >= 1
    assert recs_data["best_partner"] is not None
    assert recs_data["best_partner_reason"] is not None
    assert "best recommended partner" in recs_data["best_partner_reason"].lower()


def test_institution_request_addition(client):
    payload = {
        "name": "State Tribal Development Facilitation Center",
        "state": "Maharashtra",
        "district": "Nanded",
        "city": "Nanded",
        "requested_by_email": "citizen@example.com"
    }
    res = client.post("/institutions/request", json=payload)
    assert res.status_code == 201
    assert res.json()["name"] == payload["name"]
    assert res.json()["status"] == "pending"



def test_schemes_authorization_protection(client, auth_users):
    scheme_data = {
        "name": "Rogue Non-Admin Scheme",
        "ministry": "Fake Dept",
        "description": "Unauthorized submission",
        "is_national": True
    }

    # 1. Unauthenticated -> 401
    res_unauth = client.post("/schemes", json=scheme_data)
    assert res_unauth.status_code == 401

    # 2. Normal Beneficiary User -> 403 Forbidden
    res_user = client.post("/schemes", json=scheme_data, headers=auth_users["headers_a"])
    assert res_user.status_code == 403

    # 3. Admin User -> 200 OK
    res_admin = client.post("/schemes", json=scheme_data, headers=auth_users["headers_admin"])
    assert res_admin.status_code == 200
    created_id = res_admin.json()["id"]

    # 4. Normal user tries to delete -> 403 Forbidden
    res_del_user = client.delete(f"/schemes/{created_id}", headers=auth_users["headers_a"])
    assert res_del_user.status_code == 403

    # 5. Admin deletes -> 200 OK
    res_del_admin = client.delete(f"/schemes/{created_id}", headers=auth_users["headers_admin"])
    assert res_del_admin.status_code == 200


def test_document_and_notification_ownership_security(test_db, client, auth_users):
    user_a = auth_users["user_a"]
    user_b = auth_users["user_b"]

    # Document belonging to User A
    doc_a = Document(
        id=uuid.uuid4(),
        user_id=user_a.id,
        doc_type="pan",
        file_url="/tmp/pan_a.pdf",
        verification_status="pending"
    )
    notif_a = Notification(
        id=uuid.uuid4(),
        user_id=user_a.id,
        type="system",
        title="Welcome to Yojantra",
        body="Your account is active."
    )
    test_db.add_all([doc_a, notif_a])
    test_db.commit()

    # User B tries to verify User A's document -> 403 Forbidden
    res_verify_b = client.post(f"/documents/{doc_a.id}/verify", headers=auth_users["headers_b"])
    assert res_verify_b.status_code == 403

    # User B tries to mark User A's notification as read -> 404 (ownership check returns not found for user B)
    res_notif_b = client.put(f"/notifications/{notif_a.id}/read", headers=auth_users["headers_b"])
    assert res_notif_b.status_code == 404

    # User A marks their own notification -> 200 OK
    res_notif_a = client.put(f"/notifications/{notif_a.id}/read", headers=auth_users["headers_a"])
    assert res_notif_a.status_code == 200
