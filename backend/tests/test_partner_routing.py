"""Unit and integration tests for Channel Partner digital routing workflow (Part 1)."""
import uuid
from decimal import Decimal
import pytest

from app.models import User, Scheme, Application, Institution, Document, Business
from app.services.partner_routing_service import PartnerRoutingService, SCHEME_CATEGORY_RULES, MAX_ELIGIBLE_GROSS_NPA_RATIO
from app.services.banking_service import (
    LiveBankingPartnerData, 
    BankingDataSyncStatus, 
    PartnerNPARiskLevel, 
    PartnerCapacityTier
)
from app.core.security import create_access_token


def test_determine_scheme_category(test_db):
    """Test scheme category classification logic for various MSME schemes."""
    service = PartnerRoutingService(test_db)

    # 1. Stand-Up India
    scheme_standup = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Scheme",
        ministry="Ministry of Finance",
        description="Bank loans for SC/ST and women entrepreneurs",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_standup)
    assert cat["category_code"] == "STAND_UP"
    assert "PSB" in cat["eligible_types"]
    assert cat["preferred_type"] == "PSB"

    # 2. PMEGP
    scheme_pmegp = Scheme(
        id=uuid.uuid4(),
        name="Prime Minister's Employment Generation Programme (PMEGP)",
        ministry="Ministry of MSME",
        description="Margin money subsidy for micro enterprises",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_pmegp)
    assert cat["category_code"] == "PMEGP"
    assert "SCA" in cat["eligible_types"]
    assert cat["preferred_type"] == "SCA"

    # 3. PM Mudra
    scheme_mudra = Scheme(
        id=uuid.uuid4(),
        name="Pradhan Mantri MUDRA Yojana (PMMY)",
        ministry="Ministry of Finance",
        description="Loans up to 10 lakhs for small businesses",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_mudra)
    assert cat["category_code"] == "MUDRA"
    assert "RRB" in cat["eligible_types"]
    assert cat["preferred_type"] == "RRB"

    # 4. PM SVANidhi
    scheme_svanidhi = Scheme(
        id=uuid.uuid4(),
        name="PM SVANidhi Micro Credit",
        ministry="MoHUA",
        description="Micro-credit for street vendors",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_svanidhi)
    assert cat["category_code"] == "SVANIDHI"
    assert "PSB" in cat["eligible_types"]

    # 5. Affirmative Action / Tribal
    scheme_tribal = Scheme(
        id=uuid.uuid4(),
        name="National Scheduled Tribes Finance Development",
        ministry="Ministry of Tribal Affairs",
        description="Concessional financial assistance for ST beneficiaries",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_tribal)
    assert cat["category_code"] == "AFFIRMATIVE_SCA"
    assert "SCA" in cat["eligible_types"]

    # 6. Technology Grant / Incubation
    scheme_tech = Scheme(
        id=uuid.uuid4(),
        name="ASPIRE Technology Incubation Scheme",
        ministry="Ministry of MSME",
        scheme_type="grant",
        description="Promoting innovation and rural entrepreneurship",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_tech)
    assert cat["category_code"] == "TECH_GRANT"

    # 7. General MSME Fallback
    scheme_gen = Scheme(
        id=uuid.uuid4(),
        name="Credit Guarantee Trust for MSEs (CGTMSE)",
        ministry="Ministry of MSME",
        description="Collateral free credit facility",
        status="active"
    )
    cat = service.determine_scheme_category(scheme_gen)
    assert cat["category_code"] == "GENERAL_MSME"

    # 8. None Scheme
    cat_none = service.determine_scheme_category(None)
    assert cat_none["category_code"] == "GENERAL_MSME"


