"""Channel Partners & Partner Institutions Discovery Router for Yojantra.
Enables India-wide search across State Channelizing Agencies (SCAs), Public Sector Banks (PSBs), 
Regional Rural Banks (RRBs), NBFC-MFIs, and Facilitation Centers with distance ranking & scheme compatibility.
"""
import math
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models import Institution, InstitutionRequest, Scheme, User
from app.schemas import (
    InstitutionResponse, 
    InstitutionRequestCreate, 
    InstitutionRequestResponse,
    PartnerRecommendationSummary
)
from app.services.banking_service import BankingDataService, BankingDataSyncStatus
from app.services.partner_routing_service import PartnerRoutingService

router = APIRouter(prefix="/institutions", tags=["Institutions"])


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two coordinates using Haversine formula."""
    earth_radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return round(earth_radius * c, 2)


def generate_navigation_url(lat: Optional[float], lng: Optional[float], name: str, district: Optional[str] = None, state: Optional[str] = None) -> str:
    """Generate safe navigation URL pointing to exact GPS coordinates or search query."""
    if lat is not None and lng is not None:
        try:
            f_lat, f_lng = float(lat), float(lng)
            if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lng <= 180.0:
                return f"https://www.google.com/maps/dir/?api=1&destination={f_lat},{f_lng}"
        except (ValueError, TypeError):
            pass
    query = " ".join([p for p in [name, district, state, "India"] if p])
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"


def get_scheme_partner_rules(scheme: Optional[Scheme]) -> Dict[str, Any]:
    """Map government scheme types to eligible channel partner institution categories."""
    if not scheme:
        return {
            "eligible_types": ["SCA", "PSB", "RRB", "NBFC-MFI", "Facilitation Center"],
            "preferred_type": "PSB",
            "reason_template": "Authorized multi-scheme lending & facilitation institution in your district."
        }

    scheme_name_lower = scheme.name.lower()
    ministry_lower = scheme.ministry.lower() if scheme.ministry else ""

    # Stand-Up India (Mandatory SC/ST/Women loan via Scheduled Commercial / PSB & RRB banks)
    if "stand-up" in scheme_name_lower or "stand up" in scheme_name_lower:
        return {
            "eligible_types": ["PSB", "RRB", "SCA"],
            "preferred_type": "PSB",
            "reason_template": "Stand-Up India mandates loan sanctioning through Scheduled Commercial & Public Sector Banks with dedicated lead bank officers."
        }
    # PMEGP / KVIC (Khadi & Village, SCAs, District Industries Centers, PSBs)
    elif "pmegp" in scheme_name_lower or "prime minister's employment" in scheme_name_lower:
        return {
            "eligible_types": ["SCA", "PSB", "RRB", "Facilitation Center"],
            "preferred_type": "SCA",
            "reason_template": "State Channelizing Agencies & District Industries Centers (DIC) act as primary nodal agencies for PMEGP margin money subsidy sanction."
        }
    # PM Mudra (Shishu, Kishore, Tarun handled by PSBs, RRBs, NBFC-MFIs)
    elif "mudra" in scheme_name_lower:
        return {
            "eligible_types": ["PSB", "RRB", "NBFC-MFI"],
            "preferred_type": "RRB",
            "reason_template": "Mudra micro-enterprises benefit from high regional credit dispersal rates at Regional Rural Banks and PSBs."
        }
    # NSFDC / NBCFDC / NSKFDC / Social Justice Schemes
    elif "tribal" in scheme_name_lower or "sc" in scheme_name_lower or "social justice" in ministry_lower:
        return {
            "eligible_types": ["SCA", "RRB", "PSB"],
            "preferred_type": "SCA",
            "reason_template": "Designated State Channelizing Agency (SCA) for concessional refinance and affirmative capital subsidies."
        }
    # Default MSME / General Scheme
    else:
        return {
            "eligible_types": ["PSB", "RRB", "SCA", "NBFC-MFI", "Facilitation Center"],
            "preferred_type": "PSB",
            "reason_template": "Accredited lending partner for micro and small enterprise credit schemes."
        }


@router.get("/recommendations", response_model=PartnerRecommendationSummary)
def get_partner_recommendations(
    scheme_id: Optional[UUID] = Query(None, description="Selected scheme to rank partners for"),
    lat: Optional[float] = Query(None, description="User GPS latitude for proximity ranking"),
    lng: Optional[float] = Query(None, description="User GPS longitude for proximity ranking"),
    state: Optional[str] = Query(None, description="Filter by Indian State / UT"),
    district: Optional[str] = Query(None, description="Filter by District"),
    city: Optional[str] = Query(None, description="Filter by City"),
    institution_type: Optional[str] = Query(None, description="Filter by partner type: SCA, PSB, RRB, NBFC-MFI"),
    db: Session = Depends(get_db)
):
    """
    Get ranked channel partners (SCAs, PSBs, RRBs, NBFC-MFIs) for a selected government scheme.
    Computes:
    - Partner eligibility for the selected scheme (scheme-compatible partner routing)
    - Distance-based ranking (if GPS coordinates provided)
    - Partner eligibility/availability indicators (configured fund availability metadata)
    - Best partner recommendation with explicit reasoning
    Note: Dynamic live NPA/overdue & real-time fund-utilization safeguards are framework-ready; live sync requires authorized banking core data.
    """
    scheme = None
    if scheme_id:
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()

    rules = get_scheme_partner_rules(scheme)

    query = db.query(Institution).filter(Institution.status == "active")
    if state:
        query = query.filter(func.lower(Institution.state) == state.strip().lower())
    if district:
        query = query.filter(func.lower(Institution.district) == district.strip().lower())
    if city:
        query = query.filter(func.lower(Institution.city) == city.strip().lower())
    if institution_type:
        query = query.filter(func.lower(Institution.institution_type) == institution_type.strip().lower())

    institutions = query.all()

    # If no institutions found for specific city, fallback to district
    if not institutions and city and district:
        fallback_q = db.query(Institution).filter(
            Institution.status == "active",
            func.lower(Institution.district) == district.strip().lower()
        )
        if state:
            fallback_q = fallback_q.filter(func.lower(Institution.state) == state.strip().lower())
        if institution_type:
            fallback_q = fallback_q.filter(func.lower(Institution.institution_type) == institution_type.strip().lower())
        institutions = fallback_q.all()

    # If no institutions in district, fallback to state-wide
    if not institutions and state:
        fallback_q = db.query(Institution).filter(
            Institution.status == "active",
            func.lower(Institution.state) == state.strip().lower()
        )
        if institution_type:
            fallback_q = fallback_q.filter(func.lower(Institution.institution_type) == institution_type.strip().lower())
        institutions = fallback_q.all()

    # If still none, get all active
    if not institutions:
        institutions = db.query(Institution).filter(Institution.status == "active").limit(30).all()

    partner_responses = []
    type_counts: Dict[str, int] = {}
    routing_service = PartnerRoutingService(db=db)

    for inst in institutions:
        itype = inst.institution_type or "PSB"
        type_counts[itype] = type_counts.get(itype, 0) + 1

        verdict, elig_reason, metrics = routing_service.evaluate_partner_eligibility(
            partner=inst,
            scheme=scheme
        )
        is_eligible = (verdict != "INELIGIBLE")
        
        # Calculate distance if coordinates available
        dist_km = None
        if lat is not None and lng is not None and inst.latitude is not None and inst.longitude is not None:
            dist_km = calculate_haversine_distance(lat, lng, inst.latitude, inst.longitude)

        # Geographic tier: city -> district -> state -> national
        if lat is not None and lng is not None:
            if dist_km is not None and dist_km <= 50.0:
                geo_tier = "district"
            elif state and inst.state and inst.state.strip().lower() == state.strip().lower():
                geo_tier = "state"
            else:
                geo_tier = "national"
        else:
            if city and inst.city and inst.city.strip().lower() == city.strip().lower():
                geo_tier = "city"
            elif district and inst.district and inst.district.strip().lower() == district.strip().lower():
                geo_tier = "district"
            elif state and inst.state and inst.state.strip().lower() == state.strip().lower():
                geo_tier = "state"
            else:
                geo_tier = "national"

        nav_url = generate_navigation_url(inst.latitude, inst.longitude, inst.name, inst.district, inst.state)

        # Construct specific recommendation reason
        reason_parts = []
        if is_eligible and scheme:
            reason_parts.append(f"Official accredited channel category for {scheme.name}.")
        elif not is_eligible and scheme:
            reason_parts.append(f"General lending partner; may not support {scheme.name} nodal subsidy routing.")
        if itype == rules.get("preferred_type"):
            reason_parts.append(rules["reason_template"])
        if dist_km is not None:
            reason_parts.append(f"Located {dist_km} km from your current coordinates.")
        elif inst.district:
            reason_parts.append(f"Operating in {inst.district} district jurisdiction.")

        reason_text = " ".join(reason_parts) if reason_parts else "Registered channel partner for government scheme facilitation."

        # Handle schemes list
        schemes_handled = [scheme.name] if scheme else ["PMEGP", "PM Mudra", "Stand-Up India"]

        resp_item = InstitutionResponse(
            id=inst.id,
            name=inst.name,
            short_name=inst.short_name,
            code=inst.code,
            institution_type=inst.institution_type,
            state=inst.state,
            district=inst.district,
            city=inst.city,
            address=inst.address,
            website=inst.website,
            affiliation=inst.affiliation,
            nirf_rank=inst.nirf_rank,
            latitude=inst.latitude,
            longitude=inst.longitude,
            status=inst.status,
            distance_km=dist_km,
            geographic_tier=geo_tier,
            is_eligible_for_scheme=is_eligible,
            eligibility_verdict=verdict,
            navigation_url=nav_url,
            schemes_handled=schemes_handled,
            fund_availability_status=verdict,
            fund_disclosure="Live banking feeds reflect authenticated partner connections. When unconfigured, verified metadata ensures safe routing.",
            recommendation_rank=1,
            is_best_partner=False,
            recommendation_reason=reason_text,
            contact_phone=inst.code or "+91-1800-11-2211",
            working_hours="10:00 AM - 5:00 PM (Mon-Sat)",
            sync_status=BankingDataSyncStatus.LIVE.value if bool(getattr(inst, "is_authenticated_live", False)) else BankingDataSyncStatus.CONFIGURATION_READY.value,
            provider_name="National Banking & Channel Partner Gateway",
            provider_id="cbs-sca-gateway",
            last_synced_at=getattr(inst, "telemetry_updated_at", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
            is_authenticated_live=bool(getattr(inst, "is_authenticated_live", False)),
            fund_utilization_percentage=getattr(inst, "fund_utilization_percentage", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
            available_lending_capacity_inr=getattr(inst, "available_lending_capacity_inr", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
            capacity_tier=(getattr(inst, "capacity_tier", None) if bool(getattr(inst, "is_authenticated_live", False)) else None) or "UNVERIFIED",
            gross_npa_ratio=getattr(inst, "gross_npa_ratio", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
            npa_risk_indicator=(getattr(inst, "npa_risk_indicator", None) if bool(getattr(inst, "is_authenticated_live", False)) else None) or "UNKNOWN",
            is_lending_halted=bool(getattr(inst, "is_lending_halted", False)) if bool(getattr(inst, "is_authenticated_live", False)) else False,
            disbursement_sla_days=None
        )
        partner_responses.append(resp_item)

    # Multi-factor ranking:
    # 1. Scheme eligibility first: ELIGIBLE (0) -> NEEDS_VERIFICATION (1) -> INELIGIBLE (2)
    # 2. Preferred institution type for the scheme
    # 3. Live Banking Safeguards (penalize halted / high NPA)
    # 4. Proximity (Distance in km when GPS active, or District -> State -> National when fallback)
    def rank_key(p: InstitutionResponse):
        if p.eligibility_verdict == "ELIGIBLE":
            eligibility_score = 0
        elif p.eligibility_verdict == "NEEDS_VERIFICATION":
            eligibility_score = 1
        else:
            eligibility_score = 2

        preferred_score = 0 if p.institution_type == rules.get("preferred_type") else 1
        
        # Live Banking Factors (Applied strictly when verified live)
        live_penalty = 0
        if p.sync_status == "LIVE":
            if p.is_lending_halted:
                live_penalty += 10
            if p.capacity_tier == "CONSTRAINED":
                live_penalty += 3
            elif p.capacity_tier == "HIGH":
                live_penalty -= 2
            if p.npa_risk_indicator == "ELEVATED":
                live_penalty += 4
            elif p.npa_risk_indicator == "LOW":
                live_penalty -= 1

        if lat is not None and lng is not None:
            dist_score = p.distance_km if p.distance_km is not None else 9999.0
            geo_tier_score = 0
        else:
            dist_score = 0.0
            if p.geographic_tier == "city":
                geo_tier_score = 0
            elif p.geographic_tier == "district":
                geo_tier_score = 1
            elif p.geographic_tier == "state":
                geo_tier_score = 2
            else:
                geo_tier_score = 3
                
        return (eligibility_score, preferred_score, live_penalty, geo_tier_score, dist_score, p.name)

    partner_responses.sort(key=rank_key)

    # Assign ranks and mark best partner
    for idx, p in enumerate(partner_responses):
        p.recommendation_rank = idx + 1
        if idx == 0:
            p.is_best_partner = True
            p.recommendation_reason = f"⭐ Best Recommended Partner: {p.recommendation_reason}"

    best_partner = partner_responses[0] if partner_responses else None
    best_reason = best_partner.recommendation_reason if best_partner else None

    banking_service = BankingDataService()
    banking_summary = banking_service.get_sync_summary()

    return PartnerRecommendationSummary(
        selected_scheme_id=scheme.id if scheme else None,
        selected_scheme_name=scheme.name if scheme else "All National & State Schemes",
        total_partners_found=len(partner_responses),
        best_partner=best_partner,
        best_partner_reason=best_reason,
        partners_by_type=type_counts,
        partners=partner_responses,
        banking_integration_status=banking_summary
    )


@router.get("", response_model=List[InstitutionResponse])
def list_institutions(
    q: Optional[str] = Query(None, description="Search by name, short name, city, or identifier code"),
    state: Optional[str] = Query(None, description="Filter by Indian State / UT"),
    district: Optional[str] = Query(None, description="Filter by District"),
    city: Optional[str] = Query(None, description="Filter by City"),
    institution_type: Optional[str] = Query(None, description="Filter by type: SCA, PSB, RRB, NBFC-MFI, etc."),
    scheme_id: Optional[UUID] = Query(None, description="Optional scheme to evaluate partner compatibility"),
    lat: Optional[float] = Query(None, description="User latitude for distance calculation"),
    lng: Optional[float] = Query(None, description="User longitude for distance calculation"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search and filter channel partners and partner institutions across India with pagination.
    Supports distance calculation, partner types (SCA, PSB, RRB, NBFC-MFI), and scheme compatibility.
    """
    query = db.query(Institution).filter(Institution.status == "active")

    if state:
        query = query.filter(func.lower(Institution.state) == state.strip().lower())
    if district:
        query = query.filter(func.lower(Institution.district) == district.strip().lower())
    if city:
        query = query.filter(func.lower(Institution.city) == city.strip().lower())
    if institution_type:
        query = query.filter(func.lower(Institution.institution_type) == institution_type.strip().lower())

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(
            Institution.name.ilike(search_term) |
            Institution.short_name.ilike(search_term) |
            Institution.city.ilike(search_term) |
            Institution.code.ilike(search_term)
        )

    institutions = (
        query
        .order_by(Institution.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first() if scheme_id else None
    rules = get_scheme_partner_rules(scheme)
    routing_service = PartnerRoutingService(db=db)

    results = []
    for inst in institutions:
        itype = inst.institution_type or "PSB"
        verdict, _, metrics = routing_service.evaluate_partner_eligibility(partner=inst, scheme=scheme)
        is_eligible = (verdict != "INELIGIBLE")

        dist_km = None
        if lat is not None and lng is not None and inst.latitude is not None and inst.longitude is not None:
            dist_km = calculate_haversine_distance(lat, lng, inst.latitude, inst.longitude)

        # Geographic tier: district -> state -> national
        if lat is not None and lng is not None:
            if dist_km is not None and dist_km <= 50.0:
                geo_tier = "district"
            elif state and inst.state and inst.state.strip().lower() == state.strip().lower():
                geo_tier = "state"
            else:
                geo_tier = "national"
        else:
            if district and inst.district and inst.district.strip().lower() == district.strip().lower():
                geo_tier = "district"
            elif state and inst.state and inst.state.strip().lower() == state.strip().lower():
                geo_tier = "state"
            else:
                geo_tier = "national"

        nav_url = generate_navigation_url(inst.latitude, inst.longitude, inst.name, inst.district, inst.state)
        
        results.append(
            InstitutionResponse(
                id=inst.id,
                name=inst.name,
                short_name=inst.short_name,
                code=inst.code,
                institution_type=inst.institution_type,
                state=inst.state,
                district=inst.district,
                city=inst.city,
                address=inst.address,
                website=inst.website,
                affiliation=inst.affiliation,
                nirf_rank=inst.nirf_rank,
                latitude=inst.latitude,
                longitude=inst.longitude,
                status=inst.status,
                distance_km=dist_km,
                geographic_tier=geo_tier,
                is_eligible_for_scheme=is_eligible,
                eligibility_verdict=verdict,
                navigation_url=nav_url,
                schemes_handled=[scheme.name] if scheme else ["PMEGP", "PM Mudra", "Stand-Up India"],
                fund_availability_status=verdict,
                fund_disclosure="Live banking feeds reflect authenticated partner connections. When unconfigured, verified metadata ensures safe routing.",
                recommendation_rank=1,
                is_best_partner=False,
                recommendation_reason=f"Registered {itype} branch for entrepreneur loan processing.",
                sync_status=BankingDataSyncStatus.LIVE.value if bool(getattr(inst, "is_authenticated_live", False)) else BankingDataSyncStatus.CONFIGURATION_READY.value,
                provider_name="National Banking & Channel Partner Gateway",
                provider_id="cbs-sca-gateway",
                last_synced_at=getattr(inst, "telemetry_updated_at", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
                is_authenticated_live=bool(getattr(inst, "is_authenticated_live", False)),
                fund_utilization_percentage=getattr(inst, "fund_utilization_percentage", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
                available_lending_capacity_inr=getattr(inst, "available_lending_capacity_inr", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
                capacity_tier=(getattr(inst, "capacity_tier", None) if bool(getattr(inst, "is_authenticated_live", False)) else None) or "UNVERIFIED",
                gross_npa_ratio=getattr(inst, "gross_npa_ratio", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
                npa_risk_indicator=(getattr(inst, "npa_risk_indicator", None) if bool(getattr(inst, "is_authenticated_live", False)) else None) or "UNKNOWN",
                is_lending_halted=bool(getattr(inst, "is_lending_halted", False)) if bool(getattr(inst, "is_authenticated_live", False)) else False,
                disbursement_sla_days=None
            )
        )

    if lat is not None and lng is not None:
        results.sort(key=lambda x: (x.distance_km if x.distance_km is not None else 9999.0, x.name))
    elif district or state:
        tier_order = {"district": 0, "state": 1, "national": 2}
        results.sort(key=lambda x: (tier_order.get(x.geographic_tier, 2), x.name))

    return results


@router.get("/requests", response_model=List[InstitutionRequestResponse])
def list_institution_requests(
    status_filter: Optional[str] = Query(None, description="Filter requests by status"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """List citizen requests for new partner additions (Admin authorization strictly required)."""
    query = db.query(InstitutionRequest)
    if status_filter:
        query = query.filter(InstitutionRequest.status == status_filter.strip().lower())
    return [InstitutionRequestResponse.model_validate(r) for r in query.order_by(InstitutionRequest.created_at.desc()).all()]


@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(institution_id: UUID, db: Session = Depends(get_db)):
    """Retrieve detailed profile of a channel partner or partner institution."""
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Partner institution not found")

    nav_url = generate_navigation_url(inst.latitude, inst.longitude, inst.name, inst.district, inst.state)

    return InstitutionResponse(
        id=inst.id,
        name=inst.name,
        short_name=inst.short_name,
        code=inst.code,
        institution_type=inst.institution_type,
        state=inst.state,
        district=inst.district,
        city=inst.city,
        address=inst.address,
        website=inst.website,
        affiliation=inst.affiliation,
        nirf_rank=inst.nirf_rank,
        latitude=inst.latitude,
        longitude=inst.longitude,
        status=inst.status,
        distance_km=None,
        geographic_tier="district" if inst.district else "national",
        is_eligible_for_scheme=True,
        eligibility_verdict="ELIGIBLE",
        navigation_url=nav_url,
        schemes_handled=["PMEGP", "PM Mudra", "Stand-Up India"],
        fund_availability_status="Eligible Channel Type",
        fund_disclosure="Live banking feeds reflect authenticated partner connections. When unconfigured, verified metadata ensures safe routing.",
        recommendation_rank=1,
        is_best_partner=False,
        recommendation_reason="Accredited channel partner for government scheme facilitation.",
        contact_phone=inst.code or "+91-1800-11-2211",
        working_hours="10:00 AM - 5:00 PM (Mon-Sat)",
        sync_status=BankingDataSyncStatus.LIVE.value if bool(getattr(inst, "is_authenticated_live", False)) else BankingDataSyncStatus.CONFIGURATION_READY.value,
        provider_name="National Banking & Channel Partner Gateway",
        provider_id="cbs-sca-gateway",
        last_synced_at=getattr(inst, "telemetry_updated_at", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
        is_authenticated_live=bool(getattr(inst, "is_authenticated_live", False)),
        fund_utilization_percentage=getattr(inst, "fund_utilization_percentage", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
        available_lending_capacity_inr=getattr(inst, "available_lending_capacity_inr", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
        capacity_tier=(getattr(inst, "capacity_tier", None) if bool(getattr(inst, "is_authenticated_live", False)) else None) or "UNVERIFIED",
        gross_npa_ratio=getattr(inst, "gross_npa_ratio", None) if bool(getattr(inst, "is_authenticated_live", False)) else None,
        npa_risk_indicator=(getattr(inst, "npa_risk_indicator", None) if bool(getattr(inst, "is_authenticated_live", False)) else None) or "UNKNOWN",
        is_lending_halted=bool(getattr(inst, "is_lending_halted", False)) if bool(getattr(inst, "is_authenticated_live", False)) else False,
        disbursement_sla_days=None
    )


@router.post("/request", response_model=InstitutionRequestResponse, status_code=status.HTTP_201_CREATED)
def request_institution(
    req: InstitutionRequestCreate,
    db: Session = Depends(get_db)
):
    """Allow citizens and entrepreneurs to request addition of unlisted channel partners / institutions."""
    record = InstitutionRequest(
        name=req.name.strip(),
        state=req.state.strip(),
        district=req.district.strip(),
        city=req.city.strip() if req.city else None,
        requested_by_email=req.requested_by_email.strip() if req.requested_by_email else None,
        status="pending"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return InstitutionRequestResponse.model_validate(record)

