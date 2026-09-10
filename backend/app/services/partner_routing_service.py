"""Channel Partner digital routing service for Yojantra.
Identifies and filters accredited channel partners (SCAs, PSBs, RRBs, NBFC-MFIs, Facilitation Centers)
based on scheme category, beneficiary geography, institutional compatibility, active status,
and verified core-banking / risk telemetry safeguards.
"""
from datetime import datetime, timezone
from decimal import Decimal
import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Application, Scheme, Institution, User
from app.schemas import ApplicationPartnerRoutingItem, ApplicationPartnerRoutingResponse
from app.services.banking_service import (
    BankingDataService, 
    LiveBankingPartnerData, 
    BankingDataSyncStatus,
    PartnerCapacityTier,
    PartnerNPARiskLevel
)

logger = logging.getLogger(__name__)

# Configured threshold for maximum gross NPA ratio for eligible lending partners (12.0%)
MAX_ELIGIBLE_GROSS_NPA_RATIO: Decimal = Decimal("12.0")


# Scheme category routing rules and supported channel partner types
SCHEME_CATEGORY_RULES: Dict[str, Dict[str, Any]] = {
    "STAND_UP": {
        "category_code": "STAND_UP",
        "category_label": "Stand-Up India Enterprise Credit (SC/ST/Women)",
        "eligible_types": ["PSB", "RRB", "SCA", "Public Sector Bank", "Regional Rural Bank", "State Channelizing Agency"],
        "preferred_type": "PSB",
        "routing_note": "Stand-Up India mandates credit sanction through Scheduled Commercial Banks (PSBs/RRBs) and SCAs with lead district bank officers.",
        "partner_reason": "Designated Scheduled Commercial Bank / Lead Bank for Stand-Up India credit facility."
    },
    "PMEGP": {
        "category_code": "PMEGP",
        "category_label": "PMEGP Margin Money Subsidy & Micro-Enterprise Credit",
        "eligible_types": ["SCA", "PSB", "RRB", "Facilitation Center", "State Channelizing Agency", "Public Sector Bank", "Regional Rural Bank"],
        "preferred_type": "SCA",
        "routing_note": "State Channelizing Agencies (SCAs) & District Industries Centers (DIC) act as primary nodal agencies for PMEGP margin money sanction.",
        "partner_reason": "Nodal State Channelizing Agency / DIC center for PMEGP margin money subsidy appraisal."
    },
    "MUDRA": {
        "category_code": "MUDRA",
        "category_label": "PM Mudra Micro-Credit (Shishu / Kishore / Tarun)",
        "eligible_types": ["PSB", "RRB", "NBFC-MFI", "Public Sector Bank", "Regional Rural Bank"],
        "preferred_type": "RRB",
        "routing_note": "Mudra micro-credit is routed via Regional Rural Banks, Public Sector Banks, and accredited MFIs with regional outreach.",
        "partner_reason": "Accredited Mudra lending institution with micro-enterprise credit delivery facility."
    },
    "SVANIDHI": {
        "category_code": "SVANIDHI",
        "category_label": "PM SVANidhi Urban Micro-Credit & Working Capital",
        "eligible_types": ["PSB", "RRB", "NBFC-MFI", "Facilitation Center", "Public Sector Bank", "Regional Rural Bank"],
        "preferred_type": "PSB",
        "routing_note": "Urban micro-credit routed through designated lead commercial banks and municipal facilitation centers.",
        "partner_reason": "Urban micro-credit lending partner for working capital term loans."
    },
    "AFFIRMATIVE_SCA": {
        "category_code": "AFFIRMATIVE_SCA",
        "category_label": "Concessional Refinance & Affirmative Capital (SC/ST/OBC/Tribal/Minority)",
        "eligible_types": ["SCA", "RRB", "PSB", "State Channelizing Agency", "Regional Rural Bank", "Public Sector Bank"],
        "preferred_type": "SCA",
        "routing_note": "Designated State Channelizing Agency (SCA) for concessional refinance and affirmative capital subsidies.",
        "partner_reason": "Designated State Channelizing Agency (SCA) for affirmative action lending."
    },
    "TECH_GRANT": {
        "category_code": "TECH_GRANT",
        "category_label": "Technology Development, Incubation & Enterprise Grant",
        "eligible_types": [
            "Autonomous", "Facilitation Center", "PSB", "SCA", 
            "IIT / Institute of National Importance", 
            "NIT / Institute of National Importance", 
            "Autonomous Govt-Aided College",
            "Autonomous Private Engineering College",
            "State University",
            "Deemed to be University"
        ],
        "preferred_type": "Facilitation Center",
        "routing_note": "Routed via MSME Technology Development Facilitation Centers and accredited academic incubation hubs.",
        "partner_reason": "Accredited technical development & incubation partner for enterprise grant programs."
    },
    "GENERAL_MSME": {
        "category_code": "GENERAL_MSME",
        "category_label": "General MSME Credit & Lending Facility",
        "eligible_types": ["PSB", "RRB", "SCA", "NBFC-MFI", "Facilitation Center", "Public Sector Bank", "Regional Rural Bank", "State Channelizing Agency"],
        "preferred_type": "PSB",
        "routing_note": "Accredited lending partner for micro and small enterprise credit schemes.",
        "partner_reason": "Accredited financial channel partner for MSME credit schemes."
    }
}