def test_find_eligible_partners_matching_hierarchy(test_db):
    """Test channel partner discovery, filtering by eligible type and geographic ranking."""
    service = PartnerRoutingService(test_db)

    user = User(
        id=uuid.uuid4(),
        phone="+919876540001",
        full_name="Ramesh Patel",
        state="Gujarat",
        district="Ahmedabad",
        is_active=True
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Scheme",
        ministry="Ministry of Finance",
        description="Bank loans for SC/ST and women entrepreneurs",
        status="active"
    )
    test_db.add_all([user, scheme])
    test_db.commit()

    # Create 4 partners:
    # 1. District match + preferred type (PSB in Ahmedabad, Gujarat)
    p_district = Institution(
        id=uuid.uuid4(),
        name="State Bank of India - Ahmedabad Main Branch",
        institution_type="PSB",
        state="Gujarat",
        district="Ahmedabad",
        city="Ahmedabad",
        address="Bhadra, Ahmedabad 380001",
        status="active"
    )
    # 2. State match (RRB in Vadodara, Gujarat)
    p_state = Institution(
        id=uuid.uuid4(),
        name="Baroda Gujarat Gramin Bank",
        institution_type="RRB",
        state="Gujarat",
        district="Vadodara",
        city="Vadodara",
        address="Sayajiganj, Vadodara",
        status="active"
    )
    # 3. Ineligible type for Stand-Up (e.g., State University)
    p_ineligible = Institution(
        id=uuid.uuid4(),
        name="Ahmedabad Arts College",
        institution_type="State University",
        state="Gujarat",
        district="Ahmedabad",
        status="active"
    )
    # 4. Out of state partner (PSB in Delhi)
    p_national = Institution(
        id=uuid.uuid4(),
        name="Punjab National Bank - Connaught Place",
        institution_type="PSB",
        state="Delhi",
        district="New Delhi",
        city="New Delhi",
        status="active"
    )
    test_db.add_all([p_district, p_state, p_ineligible, p_national])
    test_db.commit()

    app = Application(
        id=uuid.uuid4(),
        user_id=user.id,
        scheme_id=scheme.id,
        status="draft"
    )
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)

    # Ineligible partner must not be included
    partner_ids = [p.partner_id for p in eligible_partners]
    assert p_ineligible.id not in partner_ids
    assert p_district.id in partner_ids
    assert p_state.id in partner_ids
    assert p_national.id in partner_ids

    # Top assigned partner should be district-matched preferred partner
    assert assigned is not None
    assert assigned.partner_id == p_district.id
    assert assigned.partner_name == "State Bank of India - Ahmedabad Main Branch"
    assert assigned.is_preferred is True
    assert assigned.district == "Ahmedabad"
    assert assigned.location == "Ahmedabad, Gujarat"
    assert "Primary district nodal partner in Ahmedabad" in assigned.recommendation_reason


def test_empty_partner_result_when_none_exist(test_db):
    """If no suitable channel partner exists, return a clear empty result."""
    service = PartnerRoutingService(test_db)

    user = User(
        id=uuid.uuid4(),
        phone="+919876540002",
        full_name="Kavita Rao",
        state="Sikkim",
        district="Gangtok",
        is_active=True
    )
    # Mudra scheme (eligible: PSB, RRB, NBFC-MFI)
    scheme = Scheme(
        id=uuid.uuid4(),
        name="PM Mudra Yojana",
        ministry="Ministry of Finance",
        description="Micro units development loans",
        status="active"
    )
    # Add only colleges / universities in DB
    inst = Institution(
        id=uuid.uuid4(),
        name="Sikkim State University",
        institution_type="State University",
        state="Sikkim",
        district="Gangtok",
        status="active"
    )
    test_db.add_all([user, scheme, inst])
    test_db.commit()

    app = Application(
        id=uuid.uuid4(),
        user_id=user.id,
        scheme_id=scheme.id,
        status="draft"
    )
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert len(eligible_partners) == 0
    assert assigned is None

    response = service.get_application_partner_routing(app)
    assert response.total_eligible_partners == 0
    assert response.assigned_partner is None
    assert response.eligible_partners == []
    assert "No accredited channel partners" in response.routing_note


def test_get_application_partners_api_endpoint(client, test_db):
    """Test GET /applications/{app_id}/partners and /routing-partners endpoints with auth & ownership checks."""
    user_a = User(id=uuid.uuid4(), phone="+919876540011", full_name="User A", state="Maharashtra", district="Pune", is_active=True)
    user_b = User(id=uuid.uuid4(), phone="+919876540012", full_name="User B", state="Maharashtra", district="Pune", is_active=True)
    scheme = Scheme(
        id=uuid.uuid4(),
        name="PMEGP Scheme",
        ministry="Ministry of MSME",
        description="Employment generation margin money scheme",
        status="active"
    )
    partner = Institution(
        id=uuid.uuid4(),
        name="Maharashtra State Channelizing Agency",
        institution_type="SCA",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        address="Shivaji Nagar, Pune",
        status="active"
    )
    test_db.add_all([user_a, user_b, scheme, partner])
    test_db.commit()

    token_a = create_access_token(data={"sub": str(user_a.id), "role": "user"})
    token_b = create_access_token(data={"sub": str(user_b.id), "role": "user"})
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create application for User A
    create_res = client.post("/applications", json={"scheme_id": str(scheme.id)}, headers=headers_a)
    assert create_res.status_code == 200
    app_id = create_res.json()["id"]

    # 1. User A gets partners
    res_a = client.get(f"/applications/{app_id}/partners", headers=headers_a)
    assert res_a.status_code == 200
    data = res_a.json()
    assert data["application_id"] == app_id
    assert data["scheme_id"] == str(scheme.id)
    assert data["scheme_category"] == "PMEGP Margin Money Subsidy & Micro-Enterprise Credit"
    assert data["total_eligible_partners"] >= 1
    assert data["assigned_partner"]["partner_name"] == "Maharashtra State Channelizing Agency"
    assert data["assigned_partner"]["partner_type"] == "SCA"
    assert data["assigned_partner"]["location"] == "Pune, Maharashtra"
    assert data["assigned_partner"]["is_preferred"] is True

    # 2. Test alias endpoint /routing-partners
    alias_res = client.get(f"/applications/{app_id}/routing-partners", headers=headers_a)
    assert alias_res.status_code == 200
    assert alias_res.json()["category_code"] == "PMEGP"

    # 3. User B gets 403/404 (ownership security)
    res_b = client.get(f"/applications/{app_id}/partners", headers=headers_b)
    assert res_b.status_code in (403, 404)

    # 4. Non-existent application returns 404
    fake_id = str(uuid.uuid4())
    res_fake = client.get(f"/applications/{fake_id}/partners", headers=headers_a)
    assert res_fake.status_code == 404


