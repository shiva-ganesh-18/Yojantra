"""End-to-End User Journey Test for SchemeMatch AI Phase 1.

Verifies the complete flow:
LOGIN -> OTP -> ONBOARDING -> DASHBOARD -> SCHEMES -> MATCHES ->
DOCUMENT UPLOAD -> OCR -> APPLICATION CREATION -> SUBMISSION ->
TRACKING -> CHAT -> CSC -> NOTIFICATIONS.
"""
import io
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from app.models import Scheme, EligibilityRule, Benefit, CSCCenter, Notification, OTPVerification
from app.core.security import hash_otp


def test_full_phase1_e2e_user_journey(test_db, client):
    # Setup test data in DB
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Pradhan Mantri Mudra Yojana (PMMY)",
        ministry="Ministry of Finance",
        description="Micro-enterprise loans up to 10 lakhs",
        scheme_type="credit_guarantee",
        max_benefit_inr=1000000.0,
        status="active"
    )
    test_db.add(scheme)

    rule = EligibilityRule(
        scheme_id=scheme.id,
        field_name="max_investment",
        operator="<=",
        rule_value=1000000.0,
        is_mandatory=True,
        description="Investment up to Rs. 10 Lakhs"
    )
    test_db.add(rule)

    csc = CSCCenter(
        id=uuid.uuid4(),
        csc_id="CSC-PUN-001",
        name="CSC Common Services Centre - Central",
        state="Maharashtra",
        district="Pune",
        pincode="411001",
        latitude=18.5204,
        longitude=73.8567,
        phone="+919876500001",
        services_offered=["Aadhaar", "Scheme Applications", "PAN Card"]
    )
    test_db.add(csc)
    test_db.commit()

    # =========================================================================
    # 1. LOGIN VIA GOOGLE AUTH (FIREBASE ID TOKEN)
    # =========================================================================
    from unittest.mock import patch
    mock_payload = {
        "uid": "firebase_uid_e2e_journey",
        "email": "priya.sharma@example.com",
        "email_verified": True,
        "name": "Priya Sharma",
        "picture": "https://example.com/priya.jpg",
    }
    with patch("app.routers.auth.verify_firebase_token", return_value=mock_payload):
        login_res = client.post("/auth/google", json={"id_token": "mock-e2e-google-id-token"})
        assert login_res.status_code == 200
        auth_data = login_res.json()
        token = auth_data["access_token"]
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}

    # =========================================================================
    # 2. ONBOARDING & PROFILE SETUP
    # =========================================================================
    update_profile_res = client.put(
        "/users/me",
        json={
            "full_name": "Priya Sharma",
            "gender": "female",
            "social_category": "OBC",
            "state": "Maharashtra",
            "district": "Pune",
            "is_rural": False,
            "preferred_language": "hi",
            "onboarding_completed": True
        },
        headers=headers
    )
    assert update_profile_res.status_code == 200
    assert update_profile_res.json()["full_name"] == "Priya Sharma"
    assert update_profile_res.json()["onboarding_completed"] is True

    # Register Business
    business_res = client.post(
        "/users/me/business",
        json={
            "business_name": "Priya Food Crafts & Spices",
            "entity_type": "proprietorship",
            "sector": "Food Processing",
            "enterprise_type": "micro",
            "annual_turnover_inr": 850000.0,
            "investment_plant_machinery_inr": 450000.0,
            "women_ownership_percentage": 100.0,
            "number_of_employees": 4
        },
        headers=headers
    )
    assert business_res.status_code == 200
    assert business_res.json()["business_name"] == "Priya Food Crafts & Spices"

    # =========================================================================
    # 3. DASHBOARD & SCHEMES LIST
    # =========================================================================
    schemes_res = client.get("/schemes", headers=headers)
    assert schemes_res.status_code == 200
    schemes_list = schemes_res.json()
    assert len(schemes_list) >= 1

    scheme_detail_res = client.get(f"/schemes/{scheme.id}", headers=headers)
    assert scheme_detail_res.status_code == 200
    assert scheme_detail_res.json()["name"] == "Pradhan Mantri Mudra Yojana (PMMY)"

    # =========================================================================
    # 4. MATCHING ENGINE
    # =========================================================================
    matches_res = client.post("/schemes/match", json={"refresh": True}, headers=headers)
    assert matches_res.status_code == 200
    matches = matches_res.json()
    assert len(matches) >= 1
    assert matches[0]["scheme_id"] == str(scheme.id)
    assert float(matches[0]["match_score"]) > 0
    assert "match_reasons" in matches[0] or "eligibility_status" in matches[0]

    # =========================================================================
    # 5. DOCUMENT UPLOAD & OCR
    # =========================================================================
    from PIL import Image
    img = Image.new("RGB", (120, 40), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    test_file_content = buf.getvalue()

    files = {
        "file": ("aadhaar_sample.png", io.BytesIO(test_file_content), "image/png")
    }
    data = {"doc_type": "aadhaar"}
    upload_res = client.post("/documents/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 200
    doc_data = upload_res.json()
    assert doc_data["doc_type"] == "aadhaar"
    assert doc_data["verification_status"] in ["uploaded", "pending", "pending_verification", "verified"]
    doc_id = doc_data["id"]

    # List documents
    docs_list_res = client.get("/documents", headers=headers)
    assert docs_list_res.status_code == 200
    assert len(docs_list_res.json()) >= 1

    # =========================================================================
    # 6. APPLICATION CREATION & SUBMISSION & TRACKING
    # =========================================================================
    app_create_res = client.post(
        "/applications",
        json={
            "scheme_id": str(scheme.id),
            "requested_amount_inr": 350000.0,
            "application_data": {
                "purpose": "Expanding kitchen processing unit",
                "attached_documents": [doc_id]
            }
        },
        headers=headers
    )
    assert app_create_res.status_code == 200
    app_id = app_create_res.json()["id"]
    assert app_create_res.json()["status"] == "draft"

    # Submit Application
    app_submit_res = client.post(f"/applications/{app_id}/submit", headers=headers)
    assert app_submit_res.status_code == 200
    assert app_submit_res.json()["status"] == "submitted"

    # Track Application Details
    app_track_res = client.get(f"/applications/{app_id}", headers=headers)
    assert app_track_res.status_code == 200
    assert app_track_res.json()["status"] == "submitted"
    assert app_track_res.json()["next_action"] == "Under review by authorities"

    # =========================================================================
    # 7. CHAT
    # =========================================================================
    chat_res = client.post(
        "/chat/message",
        json={"message": "What documents do I need for Mudra loan?"},
        headers=headers
    )
    assert chat_res.status_code == 200
    assert "reply" in chat_res.json() or "response" in chat_res.json()
    chat_reply = chat_res.json().get("reply") or chat_res.json().get("response")
    assert len(chat_reply) > 0

    # =========================================================================
    # 8. CSC LOCATOR
    # =========================================================================
    csc_res = client.get("/csc/nearby?lat=18.5204&lng=73.8567&radius_km=10", headers=headers)
    assert csc_res.status_code == 200
    res_data = csc_res.json()
    centers = res_data.get("centers", res_data)
    assert len(centers) >= 1
    assert centers[0]["name"] == "CSC Common Services Centre - Central"

    # =========================================================================
    # 9. NOTIFICATIONS
    # =========================================================================
    notif = Notification(
        id=uuid.uuid4(),
        user_id=uuid.UUID(auth_data["user"]["id"]),
        title="Application Submitted",
        body="Your application for PMMY was submitted successfully.",
        type="application_update",
        is_read=False
    )
    test_db.add(notif)
    test_db.commit()

    notif_list_res = client.get("/notifications", headers=headers)
    assert notif_list_res.status_code == 200
    notifications = notif_list_res.json()
    assert len(notifications) >= 1
    assert notifications[0]["title"] == "Application Submitted"

    mark_read_res = client.patch(f"/notifications/{notif.id}/read", headers=headers)
    assert mark_read_res.status_code == 200
    assert "Marked as read" in mark_read_res.json()["message"]
