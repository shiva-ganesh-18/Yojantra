"""Tests for Schemes discovery, search, filters, and admin management."""
import pytest
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models import User, Scheme


@pytest.fixture
def sample_schemes(test_db):
    s1 = Scheme(
        id=uuid.uuid4(),
        name="PM Mudra Yojana",
        ministry="Ministry of Finance",
        description="Micro finance scheme providing loans up to 10 lakh.",
        scheme_type="loan",
        max_benefit_inr=Decimal("1000000"),
        status="active"
    )
    s2 = Scheme(
        id=uuid.uuid4(),
        name="Startup India Seed Fund",
        ministry="DPIIT",
        description="Early stage grant assistance for technology startups.",
        scheme_type="grant",
        max_benefit_inr=Decimal("2000000"),
        status="active"
    )
    test_db.add_all([s1, s2])
    test_db.commit()
    return s1, s2


def test_list_schemes(client, sample_schemes):
    response = client.get("/schemes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_search_schemes_by_query(client, sample_schemes):
    response = client.get("/schemes?q=Mudra")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "PM Mudra Yojana"


def test_filter_schemes_by_type(client, sample_schemes):
    response = client.get("/schemes?scheme_type=grant")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Startup India Seed Fund"


def test_get_scheme_by_id(client, sample_schemes):
    s1, _ = sample_schemes
    response = client.get(f"/schemes/{s1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PM Mudra Yojana"


def test_get_scheme_not_found(client, sample_schemes):
    random_id = uuid.uuid4()
    response = client.get(f"/schemes/{random_id}")
    assert response.status_code == 404


def test_get_recommended_schemes_route(client, test_db):
    """Ensure /schemes/recommended route is not masked by /schemes/{scheme_id}."""
    user = User(id=uuid.uuid4(), phone="+919876599999", full_name="Rec User", is_active=True, onboarding_completed=True)
    test_db.add(user)
    test_db.commit()
    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/schemes/recommended", headers=headers)
    # Should cleanly return 200 list (not 422 UUID parsing failure)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