def test_submit_application_with_partner_routing(client, test_db):
    """Test that submitting an application prepares channel partner routing and updates timeline note."""
    user = User(
        id=uuid.uuid4(),
        phone="+919876540020",
        full_name="Anita Desai",
        state="Karnataka",
        district="Bangalore Urban",
        is_active=True
    )
    biz = Business(
        id=uuid.uuid4(),
        user_id=user.id,
        business_name="Desai Crafts",
        business_type="manufacturing",
        registration_type="udyam",
        annual_turnover_inr=Decimal("2000000")
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Scheme",
        ministry="Ministry of Finance",
        description="Loans for women and SC/ST entrepreneurs",
        requires_udyam=False,
        documents_required=["aadhaar", "pan"],
        status="active"
    )
    doc_aadhaar = Document(id=uuid.uuid4(), user_id=user.id, doc_type="aadhaar", file_url="/fake/aadhaar.pdf", verification_status="verified")
    doc_pan = Document(id=uuid.uuid4(), user_id=user.id, doc_type="pan", file_url="/fake/pan.pdf", verification_status="verified")

    partner = Institution(
        id=uuid.uuid4(),
        name="Canara Bank - Bangalore MSME Care Center",
        institution_type="PSB",
        state="Karnataka",
        district="Bangalore Urban",
        city="Bangalore",
        address="MG Road, Bangalore",
        status="active"
    )
    test_db.add_all([user, biz, scheme, doc_aadhaar, doc_pan, partner])
    test_db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create application
    create_res = client.post("/applications", json={"scheme_id": str(scheme.id)}, headers=headers)
    assert create_res.status_code == 200
    app_data = create_res.json()
    app_id = app_data["id"]
    assert app_data["scheme_category"] is not None
    assert app_data["assigned_partner_name"] == "Canara Bank - Bangalore MSME Care Center"

    # 2. Submit application
    submit_res = client.post(f"/applications/{app_id}/submit", headers=headers)
    assert submit_res.status_code == 200
    submit_data = submit_res.json()

    assert submit_data["status"] == "submitted"
    assert submit_data["scheme_category"] == "Stand-Up India Enterprise Credit (SC/ST/Women)"
    assert submit_data["assigned_partner"]["partner_name"] == "Canara Bank - Bangalore MSME Care Center"
    assert submit_data["assigned_partner"]["partner_type"] == "PSB"
    assert submit_data["total_eligible_partners"] >= 1

    # 3. Retrieve application detail to verify persisted partner routing
    get_res = client.get(f"/applications/{app_id}", headers=headers)
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["assigned_partner_name"] == "Canara Bank - Bangalore MSME Care Center"
    assert detail["assigned_partner_type"] == "PSB"
    assert detail["scheme_category"] == "Stand-Up India Enterprise Credit (SC/ST/Women)"

    # Check timeline step 2 note
    step2 = [s for s in detail["timeline"] if s["step"] == 2][0]
    assert "Canara Bank - Bangalore MSME Care Center" in step2["note"]
    assert step2["status"] == "current"


# =========================================================================
# PART 2 REGRESSION TESTS: ELIGIBILITY FILTERING & BANKING SAFEGUARDS
# =========================================================================

def test_inactive_partner_exclusion(test_db):
    """Verify that inactive/suspended channel partners are excluded with a transparent reason."""
    service = PartnerRoutingService(test_db)
    user = User(id=uuid.uuid4(), phone="+919876540050", full_name="Inactive Test User", state="Delhi", district="North Delhi", is_active=True)
    scheme = Scheme(id=uuid.uuid4(), name="PMEGP Scheme", ministry="Ministry of MSME", description="Subsidy scheme", status="active")
    
    inactive_partner = Institution(
        id=uuid.uuid4(),
        name="Suspended Delhi Nodal Center",
        institution_type="SCA",
        state="Delhi",
        district="North Delhi",
        status="inactive"
    )
    test_db.add_all([user, scheme, inactive_partner])
    test_db.commit()

    verdict, reason, meta = service.evaluate_partner_eligibility(inactive_partner, scheme, user)
    assert verdict == "INELIGIBLE"
    assert "inactive" in reason.lower()

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    partner_ids = [p.partner_id for p in eligible_partners]
    assert inactive_partner.id not in partner_ids
    assert assigned is None


