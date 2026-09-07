"""Tests for AI Chat, CSC Locator, and Notifications."""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models import User, CSCCenter, Notification
from app.services.notification_service import get_notification_service


@pytest.fixture
def auth_user(test_db):
    user = User(
        id=uuid.uuid4(),
        phone="+919876500050",
        full_name="Chat User",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    return user, {"Authorization": f"Bearer {token}"}


def test_chat_message_flow(client, auth_user):
    _, headers = auth_user
    chat_payload = {
        "message": "What schemes are available for women in food processing?",
        "language": "en",
        "channel": "text"
    }
    response = client.post("/chat/message", json=chat_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0


def test_csc_locator_nearby_and_district(test_db, client):
    # Seed sample CSC centers
    c1 = CSCCenter(
        csc_id="CSC-TEST-001",
        name="Bangalore Rural CSC",
        state="Karnataka",
        district="Bangalore Rural",
        address="Main Road, Devanahalli",
        phone="+919876543210",
        latitude=13.2465,
        longitude=77.7118,
        services_offered=["Aadhaar", "PAN", "UDYAM"],
        is_active=True
    )
    c2 = CSCCenter(
        csc_id="CSC-TEST-002",
        name="Delhi North CSC",
        state="Delhi",
        district="North Delhi",
        address="Civil Lines",
        phone="+919876543211",
        latitude=28.7041,
        longitude=77.1025,
        services_offered=["Aadhaar", "PAN"],
        is_active=True
    )
    test_db.add_all([c1, c2])
    test_db.commit()

    # Query nearby Bangalore (lat 13.24, lng 77.71) within 15 km
    res_nearby = client.get("/csc/nearby?lat=13.24&lng=77.71&radius_km=15")
    assert res_nearby.status_code == 200
    nearby_data = res_nearby.json()
    assert nearby_data["count"] >= 1
    assert nearby_data["centers"][0]["csc_id"] == "CSC-TEST-001"
    assert "distance_km" in nearby_data["centers"][0]

    # Query by district
    res_dist = client.get("/csc/by-district?state=Karnataka&district=Bangalore%20Rural")
    assert res_dist.status_code == 200
    assert len(res_dist.json()["centers"]) == 1
    assert res_dist.json()["centers"][0]["name"] == "Bangalore Rural CSC"


def test_notifications_workflow(test_db, client, auth_user):
    user, headers = auth_user
    service = get_notification_service(test_db)

    # 1. Create notification
    notif = service.create_notification(
        user_id=user.id,
        notif_type="scheme_match",
        title="New Match Found",
        body="You match with Stand-Up India scheme.",
        priority="high"
    )

    # 2. Get unread count
    count_res = client.get("/notifications/unread-count", headers=headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] == 1

    # 3. List notifications
    list_res = client.get("/notifications", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    notif_id = list_res.json()[0]["id"]
    assert list_res.json()[0]["is_read"] is False

    # 4. Mark as read
    read_res = client.put(f"/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200

    # 5. Verify unread count is now 0
    count_res2 = client.get("/notifications/unread-count", headers=headers)
    assert count_res2.status_code == 200
    assert count_res2.json()["unread_count"] == 0
