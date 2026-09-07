"""Tests for User Onboarding, Profile, and Business Profile management."""
import pytest
from datetime import date
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models import User, Business


@pytest.fixture
def auth_user(test_db):
    user = User(
        id=uuid.uuid4(),
        phone="+919876500001",
        full_name="Ananya Verma",
        gender="female",
        social_category="general",
        state="Karnataka",
        district="Bangalore",
        is_active=True,
        onboarding_completed=False
    )
    test_db.add(user)
    test_db.commit()
    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    return user, {"Authorization": f"Bearer {token}"}


def test_get_user_profile(client, auth_user):
    user, headers = auth_user
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == user.phone
    assert data["full_name"] == "Ananya Verma"
    assert data["gender"] == "female"


def test_update_user_profile(client, auth_user, test_db):
    user, headers = auth_user
    update_data = {
        "full_name": "Ananya Sharma",
        "state": "Maharashtra",
        "district": "Pune",
        "is_rural": False,
        "onboarding_completed": True
    }
    response = client.put("/users/me", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Ananya Sharma"
    assert data["state"] == "Maharashtra"
    assert data["district"] == "Pune"


def test_business_create_and_get(client, auth_user, test_db):
    user, headers = auth_user
    business_payload = {
        "business_name": "Verma Artisanal Foods",
        "business_type": "food_processing",
        "business_stage": "revenue",
        "annual_turnover_inr": 1200000.0,
        "num_employees": 5,
        "funding_needed_inr": 500000.0,
        "has_collateral": False
    }

    # Create business
    post_res = client.post("/users/me/business", json=business_payload, headers=headers)
    assert post_res.status_code == 200
    created = post_res.json()
    assert created["business_name"] == "Verma Artisanal Foods"
    assert created["business_type"] == "food_processing"

    # Get business
    get_res = client.get("/users/me/business", headers=headers)
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["business_name"] == "Verma Artisanal Foods"
    assert fetched["has_collateral"] is False


def test_business_relationship_cascade(test_db):
    user = User(
        id=uuid.uuid4(),
        phone="+919876500002",
        full_name="Test Cascade User",
        is_active=True
    )
    test_db.add(user)
    test_db.flush()

    business = Business(
        user_id=user.id,
        business_name="Cascade Enterprise",
        business_type="trading"
    )
    test_db.add(business)
    test_db.commit()

    # Query back
    assert user.business is not None
    assert user.business.business_name == "Cascade Enterprise"
    assert business.user.phone == "+919876500002"