def test_incompatible_partner_exclusion(test_db):
    """Verify that partners of incompatible category are excluded with an explanatory reason."""
    service = PartnerRoutingService(test_db)
    user = User(id=uuid.uuid4(), phone="+919876540051", full_name="Incompatible Test User", state="Karnataka", district="Mysore", is_active=True)
    scheme = Scheme(id=uuid.uuid4(), name="Pradhan Mantri MUDRA Yojana", ministry="Ministry of Finance", description="Micro loans", status="active")
    
    # State University is not a valid Mudra partner type (only PSB, RRB, NBFC-MFI)
    univ_partner = Institution(
        id=uuid.uuid4(),
        name="Mysore State University",
        institution_type="State University",
        state="Karnataka",
        district="Mysore",
        status="active"
    )
    test_db.add_all([user, scheme, univ_partner])
    test_db.commit()

    verdict, reason, meta = service.evaluate_partner_eligibility(univ_partner, scheme, user)
    assert verdict == "INELIGIBLE"
    assert "incompatible" in reason.lower()

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert univ_partner.id not in [p.partner_id for p in eligible_partners]


def test_verified_ineligible_partner_exclusion(test_db):
    """Verify that partners failing verified risk thresholds (high NPA, halted lending, zero capacity) are excluded."""
    service = PartnerRoutingService(test_db)
    user = User(id=uuid.uuid4(), phone="+919876540052", full_name="Risk Test User", state="Maharashtra", district="Mumbai", is_active=True)
    scheme = Scheme(id=uuid.uuid4(), name="Stand-Up India Scheme", ministry="Ministry of Finance", description="Credit scheme", status="active")

    # Partner 1: Gross NPA exceeds 12% threshold (15.5%)
    partner_high_npa = Institution(
        id=uuid.uuid4(),
        name="High NPA Regional Bank",
        institution_type="PSB",
        state="Maharashtra",
        district="Mumbai",
        status="active"
    )
    b_high_npa = LiveBankingPartnerData(
        partner_id=partner_high_npa.id,
        partner_name=partner_high_npa.name,
        institution_type="PSB",
        sync_status=BankingDataSyncStatus.LIVE,
        is_authenticated_live=True,
        gross_npa_ratio=Decimal("15.5"),
        npa_risk_indicator=PartnerNPARiskLevel.MODERATE,
        is_lending_halted=False
    )
    verdict1, reason1, _ = service.evaluate_partner_eligibility(partner_high_npa, scheme, user, banking_data=b_high_npa)
    assert verdict1 == "INELIGIBLE"
    assert "15.5%" in reason1
    assert "exceeds" in reason1.lower()

    # Partner 2: Lending halted
    partner_halted = Institution(
        id=uuid.uuid4(),
        name="Halted Facility Bank",
        institution_type="PSB",
        state="Maharashtra",
        district="Mumbai",
        status="active"
    )
    b_halted = LiveBankingPartnerData(
        partner_id=partner_halted.id,
        partner_name=partner_halted.name,
        institution_type="PSB",
        sync_status=BankingDataSyncStatus.LIVE,
        is_authenticated_live=True,
        gross_npa_ratio=Decimal("4.5"),
        is_lending_halted=True
    )
    verdict2, reason2, _ = service.evaluate_partner_eligibility(partner_halted, scheme, user, banking_data=b_halted)
    assert verdict2 == "INELIGIBLE"
    assert "halted" in reason2.lower()

    # Partner 3: Zero remaining lending quota capacity
    partner_zero_cap = Institution(
        id=uuid.uuid4(),
        name="Exhausted Quota Bank",
        institution_type="PSB",
        state="Maharashtra",
        district="Mumbai",
        status="active"
    )
    b_zero_cap = LiveBankingPartnerData(
        partner_id=partner_zero_cap.id,
        partner_name=partner_zero_cap.name,
        institution_type="PSB",
        sync_status=BankingDataSyncStatus.LIVE,
        is_authenticated_live=True,
        gross_npa_ratio=Decimal("5.0"),
        available_lending_capacity_inr=Decimal("0")
    )
    verdict3, reason3, _ = service.evaluate_partner_eligibility(partner_zero_cap, scheme, user, banking_data=b_zero_cap)
    assert verdict3 == "INELIGIBLE"
    assert "zero" in reason3.lower()

    # Partner 4: Elevated NPA risk indicator
    partner_elevated = Institution(
        id=uuid.uuid4(),
        name="Elevated Risk Bank",
        institution_type="PSB",
        state="Maharashtra",
        district="Mumbai",
        status="active"
    )
    b_elevated = LiveBankingPartnerData(
        partner_id=partner_elevated.id,
        partner_name=partner_elevated.name,
        institution_type="PSB",
        sync_status=BankingDataSyncStatus.LIVE,
        is_authenticated_live=True,
        npa_risk_indicator=PartnerNPARiskLevel.ELEVATED
    )
    verdict4, reason4, _ = service.evaluate_partner_eligibility(partner_elevated, scheme, user, banking_data=b_elevated)
    assert verdict4 == "INELIGIBLE"
    assert "elevated" in reason4.lower()


