"""Regression tests for Part 7: Geo-Spatial Channel Partner Locator.

Validates:
- Precise Haversine distance calculation and sorting by GPS proximity
- District / State / National geographic fallback hierarchy when GPS is unavailable
- Scheme category compatibility and eligibility filtering
- Real banking telemetry (NPA ratio, risk indicator, capacity tier, verification badges) without faking data
- Navigation URL generation for both GPS and non-GPS partners
- Authorization checks: citizen request creation vs strict admin access for partner requests
"""
import pytest
import uuid
from decimal import Decimal

from app.models import User, Institution, InstitutionRequest, Scheme
from app.core.security import create_access_token
from app.services.partner_routing_service import PartnerRoutingService
from app.services.banking_service import (
    LiveBankingPartnerData,
    BankingDataSyncStatus,
    PartnerCapacityTier,
    PartnerNPARiskLevel
)


@pytest.fixture
def auth_users(test_db):
    citizen = User(
        id=uuid.uuid4(),
        phone="+919811111111",
        email="citizen@yojantra.in",
        full_name="Ramesh Kumar",
        role="user",
        state="Maharashtra",
        district="Pune"
    )
    admin = User(
        id=uuid.uuid4(),
        phone="+919899999999",
        email="admin@yojantra.in",
        full_name="System Admin",
        role="admin",
        state="Delhi",
        district="New Delhi"
    )
    test_db.add_all([citizen, admin])
    test_db.commit()

    token_citizen = create_access_token({"sub": str(citizen.id), "phone": citizen.phone, "role": citizen.role})
    token_admin = create_access_token({"sub": str(admin.id), "phone": admin.phone, "role": admin.role})

    return {
        "citizen": citizen,
        "admin": admin,
        "headers_citizen": {"Authorization": f"Bearer {token_citizen}"},
        "headers_admin": {"Authorization": f"Bearer {token_admin}"},
    }


@pytest.fixture
def geo_partners(test_db):
    """Accredited channel partners in Maharashtra and national hubs with verified real coordinates."""
    # 1. Partner in Pune (~0 km from Pune center: 18.5204, 73.8567)
    p_pune = Institution(
        id=uuid.uuid4(),
        name="State Bank of India - Pune Main Branch",
        short_name="SBI Pune",
        code="SBIN0000454",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        address="Collector Office Compound, Pune",
        latitude=18.5204,
        longitude=73.8567,
        status="active"
    )
    p_pune.gross_npa_ratio = Decimal("3.80")
    p_pune.capacity_tier = "HIGH"
    p_pune.npa_risk_indicator = "LOW"

    # 2. Partner in Mumbai (~120 km from Pune: 18.9220, 72.8347)
    p_mumbai = Institution(
        id=uuid.uuid4(),
        name="Maharashtra State Channelizing Agency - Mumbai HQ",
        short_name="MSCA Mumbai",
        code="MSCA0001",
        institution_type="SCA",
        state="Maharashtra",
        district="Mumbai",
        city="Mumbai",
        address="Nariman Point, Mumbai",
        latitude=18.9220,
        longitude=72.8347,
        status="active"
    )
    p_mumbai.capacity_tier = "MODERATE"

    # 3. Partner in Nagpur (~620 km from Pune: 21.1458, 79.0882)
    p_nagpur = Institution(
        id=uuid.uuid4(),
        name="Vidharbha Konkan Gramin Bank - Nagpur",
        short_name="VKGB Nagpur",
        code="VKGB00021",
        institution_type="RRB",
        state="Maharashtra",
        district="Nagpur",
        city="Nagpur",
        address="Civil Lines, Nagpur",
        latitude=21.1458,
        longitude=79.0882,
        status="active"
    )

    # 4. Partner with missing GPS coordinates in Pune district
    p_no_coords = Institution(
        id=uuid.uuid4(),
        name="Baramati Taluka Cooperative Lead Cell",
        short_name="Baramati Cell",
        code="BARA001",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        city="Baramati",
        address="Baramati MIDC",
        latitude=None,
        longitude=None,
        status="active"
    )

    # 5. Partner in another state (Delhi)
    p_delhi = Institution(
        id=uuid.uuid4(),
        name="Punjab National Bank - Delhi Connaught Place",
        short_name="PNB Delhi",
        code="PUNB00011",
        institution_type="PSB",
        state="Delhi",
        district="New Delhi",
        city="New Delhi",
        address="Connaught Place, New Delhi",
        latitude=28.6315,
        longitude=77.2167,
        status="active"
    )

    test_db.add_all([p_pune, p_mumbai, p_nagpur, p_no_coords, p_delhi])
    test_db.commit()

    return {
        "pune": p_pune,
        "mumbai": p_mumbai,
        "nagpur": p_nagpur,
        "no_coords": p_no_coords,
        "delhi": p_delhi
    }


# ==================== TEST SUITE ====================