class PartnerRoutingService:
    """Service to classify schemes, filter by eligibility, rank Channel Partners, and prepare application routing."""

    def __init__(
        self, 
        db: Session,
        banking_service: Optional[BankingDataService] = None,
        max_npa_threshold: Decimal = MAX_ELIGIBLE_GROSS_NPA_RATIO
    ):
        self.db = db
        self.banking_service = banking_service or BankingDataService()
        self.max_npa_threshold = max_npa_threshold

    def determine_scheme_category(self, scheme: Optional[Scheme]) -> Dict[str, Any]:
        """Determine scheme/loan category and routing rules for a given scheme."""
        if not scheme:
            return SCHEME_CATEGORY_RULES["GENERAL_MSME"]

        name_lower = (scheme.name or "").lower()
        ministry_lower = (scheme.ministry or "").lower()
        scheme_type_lower = (scheme.scheme_type or "").lower()

        # 1. Stand-Up India
        if "stand-up" in name_lower or "stand up" in name_lower:
            return SCHEME_CATEGORY_RULES["STAND_UP"]

        # 2. PMEGP
        if "pmegp" in name_lower or "prime minister's employment generation" in name_lower or "khadi" in name_lower:
            return SCHEME_CATEGORY_RULES["PMEGP"]

        # 3. PM Mudra
        if "mudra" in name_lower:
            return SCHEME_CATEGORY_RULES["MUDRA"]

        # 4. PM SVANidhi
        if "svanidhi" in name_lower or "street vendor" in name_lower:
            return SCHEME_CATEGORY_RULES["SVANIDHI"]

        # 5. Affirmative action SCAs (SC, ST, OBC, Tribal, Minority)
        if any(term in name_lower for term in ["tribal", "safai karamchari", "nsfdc", "nbcfdc", "nskfdc", "backward classes"]) or \
           any(term in ministry_lower for term in ["social justice", "tribal affairs", "minority affairs"]):
            return SCHEME_CATEGORY_RULES["AFFIRMATIVE_SCA"]

        # 6. Technology Grants / Incubation / R&D
        if any(term in name_lower for term in ["aspire", "tread", "incubator", "incubation", "clcss", "design clinic", "lean manufacturing", "ramap"]) or \
           scheme_type_lower == "grant":
            return SCHEME_CATEGORY_RULES["TECH_GRANT"]

        # 7. Default General MSME
        return SCHEME_CATEGORY_RULES["GENERAL_MSME"]

    def evaluate_partner_eligibility(
        self,
        partner: Institution,
        scheme: Optional[Scheme] = None,
        user: Optional[User] = None,
        banking_data: Optional[Any] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Evaluate a single channel partner's eligibility for an application/scheme.
        
        Returns:
            (verdict, reason, metrics_meta)
            where verdict is one of 'ELIGIBLE', 'INELIGIBLE', or 'NEEDS_VERIFICATION'.
        """
        category_info = self.determine_scheme_category(scheme)
        eligible_type_strings = [t.lower() for t in category_info["eligible_types"]]

        # 1. Active / Inactive Partner Check
        partner_status = (partner.status or "").strip().lower()
        if partner_status != "active":
            return (
                "INELIGIBLE",
                f"Partner operational status is '{partner.status or 'inactive'}'; excluded from accepting scheme applications.",
                {"partner_status": partner.status}
            )

        # 2. Scheme / Category Compatibility Check
        inst_type = (partner.institution_type or "").strip().lower()
        if not inst_type:
            return (
                "INELIGIBLE",
                f"Partner institution type is unspecified; incompatible with scheme category '{category_info['category_label']}'.",
                {"institution_type": None}
            )

        is_compatible = any(etype in inst_type or inst_type in etype for etype in eligible_type_strings)
        if not is_compatible:
            return (
                "INELIGIBLE",
                f"Partner type '{partner.institution_type}' is incompatible with {category_info['category_label']}.",
                {"institution_type": partner.institution_type}
            )

        # 3. Geographic Eligibility Check
        if scheme and scheme.applicable_states:
            applicable = [s.strip().lower() for s in scheme.applicable_states]
            partner_state = (partner.state or "").strip().lower()
            if partner_state and partner_state not in applicable:
                return (
                    "INELIGIBLE",
                    f"Partner location in '{partner.state}' is outside scheme applicable states ({', '.join(scheme.applicable_states)}).",
                    {"partner_state": partner.state, "applicable_states": scheme.applicable_states}
                )

        # 4. Extract verified banking telemetry from banking_data or model attributes
        b_data = banking_data
        if isinstance(b_data, dict):
            pid_str = str(partner.id)
            if pid_str in b_data:
                b_data = b_data[pid_str]
            elif partner.id in b_data:
                b_data = b_data[partner.id]
            elif partner.code and partner.code in b_data:
                b_data = b_data[partner.code]

        is_live = False
        is_halted = False
        gross_npa: Optional[Decimal] = None
        npa_risk = "UNKNOWN"
        avail_capacity: Optional[Decimal] = None
        fund_util: Optional[Decimal] = None
        cap_tier = "UNVERIFIED"
        sync_status = BankingDataSyncStatus.CONFIGURATION_READY.value

        if isinstance(b_data, LiveBankingPartnerData):
            is_live = b_data.is_authenticated_live
            is_halted = b_data.is_lending_halted
            gross_npa = b_data.gross_npa_ratio
            npa_risk = b_data.npa_risk_indicator.value if hasattr(b_data.npa_risk_indicator, "value") else str(b_data.npa_risk_indicator)
            avail_capacity = b_data.available_lending_capacity_inr
            fund_util = b_data.fund_utilization_percentage
            cap_tier = b_data.capacity_tier.value if hasattr(b_data.capacity_tier, "value") else str(b_data.capacity_tier)
            sync_status = b_data.sync_status.value if hasattr(b_data.sync_status, "value") else str(b_data.sync_status)
        elif isinstance(b_data, dict):
            is_live = bool(b_data.get("is_authenticated_live", False))
            is_halted = bool(b_data.get("is_lending_halted", False))
            gross_npa = Decimal(str(b_data["gross_npa_ratio"])) if b_data.get("gross_npa_ratio") is not None else None
            npa_risk = str(b_data.get("npa_risk_indicator", "UNKNOWN"))
            avail_capacity = Decimal(str(b_data["available_lending_capacity_inr"])) if b_data.get("available_lending_capacity_inr") is not None else None
            fund_util = Decimal(str(b_data["fund_utilization_percentage"])) if b_data.get("fund_utilization_percentage") is not None else None
            cap_tier = str(b_data.get("capacity_tier", "UNVERIFIED"))
            sync_status = str(b_data.get("sync_status", BankingDataSyncStatus.LIVE.value if is_live else BankingDataSyncStatus.CONFIGURATION_READY.value))
        else:
            # Check if attributes attached to partner model instance
            if hasattr(partner, "is_authenticated_live"):
                is_live = bool(partner.is_authenticated_live)
            if hasattr(partner, "is_lending_halted") and partner.is_lending_halted is not None:
                is_halted = bool(partner.is_lending_halted)
            if hasattr(partner, "gross_npa_ratio") and partner.gross_npa_ratio is not None:
                gross_npa = Decimal(str(partner.gross_npa_ratio))
            if hasattr(partner, "npa_risk_indicator") and partner.npa_risk_indicator is not None:
                npa_risk = str(partner.npa_risk_indicator)
            if hasattr(partner, "available_lending_capacity_inr") and partner.available_lending_capacity_inr is not None:
                avail_capacity = Decimal(str(partner.available_lending_capacity_inr))
            if hasattr(partner, "fund_utilization_percentage") and partner.fund_utilization_percentage is not None:
                fund_util = Decimal(str(partner.fund_utilization_percentage))
            if hasattr(partner, "capacity_tier") and partner.capacity_tier is not None:
                cap_tier = str(partner.capacity_tier)
            if hasattr(partner, "sync_status") and partner.sync_status is not None:
                sync_status = str(partner.sync_status)
            elif is_live:
                sync_status = BankingDataSyncStatus.LIVE.value

        metrics_meta = {
            "sync_status": sync_status,
            "is_authenticated_live": is_live,
            "gross_npa_ratio": gross_npa,
            "npa_risk_indicator": npa_risk,
            "available_lending_capacity_inr": avail_capacity,
            "fund_utilization_percentage": fund_util,
            "capacity_tier": cap_tier,
            "is_lending_halted": is_halted
        }

        # 5. Verified Live Banking & Capacity / NPA Safeguards
        if is_halted:
            return (
                "INELIGIBLE",
                "Partner credit facility is halted by lead banking regulator or nodal monitoring committee.",
                metrics_meta
            )

        if gross_npa is not None:
            if gross_npa > self.max_npa_threshold:
                return (
                    "INELIGIBLE",
                    f"Partner gross NPA ratio of {gross_npa}% exceeds the maximum eligibility threshold ({self.max_npa_threshold}%).",
                    metrics_meta
                )

        if str(npa_risk).upper() == "ELEVATED":
            return (
                "INELIGIBLE",
                "Partner exhibits elevated NPA risk tier under verified banking telemetry.",
                metrics_meta
            )

        if avail_capacity is not None and avail_capacity <= Decimal("0"):
            return (
                "INELIGIBLE",
                "Partner has zero remaining lending quota capacity under verified scheme allocation.",
                metrics_meta
            )

        if fund_util is not None and fund_util >= Decimal("100.0"):
            return (
                "INELIGIBLE",
                "Partner fund utilization has reached 100% allocation ceiling.",
                metrics_meta
            )

        # If verified live data was provided and passed all risk/capacity checks:
        if is_live:
            npa_str = f"{gross_npa}%" if gross_npa is not None else "healthy"
            return (
                "ELIGIBLE",
                f"Partner is active, compatible, and verified live with gross NPA ({npa_str}) within threshold.",
                metrics_meta
            )

        # 6. Missing / Unconfigured Live Banking Data:
        # Do NOT invent fake values, do NOT mark as ELIGIBLE based on fake data.
        return (
            "NEEDS_VERIFICATION",
            "Category and geographic criteria met; live banking telemetry (NPA ratio & fund quota) is unconfigured / awaiting nodal verification.",
            metrics_meta
        )

    @staticmethod
    def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance in kilometers between two coordinates using Haversine formula."""
        earth_radius_km = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
        a = min(1.0, max(0.0, a))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(earth_radius_km * c, 2)

    @staticmethod
    def extract_coordinates(
        obj: Any, 
        lat_keys=("latitude", "lat"), 
        lng_keys=("longitude", "lng")
    ) -> Tuple[Optional[float], Optional[float]]:
        """Safely extract valid (latitude, longitude) float tuple from an object or dictionary. Returns (None, None) if missing or invalid."""
        if obj is None:
            return None, None

        lat_val = None
        lng_val = None

        if isinstance(obj, dict):
            for k in lat_keys:
                if k in obj and obj[k] is not None:
                    lat_val = obj[k]
                    break
            for k in lng_keys:
                if k in obj and obj[k] is not None:
                    lng_val = obj[k]
                    break
            # Check nested coordinates dict
            if lat_val is None and isinstance(obj.get("applicant_coordinates"), dict):
                coords = obj["applicant_coordinates"]
                lat_val = coords.get("lat") or coords.get("latitude")
                lng_val = coords.get("lng") or coords.get("longitude")
            if lat_val is None and isinstance(obj.get("coordinates"), dict):
                coords = obj["coordinates"]
                lat_val = coords.get("lat") or coords.get("latitude")
                lng_val = coords.get("lng") or coords.get("longitude")
        else:
            for k in lat_keys:
                if hasattr(obj, k) and getattr(obj, k) is not None:
                    lat_val = getattr(obj, k)
                    break
            for k in lng_keys:
                if hasattr(obj, k) and getattr(obj, k) is not None:
                    lng_val = getattr(obj, k)
                    break

        if lat_val is None or lng_val is None:
            return None, None

        try:
            f_lat = float(lat_val)
            f_lng = float(lng_val)
            if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lng <= 180.0:
                return f_lat, f_lng
        except (ValueError, TypeError):
            pass

        return None, None

    def get_applicant_coordinates(
        self,
        application: Optional[Application] = None,
        user: Optional[User] = None,
        applicant_lat: Optional[float] = None,
        applicant_lng: Optional[float] = None
    ) -> Tuple[Optional[float], Optional[float]]:
        """Extract applicant coordinates from explicit params, application.form_data, or user profile."""
        # 1. Explicitly provided lat/lng
        if applicant_lat is not None and applicant_lng is not None:
            try:
                f_lat = float(applicant_lat)
                f_lng = float(applicant_lng)
                if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lng <= 180.0:
                    return f_lat, f_lng
            except (ValueError, TypeError):
                pass

        # 2. From application form_data
        if application and application.form_data:
            c_lat, c_lng = self.extract_coordinates(application.form_data)
            if c_lat is not None and c_lng is not None:
                return c_lat, c_lng

        # 3. From user profile
        if user:
            c_lat, c_lng = self.extract_coordinates(user)
            if c_lat is not None and c_lng is not None:
                return c_lat, c_lng

        return None, None

    def find_eligible_partners_for_application(
        self, 
        application: Application, 
        limit: int = 20,
        banking_data: Optional[Any] = None,
        applicant_lat: Optional[float] = None,
        applicant_lng: Optional[float] = None
    ) -> Tuple[Dict[str, Any], List[ApplicationPartnerRoutingItem], Optional[ApplicationPartnerRoutingItem]]:
        """
        Find suitable Channel Partners supporting the application's scheme category.
        Filters out INELIGIBLE partners (inactive, incompatible, or failing banking safeguards).
        Ranks candidates using Haversine distance proximity when coordinates are available,
        or preserves the District -> State -> National hierarchy when coordinates are unavailable.
        Preserves preferred partner type ranking.
        Returns (category_info, eligible_partners_list, assigned_partner).
        """
        scheme = application.scheme
        user = application.user
        category_info = self.determine_scheme_category(scheme)
        preferred_type = category_info.get("preferred_type", "PSB").lower()

        # Extract user location
        user_state = (user.state or "").strip() if user else ""
        user_district = (user.district or "").strip() if user else ""

        # Extract applicant GPS coordinates
        app_lat, app_lng = self.get_applicant_coordinates(
            application=application,
            user=user,
            applicant_lat=applicant_lat,
            applicant_lng=applicant_lng
        )

        # Fetch all institutions in database
        all_institutions = self.db.query(Institution).all()

        candidate_records = []
        for inst in all_institutions:
            verdict, reason, meta = self.evaluate_partner_eligibility(
                partner=inst,
                scheme=scheme,
                user=user,
                banking_data=banking_data
            )
            # Exclude clearly ineligible partners from the candidate list
            if verdict != "INELIGIBLE":
                # Determine geographic tier
                inst_state = (inst.state or "").strip().lower()
                inst_district = (inst.district or "").strip().lower()

                if user_district and inst_district == user_district.lower():
                    geo_tier_str = "district"
                    loc_tier = 0
                elif user_state and inst_state == user_state.lower():
                    geo_tier_str = "state"
                    loc_tier = 1
                else:
                    geo_tier_str = "national"
                    loc_tier = 2

                # Calculate Haversine distance when BOTH applicant and partner coordinates are available
                partner_lat, partner_lng = self.extract_coordinates(inst)
                dist_km = None
                if app_lat is not None and app_lng is not None and partner_lat is not None and partner_lng is not None:
                    dist_km = self.calculate_haversine_distance(app_lat, app_lng, partner_lat, partner_lng)

                candidate_records.append((inst, verdict, reason, meta, dist_km, geo_tier_str, loc_tier, partner_lat, partner_lng))

        if not candidate_records:
            return category_info, [], None

        # Multi-factor candidate ranking:
        # 1. Geographic Proximity:
        #    - If applicant provided coordinates:
        #      * If partner has coordinates: use Haversine distance (dist_km) directly.
        #      * If partner lacks coordinates: fallback by geographic tier (10000.0 + loc_tier * 1000.0)
        #    - If applicant lacks coordinates:
        #      * Strictly preserve District (0) -> State (1) -> National (2) hierarchy
        # 2. Preferred Partner Type: 0 = Preferred type, 1 = Other supported type
        # 3. Verdict Tier: 0 = ELIGIBLE (verified live), 1 = NEEDS_VERIFICATION (unconfigured/awaiting)
        # 4. Alphabetical name for deterministic stability
        def score_candidate(record_item):
            inst, verdict, _, _, dist_km, _, loc_tier, _, _ = record_item
            itype = (inst.institution_type or "").lower()
            pref_tier = 0 if (preferred_type in itype or itype in preferred_type) else 1
            verdict_tier = 0 if verdict == "ELIGIBLE" else 1

            if app_lat is not None and app_lng is not None:
                if dist_km is not None:
                    spatial_score = dist_km
                else:
                    spatial_score = 10000.0 + (loc_tier * 1000.0)
            else:
                spatial_score = float(loc_tier)

            return (spatial_score, pref_tier, verdict_tier, inst.name or "")

        ranked_records = sorted(candidate_records, key=score_candidate)

        # Build response items
        eligible_items: List[ApplicationPartnerRoutingItem] = []
        for inst, verdict, reason, meta, dist_km, geo_tier_str, loc_tier, partner_lat, partner_lng in ranked_records[:limit]:
            itype = inst.institution_type or "Channel Partner"
            is_pref = (preferred_type in itype.lower() or itype.lower() in preferred_type)

            # Format location string
            loc_parts = [p for p in [inst.city or inst.district, inst.state] if p]
            location_str = ", ".join(loc_parts) if loc_parts else None

            # Construct transparent recommendation reason
            reason_parts = []
            if dist_km is not None:
                reason_parts.append(f"Located {dist_km} km away ({geo_tier_str} tier).")
            elif geo_tier_str == "district":
                reason_parts.append(f"Primary district nodal partner in {inst.district}.")
            elif geo_tier_str == "state":
                reason_parts.append(f"State-level accredited partner in {inst.state}.")
            else:
                reason_parts.append("National-level accredited partner.")

            rec_reason_base = category_info.get("partner_reason", "Accredited channel partner.")
            reason_parts.append(rec_reason_base)
            transparent_reason = " ".join(reason_parts)

            if verdict == "ELIGIBLE":
                routing_status = "Preferred Channel Partner" if is_pref else "Eligible Channel Partner"
            else:
                routing_status = "Awaiting Nodal Banking Verification"

            item = ApplicationPartnerRoutingItem(
                partner_id=inst.id,
                partner_name=inst.name,
                short_name=inst.short_name,
                partner_type=inst.institution_type or "Partner Institution",
                supported_scheme_category=category_info["category_label"],
                location=location_str,
                address=inst.address,
                city=inst.city,
                district=inst.district,
                state=inst.state,
                is_eligible=True,
                is_preferred=is_pref,
                status=inst.status or "active",
                routing_status=routing_status,
                eligibility_verdict=verdict,
                eligibility_reason=reason,
                geographic_tier=geo_tier_str,
                distance_km=dist_km,
                latitude=partner_lat,
                longitude=partner_lng,
                sync_status=meta.get("sync_status"),
                is_authenticated_live=meta.get("is_authenticated_live", False),
                gross_npa_ratio=meta.get("gross_npa_ratio"),
                npa_risk_indicator=meta.get("npa_risk_indicator"),
                capacity_tier=meta.get("capacity_tier"),
                contact_phone=None,
                website=inst.website,
                recommendation_reason=transparent_reason
            )
            eligible_items.append(item)

        assigned_partner = eligible_items[0] if eligible_items else None
        return category_info, eligible_items, assigned_partner

    def get_application_partner_routing(
        self, 
        application: Application,
        banking_data: Optional[Any] = None,
        applicant_lat: Optional[float] = None,
        applicant_lng: Optional[float] = None
    ) -> ApplicationPartnerRoutingResponse:
        """Generate complete partner routing response for an application with eligibility filtering, proximity ranking, and transparent reasons."""
        scheme = application.scheme
        scheme_name = scheme.name if scheme else "Government MSME Scheme"
        scheme_id = scheme.id if scheme else application.scheme_id

        category_info, eligible_partners, assigned_partner = self.find_eligible_partners_for_application(
            application=application,
            banking_data=banking_data,
            applicant_lat=applicant_lat,
            applicant_lng=applicant_lng
        )

        app_lat, app_lng = self.get_applicant_coordinates(
            application=application,
            user=application.user,
            applicant_lat=applicant_lat,
            applicant_lng=applicant_lng
        )

        user = application.user
        user_state = (user.state or "").strip() if user else ""
        user_district = (user.district or "").strip() if user else ""

        ref_code = (application.form_data or {}).get("partner_reference_code")

        # Also evaluate excluded partners to provide transparent exclusion reasons
        all_institutions = self.db.query(Institution).all()
        excluded_items: List[ApplicationPartnerRoutingItem] = []
        for inst in all_institutions:
            verdict, reason, meta = self.evaluate_partner_eligibility(
                partner=inst,
                scheme=scheme,
                user=application.user,
                banking_data=banking_data
            )
            if verdict == "INELIGIBLE":
                loc_parts = [p for p in [inst.city or inst.district, inst.state] if p]
                location_str = ", ".join(loc_parts) if loc_parts else None

                inst_state = (inst.state or "").strip().lower()
                inst_district = (inst.district or "").strip().lower()
                if user_district and inst_district == user_district.lower():
                    geo_tier_str = "district"
                elif user_state and inst_state == user_state.lower():
                    geo_tier_str = "state"
                else:
                    geo_tier_str = "national"

                partner_lat, partner_lng = self.extract_coordinates(inst)
                dist_km = None
                if app_lat is not None and app_lng is not None and partner_lat is not None and partner_lng is not None:
                    dist_km = self.calculate_haversine_distance(app_lat, app_lng, partner_lat, partner_lng)

                excluded_items.append(ApplicationPartnerRoutingItem(
                    partner_id=inst.id,
                    partner_name=inst.name,
                    short_name=inst.short_name,
                    partner_type=inst.institution_type or "Partner Institution",
                    supported_scheme_category=category_info["category_label"],
                    location=location_str,
                    address=inst.address,
                    city=inst.city,
                    district=inst.district,
                    state=inst.state,
                    is_eligible=False,
                    is_preferred=False,
                    status=inst.status or "inactive",
                    routing_status="Ineligible for Scheme Routing",
                    eligibility_verdict="INELIGIBLE",
                    eligibility_reason=reason,
                    geographic_tier=geo_tier_str,
                    distance_km=dist_km,
                    latitude=partner_lat,
                    longitude=partner_lng,
                    sync_status=meta.get("sync_status"),
                    is_authenticated_live=meta.get("is_authenticated_live", False),
                    gross_npa_ratio=meta.get("gross_npa_ratio"),
                    npa_risk_indicator=meta.get("npa_risk_indicator"),
                    capacity_tier=meta.get("capacity_tier"),
                    contact_phone=None,
                    website=inst.website,
                    recommendation_reason=reason
                ))

        routing_note = category_info["routing_note"]
        if not eligible_partners:
            routing_note = (
                f"No accredited channel partners currently registered in the system for category '{category_info['category_label']}'. "
                "Application will be routed via the central nodal ministry portal directly."
            )
        elif assigned_partner and assigned_partner.eligibility_verdict == "NEEDS_VERIFICATION":
            routing_note = (
                f"{routing_note} (Assigned partner '{assigned_partner.partner_name}' has verified institutional status; "
                "live banking telemetry requires nodal confirmation prior to final sanction)."
            )

        total_needs_verification = sum(1 for p in eligible_partners if p.eligibility_verdict == "NEEDS_VERIFICATION")

        return ApplicationPartnerRoutingResponse(
            application_id=application.id,
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            scheme_category=category_info["category_label"],
            category_code=category_info["category_code"],
            preferred_partner_type=category_info.get("preferred_type"),
            routing_channel=application.channel or "online",
            partner_reference_code=ref_code,
            total_eligible_partners=len(eligible_partners),
            total_needs_verification_partners=total_needs_verification,
            assigned_partner=assigned_partner,
            eligible_partners=eligible_partners,
            excluded_partners=excluded_items[:20],
            routing_note=routing_note
        )

    def prepare_application_routing(
        self, 
        application: Application,
        banking_data: Optional[Any] = None,
        applicant_lat: Optional[float] = None,
        applicant_lng: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Prepare and store channel partner routing metadata in application.form_data.
        Returns the updated partner routing metadata dictionary.
        """
        category_info, eligible_partners, assigned_partner = self.find_eligible_partners_for_application(
            application=application,
            banking_data=banking_data,
            applicant_lat=applicant_lat,
            applicant_lng=applicant_lng
        )

        form_data = dict(application.form_data or {})
        partner_routing_meta: Dict[str, Any] = {
            "scheme_category": category_info["category_label"],
            "category_code": category_info["category_code"],
            "preferred_partner_type": category_info.get("preferred_type"),
            "total_eligible_partners": len(eligible_partners),
            "total_needs_verification": sum(1 for p in eligible_partners if p.eligibility_verdict == "NEEDS_VERIFICATION"),
            "routed_at": datetime.now(timezone.utc).isoformat() if assigned_partner else None
        }

        if assigned_partner:
            routing_status = (
                "Routed to Channel Partner" 
                if assigned_partner.eligibility_verdict == "ELIGIBLE" 
                else "Routed (Awaiting Nodal Banking Verification)"
            )
            partner_routing_meta.update({
                "assigned_partner_id": str(assigned_partner.partner_id),
                "assigned_partner_name": assigned_partner.partner_name,
                "assigned_partner_type": assigned_partner.partner_type,
                "assigned_partner_location": assigned_partner.location,
                "geographic_tier": assigned_partner.geographic_tier,
                "distance_km": assigned_partner.distance_km,
                "eligibility_verdict": assigned_partner.eligibility_verdict,
                "eligibility_reason": assigned_partner.eligibility_reason,
                "routing_status": routing_status
            })
        else:
            partner_routing_meta.update({
                "assigned_partner_id": None,
                "assigned_partner_name": None,
                "assigned_partner_type": None,
                "assigned_partner_location": None,
                "geographic_tier": None,
                "distance_km": None,
                "eligibility_verdict": "NO_ELIGIBLE_PARTNER",
                "eligibility_reason": "No channel partners met the scheme and institutional eligibility criteria.",
                "routing_status": "Awaiting Nodal Channel Partner Assignment"
            })

        form_data["partner_routing"] = partner_routing_meta
        application.form_data = form_data
        return partner_routing_meta