def test_missing_banking_status_becomes_needs_verification(test_db):
    """If live banking data is not available, the system must NOT invent values or fake ELIGIBLE status."""
    service = PartnerRoutingService(test_db)
    user = User(id=uuid.uuid4(), phone="+919876540053", full_name="Unconfigured User", state="Haryana", district="Gurugram", is_active=True)
    scheme = Scheme(id=uuid.uuid4(), name="Stand-Up India Scheme", ministry="Ministry of Finance", description="Credit scheme", status="active")

    partner = Institution(
        id=uuid.uuid4(),
        name="Punjab National Bank - Gurugram",
        institution_type="PSB",
        state="Haryana",
        district="Gurugram",
        status="active"
    )
    test_db.add_all([user, scheme, partner])
    test_db.commit()

    # No live banking telemetry provided
    verdict, reason, meta = service.evaluate_partner_eligibility(partner, scheme, user, banking_data=None)
    assert verdict == "NEEDS_VERIFICATION"
    assert "unconfigured" in reason.lower() or "awaiting" in reason.lower()
    assert meta["is_authenticated_live"] is False
    assert meta["gross_npa_ratio"] is None
    assert meta["available_lending_capacity_inr"] is None

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    response = service.get_application_partner_routing(app)
    assert response.total_needs_verification_partners >= 1
    assert response.assigned_partner is not None
    assert response.assigned_partner.eligibility_verdict == "NEEDS_VERIFICATION"
    assert response.assigned_partner.routing_status == "Awaiting Nodal Banking Verification"


def test_eligible_partner_selection(test_db):
    """When a verified clean partner and an unverified partner exist in the same district, the verified partner is selected."""
    service = PartnerRoutingService(test_db)
    user = User(id=uuid.uuid4(), phone="+919876540054", full_name="Verified Selection User", state="Tamil Nadu", district="Chennai", is_active=True)
    scheme = Scheme(id=uuid.uuid4(), name="Stand-Up India Scheme", ministry="Ministry of Finance", description="Credit scheme", status="active")

    # Partner A: Verified live with healthy metrics
    p_verified = Institution(
        id=uuid.uuid4(),
        name="Indian Bank - Chennai Harbor Branch",
        institution_type="PSB",
        state="Tamil Nadu",
        district="Chennai",
        status="active"
    )
    # Partner B: Unconfigured live telemetry
    p_unverified = Institution(
        id=uuid.uuid4(),
        name="Canara Bank - Chennai Main Branch",
        institution_type="PSB",
        state="Tamil Nadu",
        district="Chennai",
        status="active"
    )
    test_db.add_all([user, scheme, p_verified, p_unverified])
    test_db.commit()

    banking_map = {
        str(p_verified.id): LiveBankingPartnerData(
            partner_id=p_verified.id,
            partner_name=p_verified.name,
            institution_type="PSB",
            sync_status=BankingDataSyncStatus.LIVE,
            is_authenticated_live=True,
            gross_npa_ratio=Decimal("3.8"),
            npa_risk_indicator=PartnerNPARiskLevel.LOW,
            available_lending_capacity_inr=Decimal("50000000"),
            is_lending_halted=False
        )
    }

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app, banking_data=banking_map)
    assert len(eligible_partners) == 2
    assert assigned is not None
    assert assigned.partner_id == p_verified.id
    assert assigned.eligibility_verdict == "ELIGIBLE"
    assert assigned.is_authenticated_live is True
    assert assigned.gross_npa_ratio == Decimal("3.8")