def test_geospatial_distance_calculation_and_sorting(client, geo_partners):
    """Verify that GPS coordinates trigger accurate Haversine distance calculation and sort nearest-first."""
    # User coordinates at Pune Center (18.5204, 73.8567)
    user_lat = 18.5204
    user_lng = 73.8567

    response = client.get(f"/institutions?lat={user_lat}&lng={user_lng}")
    assert response.status_code == 200
    partners = response.json()
    assert len(partners) >= 4

    # 1. Partner in Pune must be closest (~0 km)
    first = partners[0]
    assert first["id"] == str(geo_partners["pune"].id)
    assert first["distance_km"] is not None
    assert first["distance_km"] < 1.0  # < 1 km from origin
    assert first["geographic_tier"] == "district"
    assert "https://www.google.com/maps/dir/" in first["navigation_url"]
    assert "18.5204,73.8567" in first["navigation_url"]

    # 2. Partner in Mumbai (~120 km) must precede Nagpur (~620 km)
    mumbai_partner = next(p for p in partners if p["id"] == str(geo_partners["mumbai"].id))
    nagpur_partner = next(p for p in partners if p["id"] == str(geo_partners["nagpur"].id))
    assert mumbai_partner["distance_km"] < nagpur_partner["distance_km"]
    assert 100.0 < mumbai_partner["distance_km"] < 150.0
    assert 600.0 < nagpur_partner["distance_km"] < 700.0

    # 3. Partner with missing coordinates must have distance_km == None and sort after mapped partners
    no_coords_partner = next(p for p in partners if p["id"] == str(geo_partners["no_coords"].id))
    assert no_coords_partner["distance_km"] is None
    # Verify navigation URL falls back safely to search
    assert "https://www.google.com/maps/search/" in no_coords_partner["navigation_url"]


def test_geospatial_location_fallback_without_gps(client, geo_partners):
    """Verify that when GPS is unavailable, locator gracefully falls back to District -> State -> National hierarchy."""
    # No lat/lng provided, only administrative jurisdiction (District: Pune, State: Maharashtra)
    response = client.get("/institutions?district=Pune&state=Maharashtra")
    assert response.status_code == 200
    partners = response.json()

    # In Pune district, both p_pune and p_no_coords are in district tier
    pune_ids = {str(geo_partners["pune"].id), str(geo_partners["no_coords"].id)}
    assert len(partners) >= 2
    for p in partners:
        assert p["id"] in pune_ids
        assert p["geographic_tier"] == "district"
        assert p["district"] == "Pune"
        # Since GPS was not provided, distance_km must remain None (never fake coordinates!)
        assert p["distance_km"] is None

    # Now query for partner recommendations with state-level fallback
    rec_resp = client.get("/institutions/recommendations?district=Pune&state=Maharashtra")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["best_partner"] is not None
    assert rec_data["best_partner"]["district"] == "Pune"
    assert rec_data["best_partner"]["geographic_tier"] == "district"


def test_partner_scheme_compatibility_and_eligibility_filtering(test_db, client, geo_partners):
    """Verify that scheme-specific partner category compatibility correctly updates eligibility badges."""
    # Create Stand-Up India scheme requiring SCB / PSB / RRB / SCA
    stand_up_scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Facility",
        ministry="Ministry of Finance",
        description="Composite loans for SC/ST and Women via commercial banks and SCAs",
        scheme_type="credit_guarantee",
        status="active"
    )
    # Create incompatible partner type
    incompatible_partner = Institution(
        id=uuid.uuid4(),
        name="General Tech Skill Lab",
        short_name="GTSL",
        institution_type="Unaccredited Entity",
        state="Maharashtra",
        district="Pune",
        status="active"
    )
    # Create inactive partner
    inactive_partner = Institution(
        id=uuid.uuid4(),
        name="De-registered Micro Cell",
        short_name="DMC",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        status="inactive"
    )
    test_db.add_all([stand_up_scheme, incompatible_partner, inactive_partner])
    test_db.commit()

    # Query recommendations for Stand-Up India
    response = client.get(f"/institutions/recommendations?scheme_id={stand_up_scheme.id}&district=Pune&state=Maharashtra")
    assert response.status_code == 200
    data = response.json()

    # Compatible partners (PSB, SCA, RRB) must be marked as ELIGIBLE or NEEDS_VERIFICATION
    p_sbi = next(p for p in data["partners"] if p["id"] == str(geo_partners["pune"].id))
    assert p_sbi["is_eligible_for_scheme"] is True
    assert p_sbi["eligibility_verdict"] in ["ELIGIBLE", "NEEDS_VERIFICATION"]

    # Incompatible partner must be marked as INELIGIBLE and ranked lower
    p_incomp = next(p for p in data["partners"] if p["id"] == str(incompatible_partner.id))
    assert p_incomp["is_eligible_for_scheme"] is False
    assert p_incomp["eligibility_verdict"] == "INELIGIBLE"
    assert p_incomp["recommendation_rank"] > p_sbi["recommendation_rank"]


