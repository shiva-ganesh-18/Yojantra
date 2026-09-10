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
    assert match.eligibility_status in ["Eligible", "fully_eligible"]
    assert match.recommendation_score is not None
    assert isinstance(match.why_you_match, list)
    assert isinstance(match.missing_requirements, list)
    assert isinstance(match.potential_issues, list)
    assert match.next_action is not None
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
    assert match.recommendation_score >= Decimal("70")
    assert match.eligibility_status in ["Eligible", "Possibly Eligible", "fully_eligible", "likely_eligible"]


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


def test_matching_engine_criteria_checks_and_score_breakdown(db_session):
    """Test detailed criteria checks (PASS/FAIL/UNKNOWN) and score breakdown."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Pradhan Mantri Mudra Yojana",
        ministry="Ministry of Finance",
        description="Loans up to 10 lakh for small enterprises.",
        scheme_type="loan",
        max_benefit_inr=Decimal("1000000"),
        min_benefit_inr=Decimal("50000"),
        collateral_required=False,
        is_national=True,
        requires_udyam=True,
        status="active"
    )
    db_session.add(scheme)

    # User without UDYAM to verify UNKNOWN status on that criterion
    user = User(
        id=uuid.uuid4(),
        phone="+919876543299",
        full_name="Geeta Patel",
        gender="female",
        social_category="obc",
        state="Gujarat",
        district="Surat"
    )
    db_session.add(user)

    biz = Business(
        id=uuid.uuid4(),
        user_id=user.id,
        business_name="Geeta Textiles",
        business_type="manufacturing",
        business_stage="revenue",
        annual_turnover_inr=Decimal("600000"),
        funding_needed_inr=Decimal("400000"),
        is_women_led=True
    )
    db_session.add(biz)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)

    assert len(matches) == 1
    match = matches[0]

    # Verify verdict and criteria checks
    assert match.overall_verdict in ("PASS", "UNKNOWN")
    assert len(match.criteria_checks) >= 5
    
    # State check should PASS
    state_check = next((c for c in match.criteria_checks if c.rule_id == "state"), None)
    assert state_check is not None
    assert state_check.status == "PASS"

    # UDYAM check should be UNKNOWN (pending registration)
    udyam_check = next((c for c in match.criteria_checks if c.rule_id == "udyam"), None)
    assert udyam_check is not None
    assert udyam_check.status == "UNKNOWN"

    # Score breakdown check
    assert match.score_breakdown is not None
    assert match.score_breakdown.demographic_score > Decimal("0")
    assert match.score_breakdown.enterprise_score > Decimal("0")
    assert match.score_breakdown.financial_score > Decimal("0")
    assert match.score_breakdown.total_score >= Decimal("50")

    # Loan recommendation check
    assert match.loan_recommendation is not None
    assert match.loan_recommendation.recommended_loan_amount == Decimal("400000")
    assert match.loan_recommendation.margin_money_required is not None
    assert match.loan_recommendation.estimated_monthly_emi is not None
    assert match.loan_recommendation.estimated_monthly_emi > Decimal("0")


def test_scheme_comparison_engine(db_session):
    """Test side-by-side scheme comparison for user."""
    s1 = Scheme(
        id=uuid.uuid4(),
        name="Scheme One",
        ministry="Ministry of MSME",
        description="Scheme One description.",
        scheme_type="subsidy",
        max_benefit_inr=Decimal("1000000"),
        subsidy_percentage=Decimal("35.0"),
        is_national=True,
        status="active"
    )
    s2 = Scheme(
        id=uuid.uuid4(),
        name="Scheme Two",
        ministry="Ministry of Finance",
        description="Scheme Two description.",
        scheme_type="loan",
        max_benefit_inr=Decimal("5000000"),
        is_national=True,
        status="active"
    )
    db_session.add_all([s1, s2])

    user = User(
        id=uuid.uuid4(),
        phone="+919876543288",
        full_name="Vijay Kumar",
        state="Maharashtra",
        district="Nagpur"
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    comp_resp = engine.compare_schemes(user.id, [s1.id, s2.id])

    assert len(comp_resp.schemes) == 2
    assert len(comp_resp.common_criteria) >= 2
    assert len(comp_resp.differing_features) >= 3
    assert comp_resp.recommendation_summary is not None


def test_loan_recommendation_moratorium_periods(db_session):
    """Test that scheme-specific moratorium periods (3-18 months) and amortized EMIs are accurately calculated."""
    standup = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Scheme",
        ministry="Ministry of Finance",
        description="Bank loan for greenfield enterprise.",
        scheme_type="loan",
        max_benefit_inr=Decimal("10000000"),
        min_benefit_inr=Decimal("1000000"),
        interest_rate=Decimal("9.50"),
        is_national=True,
        status="active"
    )
    pmegp = Scheme(
        id=uuid.uuid4(),
        name="PMEGP Prime Minister Employment Generation Programme",
        ministry="Ministry of MSME",
        description="Credit-linked subsidy scheme.",
        scheme_type="subsidy",
        max_benefit_inr=Decimal("5000000"),
        min_benefit_inr=Decimal("100000"),
        interest_rate=Decimal("9.00"),
        is_national=True,
        status="active"
    )
    svanidhi = Scheme(
        id=uuid.uuid4(),
        name="PM SVANidhi",
        ministry="Ministry of Housing and Urban Affairs",
        description="Working capital micro loan.",
        scheme_type="loan",
        max_benefit_inr=Decimal("50000"),
        min_benefit_inr=Decimal("10000"),
        interest_rate=Decimal("7.00"),
        is_national=True,
        status="active"
    )
    db_session.add_all([standup, pmegp, svanidhi])

    user = User(
        id=uuid.uuid4(),
        phone="+919876543277",
        full_name="Pooja Sharma",
        gender="female",
        social_category="general",
        state="Karnataka",
        district="Bengaluru"
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    
    # 1. Stand-Up India (18m moratorium, 84m total, 66m active repayment)
    rec_standup = engine._calculate_loan_recommendation(user, None, standup, Decimal("2000000"))
    assert rec_standup.moratorium_period_months == 18
    assert rec_standup.total_tenure_months == 84
    assert rec_standup.repayment_tenure_months == 66
    assert rec_standup.moratorium_note is not None
    assert rec_standup.estimated_monthly_emi > Decimal("0")

    # 2. PMEGP (6m moratorium, 84m total, 78m active repayment)
    rec_pmegp = engine._calculate_loan_recommendation(user, None, pmegp, Decimal("1000000"))
    assert rec_pmegp.moratorium_period_months == 6
    assert rec_pmegp.total_tenure_months == 84
    assert rec_pmegp.repayment_tenure_months == 78
    assert rec_pmegp.estimated_monthly_emi > Decimal("0")

    # 3. PM SVANidhi (1m moratorium, 12m total, 11m active repayment)
    rec_svanidhi = engine._calculate_loan_recommendation(user, None, svanidhi, Decimal("20000"))
    assert rec_svanidhi.moratorium_period_months == 1
    assert rec_svanidhi.total_tenure_months == 12
    assert rec_svanidhi.repayment_tenure_months == 11
    assert rec_svanidhi.estimated_monthly_emi > Decimal("0")


def test_profile_update_invalidates_stale_cache(db_session):
    """Test regression: profile update -> old cache -> /matches -> fresh matching results."""
    from datetime import datetime, timezone
    # Scheme 1: Open to all
    scheme_general = Scheme(
        id=uuid.uuid4(),
        name="General Micro Support",
        ministry="Ministry of MSME",
        description="General enterprise support.",
        is_national=True,
        target_genders=None,
        status="active"
    )
    # Scheme 2: Women-only scheme
    scheme_women = Scheme(
        id=uuid.uuid4(),
        name="Mahila Udyam Nidhi",
        ministry="Ministry of MSME",
        description="Scheme exclusively for women entrepreneurs.",
        is_national=True,
        target_genders=["female"],
        status="active"
    )
    db_session.add_all([scheme_general, scheme_women])

    # Initial User: male -> only qualifies for scheme_general
    past_time = datetime(2025, 1, 1, 10, 0, 0)
    user = User(
        id=uuid.uuid4(),
        phone="+919876543299",
        full_name="Alex Ray",
        gender="male",
        state="Delhi",
        district="New Delhi",
        created_at=past_time,
        updated_at=past_time
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)

    # 1. Initial matching with refresh=False -> matches 1 scheme (general)
    initial_matches = engine.match_user(user.id, refresh=False)
    assert len(initial_matches) == 1
    assert initial_matches[0].scheme_id == scheme_general.id

    # Simulate that initial match cache was created in the past
    cached_records = db_session.query(UserSchemeMatch).filter(UserSchemeMatch.user_id == user.id).all()
    assert len(cached_records) == 1
    for rec in cached_records:
        rec.created_at = past_time
        rec.updated_at = past_time
    db_session.commit()

    # 2. Querying again with unchanged profile -> uses cache
    cached_matches = engine.match_user(user.id, refresh=False)
    assert len(cached_matches) == 1
    assert cached_matches[0].scheme_id == scheme_general.id

    # 3. User updates profile (gender changed to female at a later time)
    new_time = datetime(2025, 6, 1, 12, 0, 0)
    user.gender = "female"
    user.updated_at = new_time
    db_session.commit()

    # 4. Calling match_user with refresh=False must automatically detect profile update
    # and recompute fresh results (now matching both general and women scheme)
    fresh_matches = engine.match_user(user.id, refresh=False)
    assert len(fresh_matches) == 2
    matched_scheme_ids = {m.scheme_id for m in fresh_matches}
    assert scheme_general.id in matched_scheme_ids
    assert scheme_women.id in matched_scheme_ids


def test_matching_new_user_without_business(db_session):
    """Test that a new user with no business profile receives national schemes and stage checks remain UNKNOWN (not FAIL)."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="PM National Credit Support",
        ministry="Ministry of MSME",
        description="National enterprise assistance.",
        is_national=True,
        target_business_stages=["pre_revenue", "revenue"],
        status="active"
    )
    db_session.add(scheme)

    user = User(
        id=uuid.uuid4(),
        phone="+919876543100",
        full_name="New Beneficiary",
        state="Maharashtra",
        district="Mumbai"
    )
    db_session.add(user)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)

    # Should match because missing business stage is UNKNOWN, not FAIL
    assert len(matches) == 1
    match = matches[0]
    assert match.scheme_id == scheme.id
    assert match.overall_verdict in ("PASS", "UNKNOWN")
    
    stage_check = next((c for c in match.criteria_checks if c.rule_id == "business_stage"), None)
    assert stage_check is not None
    assert stage_check.status == "UNKNOWN"