def test_district_state_national_ranking_preserved(test_db):
    """Strictly preserve district -> state -> national ranking hierarchy for eligible partners."""
    service = PartnerRoutingService(test_db)
    user = User(id=uuid.uuid4(), phone="+919876540055", full_name="Ranking User", state="Rajasthan", district="Jaipur", is_active=True)
    scheme = Scheme(id=uuid.uuid4(), name="PMEGP Scheme", ministry="Ministry of MSME", description="Subsidy", status="active")

    # 1. District match
    p_dist = Institution(id=uuid.uuid4(), name="Jaipur District Industries Center (DIC)", institution_type="SCA", state="Rajasthan", district="Jaipur", status="active")
    # 2. State match
    p_state = Institution(id=uuid.uuid4(), name="Rajasthan State Financial Corporation", institution_type="SCA", state="Rajasthan", district="Jodhpur", status="active")
    # 3. National match (outside state)
    p_nat = Institution(id=uuid.uuid4(), name="Delhi State Channelizing Agency", institution_type="SCA", state="Delhi", district="New Delhi", status="active")

    test_db.add_all([user, scheme, p_dist, p_state, p_nat])
    test_db.commit()

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert len(eligible_partners) == 3
    # First must be district
    assert eligible_partners[0].partner_id == p_dist.id
    # Second must be state
    assert eligible_partners[1].partner_id == p_state.id
    # Third must be national
    assert eligible_partners[2].partner_id == p_nat.id


def test_nearest_and_farther_eligible_partner(test_db):
    """Nearest eligible partner ranks #1, farther eligible partner ranks #2 when coordinates are present."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540061", 
        full_name="Nearby User", 
        state="Maharashtra", 
        district="Pune",
        is_active=True
    )
    scheme = Scheme(
        id=uuid.uuid4(), 
        name="Stand-Up India Scheme", 
        ministry="Ministry of Finance", 
        description="Credit", 
        status="active"
    )

    # Near partner (~1.8 km from Pune center 18.5204, 73.8567)
    p_near = Institution(
        id=uuid.uuid4(),
        name="Bank of Maharashtra - Shivaji Nagar",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        latitude=18.5314,
        longitude=73.8446,
        status="active"
    )
    # Far partner (~29.1 km from Pune center)
    p_far = Institution(
        id=uuid.uuid4(),
        name="Bank of Maharashtra - Talegaon",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        latitude=18.7289,
        longitude=73.6845,
        status="active"
    )
    test_db.add_all([user, scheme, p_near, p_far])
    test_db.commit()

    app = Application(
        id=uuid.uuid4(), 
        user_id=user.id, 
        scheme_id=scheme.id, 
        status="draft",
        form_data={"latitude": 18.5204, "longitude": 73.8567}
    )
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert assigned is not None
    assert assigned.partner_id == p_near.id
    assert assigned.distance_km is not None
    assert assigned.distance_km < 5.0
    assert assigned.geographic_tier == "district"
    assert "Located" in assigned.recommendation_reason
    assert "km away" in assigned.recommendation_reason

    # Farther partner ranks second
    assert len(eligible_partners) == 2
    assert eligible_partners[0].partner_id == p_near.id
    assert eligible_partners[1].partner_id == p_far.id
    assert eligible_partners[1].distance_km > eligible_partners[0].distance_km
    assert eligible_partners[1].distance_km > 20.0


def test_district_partner_without_coordinates(test_db):
    """When coordinates are absent, district partner ranks ahead of state and national partners without inventing distance."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540062", 
        full_name="Lucknow User", 
        state="Uttar Pradesh", 
        district="Lucknow",
        is_active=True
    )
    scheme = Scheme(id=uuid.uuid4(), name="PMEGP Scheme", ministry="Ministry of MSME", description="Subsidy", status="active")

    p_district = Institution(
        id=uuid.uuid4(),
        name="Lucknow District Industries Centre",
        institution_type="SCA",
        state="Uttar Pradesh",
        district="Lucknow",
        latitude=None,
        longitude=None,
        status="active"
    )
    p_state = Institution(
        id=uuid.uuid4(),
        name="UP Khadi & Village Industries Board - Kanpur",
        institution_type="SCA",
        state="Uttar Pradesh",
        district="Kanpur Nagar",
        latitude=None,
        longitude=None,
        status="active"
    )
    p_national = Institution(
        id=uuid.uuid4(),
        name="Bihar State Channelizing Agency - Patna",
        institution_type="SCA",
        state="Bihar",
        district="Patna",
        latitude=None,
        longitude=None,
        status="active"
    )
    test_db.add_all([user, scheme, p_district, p_state, p_national])
    test_db.commit()

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert assigned is not None
    assert assigned.partner_id == p_district.id
    # Never invent distance or coordinates
    assert assigned.distance_km is None
    assert assigned.latitude is None
    assert assigned.longitude is None
    assert assigned.geographic_tier == "district"
    assert eligible_partners[0].partner_id == p_district.id
    assert eligible_partners[1].partner_id == p_state.id
    assert eligible_partners[2].partner_id == p_national.id


