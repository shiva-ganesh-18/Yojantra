"""Comprehensive test suite for SchemeMatchingEngine and database models."""
# pyrefly: ignore [missing-import]
import pytest
from datetime import date, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import User, Business, Scheme, UserSchemeMatch
from app.services.matching_engine import SchemeMatchingEngine, get_matching_engine


@pytest.fixture
def db_session():
    """Create in-memory SQLite database and return a session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_matching_engine_stand_up_india(db_session):
    """Test Stand-Up India matching for an eligible female SC entrepreneur."""
    # Create Scheme
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India",
        ministry="Ministry of Finance",
        description="Bank loans for greenfield enterprise by SC/ST or woman entrepreneur.",
        scheme_type="loan",
        max_benefit_inr=Decimal("10000000"),
        min_benefit_inr=Decimal("1000000"),
        benefit_description="Bank loan ₹10 lakh - ₹1 crore",
        collateral_required=False,
        is_national=True,
        target_genders=["female"],
        target_social_categories=["sc", "st"],
        target_business_types=["manufacturing", "service", "trading"],
        target_business_stages=["pre_revenue", "revenue"],
        max_turnover_inr=Decimal("10000000"),
        max_employees=50,
        women_ownership_min_percent=51,
        requires_udyam=True,
        requires_gst=False,
        status="active"
    )
    db_session.add(scheme)

    # Create Eligible User (Woman, SC, manufacturing, with UDYAM)
    user_eligible = User(
        id=uuid.uuid4(),
        phone="+919876543210",
        full_name="Sunita Devi",
        gender="female",
        social_category="sc",
        state="Maharashtra",
        district="Pune",
        udyam_number="UDYAM-MH-12-0012345",
        date_of_birth=date(1990, 5, 15),
        onboarding_completed=True
    )
    db_session.add(user_eligible)

    biz_eligible = Business(
        id=uuid.uuid4(),
        user_id=user_eligible.id,
        business_name="Sunita Garments",
        business_type="manufacturing",
        business_stage="revenue",
        annual_turnover_inr=Decimal("1500000"),
        num_employees=5,
        is_women_led=True,
        has_collateral=False,
        funding_needed_inr=Decimal("2000000")
    )
    db_session.add(biz_eligible)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user_eligible.id)

    assert len(matches) == 1
    match = matches[0]
    assert match.name == "Stand-Up India"
    assert match.match_score >= Decimal("90")
    assert match.eligibility_status == "fully_eligible"
    assert match.confidence_level == "high"
    assert "You match the Stand-Up India scheme because:" in match.ai_explanation
    assert "• You are located in Maharashtra" in match.ai_explanation


def test_matching_engine_gender_category_disqualification(db_session):
    """Test that a male general category entrepreneur is properly disqualified for Stand-Up India."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India",
        ministry="Ministry of Finance",
        description="SC/ST or woman entrepreneur loan.",
        scheme_type="loan",
        is_national=True,
        target_genders=["female"],
        target_social_categories=["sc", "st"],
        status="active"
    )
    db_session.add(scheme)

    user_ineligible = User(
        id=uuid.uuid4(),
        phone="+919876543211",
        full_name="Rahul Sharma",
        gender="male",
        social_category="general",
        state="Delhi",
        district="Central Delhi"
    )
    db_session.add(user_ineligible)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user_ineligible.id)

    # Ineligible schemes (status == "not_eligible") are excluded from the user's active matches list
    assert len(matches) == 0


def test_mudra_scheme_general_matching(db_session):
    """Test PM Mudra matching for general entrepreneurs with micro loans."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="PM Mudra Yojana (PMMY)",
        ministry="Ministry of Finance",
        description="Loans up to 10 lakh for small enterprises.",
        scheme_type="loan",
        max_benefit_inr=Decimal("1000000"),
        min_benefit_inr=Decimal("10000"),
        is_national=True,
        target_genders=None,  # Open to all
        target_social_categories=None,  # Open to all
        target_business_types=["manufacturing", "service", "retail"],
        max_turnover_inr=Decimal("5000000"),
        status="active"
    )
    db_session.add(scheme)

    user = User(
        id=uuid.uuid4(),
        phone="+919876543212",
        full_name="Amit Kumar",
        gender="male",
        social_category="obc",
        state="Karnataka",
        district="Bangalore",
        date_of_birth=date(1995, 2, 10)
    )
    db_session.add(user)

    biz = Business(
        id=uuid.uuid4(),
        user_id=user.id,
        business_name="Kumar Electronics",
        business_type="retail",
        business_stage="revenue",
        annual_turnover_inr=Decimal("800000"),
        num_employees=2,
        funding_needed_inr=Decimal("500000")
    )
    db_session.add(biz)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)

    assert len(matches) == 1
    match = matches[0]
    assert match.name == "PM Mudra Yojana (PMMY)"
    assert match.match_score >= Decimal("70")
    assert match.eligibility_status in ["fully_eligible", "likely_eligible"]


def test_expired_deadline_disqualification(db_session):
    """Test that expired schemes are marked not_eligible and filtered out."""
    scheme_expired = Scheme(
        id=uuid.uuid4(),
        name="Expired Subsidy Scheme",
        ministry="Ministry of MSME",
        description="Scheme with past deadline.",
        application_deadline=date.today() - timedelta(days=5),
        is_national=True,
        status="active"
    )
    db_session.add(scheme_expired)

    user = User(
        id=uuid.uuid4(),
        phone="+919876543213",
        full_name="Pooja Patel",
        gender="female",
        state="Gujarat",
        district="Ahmedabad"
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)
    assert len(matches) == 0


def test_caching_and_refresh(db_session):
    """Test that match_user respects caching and updates on refresh=True."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Universal Support Scheme",
        ministry="Ministry of MSME",
        description="Open support scheme.",
        is_national=True,
        status="active"
    )
    db_session.add(scheme)

    user = User(
        id=uuid.uuid4(),
        phone="+919876543214",
        full_name="Deepak Verma",
        state="Rajasthan",
        district="Jaipur"
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    # First run computes matches
    first_run = engine.match_user(user.id, refresh=False)
    assert len(first_run) == 1

    # Check that DB now has a UserSchemeMatch record
    saved_count = db_session.query(UserSchemeMatch).filter(UserSchemeMatch.user_id == user.id).count()
    assert saved_count == 1

    # Second run without refresh returns from cache
    cached_run = engine.match_user(user.id, refresh=False)
    assert len(cached_run) == 1
    assert cached_run[0].scheme_id == first_run[0].scheme_id

    # Third run with refresh=True re-evaluates
    refreshed_run = engine.match_user(user.id, refresh=True)
    assert len(refreshed_run) == 1
    assert refreshed_run[0].scheme_id == first_run[0].scheme_id


def test_top_recommended_flag(db_session):
    """Test that top matches are marked is_recommended=True."""
    # Create 3 schemes
    for i in range(3):
        db_session.add(Scheme(
            id=uuid.uuid4(),
            name=f"Scheme {i+1}",
            ministry="Govt of India",
            description=f"Description for scheme {i+1}",
            is_national=True,
            status="active"
        ))

    user = User(
        id=uuid.uuid4(),
        phone="+919876543215",
        full_name="Aarti Sharma",
        state="Haryana",
        district="Gurugram"
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)
    assert len(matches) == 3

    # All top matches (up to 10) should have is_recommended=True in DB
    recommended = db_session.query(UserSchemeMatch).filter(
        UserSchemeMatch.user_id == user.id,
        UserSchemeMatch.is_recommended == True
    ).all()
    assert len(recommended) == 3