def test_matching_pre_revenue_turnover_zero(db_session):
    """Test that a pre-revenue/idea stage user with 0 turnover matches schemes supporting early-stage businesses."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Early Stage MSME Seed Fund",
        ministry="Ministry of MSME",
        description="Early stage MSME fund.",
        is_national=True,
        target_business_stages=["idea", "pre_revenue"],
        min_turnover_inr=Decimal("100000"),
        max_turnover_inr=Decimal("5000000"),
        status="active"
    )
    db_session.add(scheme)

    user = User(
        id=uuid.uuid4(),
        phone="+919876543101",
        full_name="Startup Founder",
        state="Karnataka",
        district="Bengaluru"
    )
    db_session.add(user)

    biz = Business(
        id=uuid.uuid4(),
        user_id=user.id,
        business_name="NextGen Tech",
        business_type="technology",
        business_stage="idea",
        annual_turnover_inr=Decimal("0")
    )
    db_session.add(biz)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)

    assert len(matches) == 1
    match = matches[0]
    assert match.scheme_id == scheme.id
    turnover_check = next((c for c in match.criteria_checks if c.rule_id == "turnover"), None)
    assert turnover_check is not None
    assert turnover_check.status == "UNKNOWN"


def test_matching_generic_business_type_becomes_unknown(db_session):
    """Test that generic/unspecified business type (e.g. 'other', 'unspecified', 'general') is UNKNOWN, not FAIL."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Handicraft Promotion Scheme",
        ministry="Ministry of Textiles",
        description="Support for handicraft artisans.",
        is_national=True,
        target_business_types=["handicraft"],
        status="active"
    )
    db_session.add(scheme)

    user = User(
        id=uuid.uuid4(),
        phone="+919876543102",
        full_name="Artisan Explorer",
        state="Rajasthan",
        district="Jaipur"
    )
    db_session.add(user)

    biz = Business(
        id=uuid.uuid4(),
        user_id=user.id,
        business_name="Unspecified Shop",
        business_type="other",
        business_stage="revenue"
    )
    db_session.add(biz)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user.id)

    # Should match as Possibly Eligible because 'other' is treated as UNKNOWN for sector-specific schemes
    assert len(matches) == 1
    match = matches[0]
    assert match.scheme_id == scheme.id
    btype_check = next((c for c in match.criteria_checks if c.rule_id == "business_type"), None)
    assert btype_check is not None
    assert btype_check.status == "UNKNOWN"