def test_partner_banking_and_npa_telemetry_preservation(client, test_db, geo_partners):
    """Verify real NPA ratio, risk indicators, and capacity tiers are preserved without synthetic data."""
    # 1. Verification of endpoint response: Unconfigured partner must NOT have fake banking metrics
    response = client.get(f"/institutions/{geo_partners['pune'].id}")
    assert response.status_code == 200
    partner = response.json()

    # Never fabricate banking data when CBS is not authenticated
    assert partner["gross_npa_ratio"] is None
    assert partner["capacity_tier"] == "UNVERIFIED"
    assert partner["npa_risk_indicator"] == "UNKNOWN"
    assert partner["sync_status"] == "CONFIGURATION_READY"
    assert partner["is_authenticated_live"] is False
    assert "Live banking feeds" in partner["fund_disclosure"]

    # Baramati Cell also has unverified telemetry without fabricated data
    resp_unverified = client.get(f"/institutions/{geo_partners['no_coords'].id}")
    assert resp_unverified.status_code == 200
    part_unver = resp_unverified.json()

    assert part_unver["gross_npa_ratio"] is None
    assert part_unver["capacity_tier"] == "UNVERIFIED"
    assert part_unver["npa_risk_indicator"] == "UNKNOWN"

    # 2. Service level verification with LiveBankingPartnerData:
    routing_service = PartnerRoutingService(db=test_db)
    
    # Unconfigured banking data must return NEEDS_VERIFICATION without faking eligibility
    verdict, reason, metrics = routing_service.evaluate_partner_eligibility(
        partner=geo_partners["no_coords"],
        banking_data=None
    )
    assert verdict == "NEEDS_VERIFICATION"
    assert metrics["gross_npa_ratio"] is None
    assert metrics["npa_risk_indicator"] == "UNKNOWN"

    # Verified live healthy banking data returns ELIGIBLE
    healthy_live = LiveBankingPartnerData(
        partner_id=geo_partners["pune"].id,
        partner_name="State Bank of India - Pune Main Branch",
        institution_type="PSB",
        sync_status=BankingDataSyncStatus.LIVE,
        is_authenticated_live=True,
        gross_npa_ratio=Decimal("3.80"),
        capacity_tier=PartnerCapacityTier.HIGH,
        npa_risk_indicator=PartnerNPARiskLevel.LOW
    )
    v_healthy, r_healthy, m_healthy = routing_service.evaluate_partner_eligibility(
        partner=geo_partners["pune"],
        banking_data=healthy_live
    )
    assert v_healthy == "ELIGIBLE"
    assert m_healthy["gross_npa_ratio"] == Decimal("3.80")
    assert m_healthy["capacity_tier"] == "HIGH"

    # Verified live banking data exceeding NPA threshold (>12.0%) returns INELIGIBLE
    violating_live = LiveBankingPartnerData(
        partner_id=geo_partners["pune"].id,
        partner_name="State Bank of India - Pune Main Branch",
        institution_type="PSB",
        sync_status=BankingDataSyncStatus.LIVE,
        is_authenticated_live=True,
        gross_npa_ratio=Decimal("15.20"),
        capacity_tier=PartnerCapacityTier.CONSTRAINED,
        npa_risk_indicator=PartnerNPARiskLevel.ELEVATED
    )
    v_violating, r_violating, m_violating = routing_service.evaluate_partner_eligibility(
        partner=geo_partners["pune"],
        banking_data=violating_live
    )
    assert v_violating == "INELIGIBLE"
    assert "exceeds the maximum eligibility threshold" in r_violating


def test_partner_request_creation_and_admin_authorization(client, auth_users):
    """Verify public citizen request submission vs strictly protected admin listing."""
    # 1. Citizen submits a partner addition request (Public / Citizen allowed)
    req_payload = {
        "name": "District Rural Development Facilitation Center",
        "state": "Maharashtra",
        "district": "Pune",
        "city": "Shirur",
        "requested_by_email": "citizen@yojantra.in"
    }
    create_resp = client.post("/institutions/request", json=req_payload)
    assert create_resp.status_code == 201
    req_data = create_resp.json()
    assert req_data["name"] == "District Rural Development Facilitation Center"
    assert req_data["status"] == "pending"

    # 2. Unauthenticated user accessing admin requests list is rejected (401)
    get_unauth = client.get("/institutions/requests")
    assert get_unauth.status_code == 401

    # 3. Regular citizen user accessing admin requests list is rejected (403 Forbidden)
    get_citizen = client.get("/institutions/requests", headers=auth_users["headers_citizen"])
    assert get_citizen.status_code == 403

    # 4. Authorized admin user accessing admin requests list succeeds (200 OK)
    get_admin = client.get("/institutions/requests", headers=auth_users["headers_admin"])
    assert get_admin.status_code == 200
    reqs_list = get_admin.json()
    assert len(reqs_list) >= 1
    assert any(r["name"] == "District Rural Development Facilitation Center" for r in reqs_list)