def test_partner_with_missing_coordinates(test_db):
    """Partners with missing coordinates have distance_km as None and are handled gracefully without error."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540063", 
        full_name="Jaipur User", 
        state="Rajasthan", 
        district="Jaipur",
        is_active=True
    )
    scheme = Scheme(id=uuid.uuid4(), name="Stand-Up India Scheme", ministry="Ministry of Finance", description="Credit", status="active")

    p_with_coords = Institution(
        id=uuid.uuid4(),
        name="State Bank of India - Sanganer Branch",
        institution_type="PSB",
        state="Rajasthan",
        district="Jaipur",
        latitude=26.8200,
        longitude=75.7800,
        status="active"
    )
    p_missing_coords = Institution(
        id=uuid.uuid4(),
        name="Bank of Baroda - Jaipur Central Branch",
        institution_type="PSB",
        state="Rajasthan",
        district="Jaipur",
        latitude=None,
        longitude=None,
        status="active"
    )
    test_db.add_all([user, scheme, p_with_coords, p_missing_coords])
    test_db.commit()

    app = Application(
        id=uuid.uuid4(), 
        user_id=user.id, 
        scheme_id=scheme.id, 
        status="draft",
        form_data={"latitude": 26.9124, "longitude": 75.7873}
    )
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert len(eligible_partners) == 2
    
    # Partner with coordinates has measured distance
    assert eligible_partners[0].partner_id == p_with_coords.id
    assert eligible_partners[0].distance_km is not None
    assert eligible_partners[0].distance_km > 0.0

    # Partner with missing coordinates has distance_km as None (never fabricated)
    assert eligible_partners[1].partner_id == p_missing_coords.id
    assert eligible_partners[1].distance_km is None
    assert eligible_partners[1].latitude is None
    assert eligible_partners[1].longitude is None


def test_ineligible_nearby_partner_must_not_be_assigned(test_db):
    """An ineligible partner located very close to the applicant must never be assigned or included in candidates."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540064", 
        full_name="Bengaluru User", 
        state="Karnataka", 
        district="Bengaluru Urban",
        is_active=True
    )
    scheme = Scheme(id=uuid.uuid4(), name="Stand-Up India Scheme", ministry="Ministry of Finance", description="Credit", status="active")

    # Ineligible partner right next door (inactive status)
    p_ineligible_inactive = Institution(
        id=uuid.uuid4(),
        name="Suspended Co-op Bank - MG Road",
        institution_type="PSB",
        state="Karnataka",
        district="Bengaluru Urban",
        latitude=12.9720,
        longitude=77.5950,
        status="inactive"
    )
    # Ineligible partner nearby (fails gross NPA threshold)
    p_ineligible_npa = Institution(
        id=uuid.uuid4(),
        name="High NPA Regional Bank - Cubbon Park",
        institution_type="PSB",
        state="Karnataka",
        district="Bengaluru Urban",
        latitude=12.9730,
        longitude=77.5960,
        status="active"
    )
    # Eligible partner farther away (7 km)
    p_eligible_farther = Institution(
        id=uuid.uuid4(),
        name="Canara Bank - Hebbal Branch",
        institution_type="PSB",
        state="Karnataka",
        district="Bengaluru Urban",
        latitude=13.0350,
        longitude=77.5970,
        status="active"
    )
    test_db.add_all([user, scheme, p_ineligible_inactive, p_ineligible_npa, p_eligible_farther])
    test_db.commit()

    banking_map = {
        str(p_ineligible_npa.id): LiveBankingPartnerData(
            partner_id=p_ineligible_npa.id,
            partner_name=p_ineligible_npa.name,
            institution_type="PSB",
            sync_status=BankingDataSyncStatus.LIVE,
            is_authenticated_live=True,
            gross_npa_ratio=Decimal("15.2"),  # Violates 12.0% threshold
            npa_risk_indicator=PartnerNPARiskLevel.ELEVATED,
            available_lending_capacity_inr=Decimal("1000000"),
            is_lending_halted=False
        )
    }

    app = Application(
        id=uuid.uuid4(), 
        user_id=user.id, 
        scheme_id=scheme.id, 
        status="draft",
        form_data={"latitude": 12.9716, "longitude": 77.5946}
    )
    app.scheme = scheme
    app.user = user

    response = service.get_application_partner_routing(app, banking_data=banking_map)

    # Assigned partner must be the eligible one
    assert response.assigned_partner is not None
    assert response.assigned_partner.partner_id == p_eligible_farther.id

    # Ineligible partners must never be in eligible_partners
    candidate_ids = [p.partner_id for p in response.eligible_partners]
    assert p_ineligible_inactive.id not in candidate_ids
    assert p_ineligible_npa.id not in candidate_ids

    # Excluded partners must contain both ineligible partners with transparent reasons
    excluded_ids = [p.partner_id for p in response.excluded_partners]
    assert p_ineligible_inactive.id in excluded_ids
    assert p_ineligible_npa.id in excluded_ids