def test_matching_genuine_state_mismatch_disqualifies(db_session):
    """Test that a genuine state mismatch strictly disqualifies the user."""
    scheme_gujarat = Scheme(
        id=uuid.uuid4(),
        name="Gujarat State MSME Subsidy",
        ministry="Govt of Gujarat",
        description="Restricted to Gujarat units.",
        is_national=False,
        applicable_states=["Gujarat"],
        status="active"
    )
    db_session.add(scheme_gujarat)

    user_tn = User(
        id=uuid.uuid4(),
        phone="+919876543103",
        full_name="Chennai Retailer",
        state="Tamil Nadu",
        district="Chennai"
    )
    db_session.add(user_tn)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user_tn.id)

    # Must NOT match due to genuine state mismatch
    assert len(matches) == 0


def test_matching_genuine_age_mismatch_disqualifies(db_session):
    """Test that genuine age mismatch (applicant below min_age or above max_age) strictly disqualifies."""
    scheme_youth = Scheme(
        id=uuid.uuid4(),
        name="Youth Innovation Grant",
        ministry="Ministry of Youth Affairs",
        description="Scheme for applicants aged 18 to 35.",
        is_national=True,
        min_age=18,
        max_age=35,
        status="active"
    )
    db_session.add(scheme_youth)

    # User aged 50 (born 1974)
    user_senior = User(
        id=uuid.uuid4(),
        phone="+919876543104",
        full_name="Senior Entrepreneur",
        date_of_birth=date(1974, 5, 10),
        state="Karnataka",
        district="Bengaluru"
    )
    db_session.add(user_senior)
    db_session.commit()

    engine = SchemeMatchingEngine(db_session)
    matches = engine.match_user(user_senior.id)

    # Must NOT match due to hard age limit
    assert len(matches) == 0