def test_needs_verification_partner_labeling(test_db):
    """NEEDS_VERIFICATION partners are displayed with proper unverified labeling and never claimed as live verified."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540065", 
        full_name="Bhopal User", 
        state="Madhya Pradesh", 
        district="Bhopal",
        is_active=True
    )
    scheme = Scheme(id=uuid.uuid4(), name="PM Mudra Yojana", ministry="Ministry of Finance", description="Mudra", status="active")

    p_partner = Institution(
        id=uuid.uuid4(),
        name="Madhya Pradesh Gramin Bank - Bhopal",
        institution_type="RRB",
        state="Madhya Pradesh",
        district="Bhopal",
        latitude=23.2599,
        longitude=77.4126,
        status="active"
    )
    test_db.add_all([user, scheme, p_partner])
    test_db.commit()

    app = Application(
        id=uuid.uuid4(), 
        user_id=user.id, 
        scheme_id=scheme.id, 
        status="draft",
        form_data={"latitude": 23.2500, "longitude": 77.4100}
    )
    app.scheme = scheme
    app.user = user

    response = service.get_application_partner_routing(app)
    assert response.assigned_partner is not None
    assert response.assigned_partner.partner_id == p_partner.id
    assert response.assigned_partner.eligibility_verdict == "NEEDS_VERIFICATION"
    assert response.assigned_partner.routing_status == "Awaiting Nodal Banking Verification"
    assert response.assigned_partner.is_authenticated_live is False
    assert response.assigned_partner.distance_km is not None
    assert response.assigned_partner.geographic_tier == "district"
    assert response.total_needs_verification_partners == 1


def test_existing_district_state_national_fallback(test_db):
    """When coordinates are unavailable, District -> State -> National geographic hierarchy is preserved."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540066", 
        full_name="Patna User", 
        state="Bihar", 
        district="Patna",
        is_active=True
    )
    scheme = Scheme(id=uuid.uuid4(), name="PMEGP Scheme", ministry="Ministry of MSME", description="Subsidy", status="active")

    p_district = Institution(id=uuid.uuid4(), name="Patna DIC", institution_type="SCA", state="Bihar", district="Patna", status="active")
    p_state = Institution(id=uuid.uuid4(), name="Gaya SCA", institution_type="SCA", state="Bihar", district="Gaya", status="active")
    p_national = Institution(id=uuid.uuid4(), name="Ranchi SCA", institution_type="SCA", state="Jharkhand", district="Ranchi", status="active")

    test_db.add_all([user, scheme, p_district, p_state, p_national])
    test_db.commit()

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert len(eligible_partners) == 3
    assert eligible_partners[0].partner_id == p_district.id
    assert eligible_partners[0].geographic_tier == "district"
    assert eligible_partners[0].distance_km is None

    assert eligible_partners[1].partner_id == p_state.id
    assert eligible_partners[1].geographic_tier == "state"
    assert eligible_partners[1].distance_km is None

    assert eligible_partners[2].partner_id == p_national.id
    assert eligible_partners[2].geographic_tier == "national"
    assert eligible_partners[2].distance_km is None


def test_preferred_partner_type_ranking(test_db):
    """Within the same geographic proximity tier, preferred partner type is ranked ahead of other eligible types."""
    service = PartnerRoutingService(test_db)
    user = User(
        id=uuid.uuid4(), 
        phone="+919876540067", 
        full_name="Hyderabad User", 
        state="Telangana", 
        district="Hyderabad",
        is_active=True
    )
    # Stand-Up India has preferred_type = "PSB", other eligible = "RRB"
    scheme = Scheme(id=uuid.uuid4(), name="Stand-Up India Scheme", ministry="Ministry of Finance", description="Credit", status="active")

    # Preferred type: PSB
    p_psb = Institution(
        id=uuid.uuid4(),
        name="State Bank of India - Hyderabad Main",
        institution_type="PSB",
        state="Telangana",
        district="Hyderabad",
        status="active"
    )
    # Other eligible type: RRB
    p_rrb = Institution(
        id=uuid.uuid4(),
        name="Telangana Grameena Bank - Hyderabad",
        institution_type="RRB",
        state="Telangana",
        district="Hyderabad",
        status="active"
    )
    test_db.add_all([user, scheme, p_psb, p_rrb])
    test_db.commit()

    app = Application(id=uuid.uuid4(), user_id=user.id, scheme_id=scheme.id, status="draft")
    app.scheme = scheme
    app.user = user

    cat_info, eligible_partners, assigned = service.find_eligible_partners_for_application(app)
    assert len(eligible_partners) == 2
    assert assigned is not None
    assert assigned.partner_id == p_psb.id
    assert assigned.is_preferred is True

    assert eligible_partners[0].partner_id == p_psb.id
    assert eligible_partners[0].is_preferred is True
    assert eligible_partners[1].partner_id == p_rrb.id
    assert eligible_partners[1].is_preferred is False
