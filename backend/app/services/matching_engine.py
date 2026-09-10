"""AI-powered scheme matching engine.

Enhanced approach:
1. Rule-based eligibility checker with PASS / FAIL / UNKNOWN status per criterion.
2. Explainable multi-factor Recommendation Score (Demographics 25%, Enterprise 25%, Financial 25%, Compliance 25%).
3. Personalized Loan Amount, Subsidy, and EMI recommendations based on user turnover, category, and scheme guidelines.
4. Transparent 'Why this scheme?' multi-tier analysis.
5. Multi-scheme comparison matrix support.
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timezone
from uuid import UUID
import json
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import User, Business, Scheme, UserSchemeMatch, utc_now
from app.schemas import (
    MatchReason, EligibilityRuleCheck, ScoreBreakdown, LoanRecommendation,
    SchemeMatchResponse, SchemeResponse, SchemeCompareResponse, SchemeCompareItem
)


class SchemeMatchingEngine:
    """Engine to evaluate and match entrepreneurs with eligible government schemes."""

    def __init__(self, db: Session):
        self.db = db

    def match_user(self, user_id: UUID, refresh: bool = False) -> List[SchemeMatchResponse]:
        """
        Find all matching schemes for a user.

        Args:
            user_id: The user to match
            refresh: If True, recompute even if cached matches exist

        Returns:
            List of SchemeMatchResponse sorted by match_score desc
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        business = self.db.query(Business).filter(Business.user_id == user_id).first()

        # Check cache unless refresh requested
        if not refresh:
            cached = self.db.query(UserSchemeMatch).filter(
                UserSchemeMatch.user_id == user_id
            ).order_by(UserSchemeMatch.match_score.desc()).all()
            if cached:
                def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
                    if not dt:
                        return None
                    if dt.tzinfo is not None:
                        return dt.astimezone(timezone.utc).replace(tzinfo=None)
                    return dt

                # Find newest profile timestamp (user or business)
                profile_timestamps = []
                user_updated = _normalize_dt(user.updated_at)
                user_created = _normalize_dt(user.created_at)
                if user_updated:
                    profile_timestamps.append(user_updated)
                elif user_created:
                    profile_timestamps.append(user_created)

                if business:
                    biz_updated = _normalize_dt(business.updated_at)
                    biz_created = _normalize_dt(business.created_at)
                    if biz_updated:
                        profile_timestamps.append(biz_updated)
                    elif biz_created:
                        profile_timestamps.append(biz_created)

                latest_profile_update = max(profile_timestamps) if profile_timestamps else None

                # Find latest cache timestamp
                cache_timestamps = [
                    _normalize_dt(m.updated_at or m.created_at)
                    for m in cached
                    if (m.updated_at or m.created_at)
                ]
                latest_cache_time = max(cache_timestamps) if cache_timestamps else None

                # If cache exists and is fresh (created/updated at or after latest profile update), return cached matches
                if latest_profile_update and latest_cache_time and latest_cache_time >= latest_profile_update:
                    return [self._match_to_response(m, user, business) for m in cached]
                elif not latest_profile_update and latest_cache_time:
                    return [self._match_to_response(m, user, business) for m in cached]

        # Get all active schemes
        schemes = self.db.query(Scheme).filter(Scheme.status == "active").all()

        matches = []
        for scheme in schemes:
            score, status, reasons, confidence, checks, breakdown, loan_rec, why_list = self._evaluate_scheme(
                user, business, scheme
            )
            # Only exclude strict non-matches
            if status not in ("not_eligible", "Not Eligible", "FAIL"):
                match = self._save_match(user_id, scheme, score, status, reasons, confidence)
                matches.append(self._match_to_response(match, user, business, checks, breakdown, loan_rec, why_list))

        # Sort by score descending
        matches.sort(key=lambda x: x.match_score, reverse=True)

        # Mark top 10 as recommended
        top_ids = [m.scheme_id for m in matches[:10]]
        if top_ids:
            self.db.query(UserSchemeMatch).filter(
                UserSchemeMatch.user_id == user_id,
                UserSchemeMatch.scheme_id.in_(top_ids)
            ).update({"is_recommended": True}, synchronize_session=False)
            self.db.commit()

        return matches

    def _evaluate_scheme(
        self, user: User, business: Optional[Business], scheme: Scheme
    ) -> Tuple[
        Decimal, str, List[MatchReason], str, 
        List[EligibilityRuleCheck], ScoreBreakdown, LoanRecommendation, List[str]
    ]:
        """
        Deep evaluation of a single scheme against user profile.

        Returns:
            (score, status, reasons, confidence, checks, score_breakdown, loan_recommendation, why_list)
        """
        reasons: List[MatchReason] = []
        checks: List[EligibilityRuleCheck] = []
        demographic_points = Decimal("0")
        enterprise_points = Decimal("0")
        financial_points = Decimal("0")
        compliance_points = Decimal("0")
        rationale: List[str] = []
        why_list: List[str] = []

        is_strict_disqualified = False

        # Helper to add check
        def add_check(rule_id: str, category: str, label: str, expected: str, actual: str, status: str, details: str = "", is_mandatory: bool = True):
            checks.append(EligibilityRuleCheck(
                rule_id=rule_id,
                category=category,
                label=label,
                expected=expected,
                actual=actual,
                status=status,
                details=details,
                is_mandatory=is_mandatory
            ))
            reasons.append(MatchReason(
                field=rule_id,
                expected=expected,
                actual=actual,
                match=(status == "PASS")
            ))

        # -------------------------------------------------------------
        # 1. LOCATION & STATE CHECK
        # -------------------------------------------------------------
        is_national = getattr(scheme, "is_national", True)
        applicable_states = getattr(scheme, "applicable_states", None)
        user_state = (user.state or "").strip()

        if is_national:
            add_check(
                "state", "Location", "Jurisdiction & Geography",
                "Pan-India / All States", user_state or "India Resident",
                "PASS", "National flagship scheme valid across all 28 States & 8 UTs."
            )
            demographic_points += Decimal("7")
            why_list.append("National Reach: Operating anywhere in India qualifies for central DBT facilitation.")
        elif applicable_states:
            states_norm = [s.strip().lower() for s in applicable_states if isinstance(s, str)]
            user_state_norm = user_state.lower()
            if user_state_norm and user_state_norm in states_norm:
                add_check(
                    "state", "Location", "State Jurisdiction",
                    ", ".join(applicable_states), user_state,
                    "PASS", f"Scheme covers your home state of {user_state}."
                )
                demographic_points += Decimal("7")
                why_list.append(f"State Focus: Direct allocation quota for beneficiaries in {user_state}.")
            elif not user_state_norm:
                add_check(
                    "state", "Location", "State Jurisdiction",
                    ", ".join(applicable_states), "Not specified in profile",
                    "UNKNOWN", "Please update your state in profile to confirm jurisdiction."
                )
                demographic_points += Decimal("3")
            else:
                add_check(
                    "state", "Location", "State Jurisdiction",
                    ", ".join(applicable_states), user_state,
                    "FAIL", f"Scheme is restricted to {', '.join(applicable_states)}."
                )
                is_strict_disqualified = True
        else:
            add_check("state", "Location", "State Coverage", "Any", user_state or "Any", "PASS")
            demographic_points += Decimal("7")

        # -------------------------------------------------------------
        # 2. GENDER DEMOGRAPHIC CHECK
        # -------------------------------------------------------------
        target_genders = getattr(scheme, "target_genders", None)
        user_gender = (user.gender or "").strip().lower()

        if target_genders:
            target_genders_norm = [g.strip().lower() for g in target_genders if isinstance(g, str)]
            if "all" in target_genders_norm or "any" in target_genders_norm:
                add_check("gender", "Demographics", "Gender Inclusivity", "All Genders", user.gender or "Any", "PASS", "Open to all genders.")
                demographic_points += Decimal("6")
            elif user_gender and user_gender in target_genders_norm:
                add_check(
                    "gender", "Demographics", "Target Gender Group",
                    ", ".join(target_genders), user.gender,
                    "PASS", f"Affirmative priority active for {user.gender} entrepreneurs."
                )
                demographic_points += Decimal("10")
                why_list.append(f"Targeted Focus: Affirmative credit subvention designed for {user.gender} founders.")
            elif not user_gender:
                add_check("gender", "Demographics", "Target Gender Group", ", ".join(target_genders), "Not provided", "UNKNOWN", "Specify gender in profile to claim affirmative scoring.")
                demographic_points += Decimal("3")
            else:
                add_check("gender", "Demographics", "Target Gender Group", ", ".join(target_genders), user.gender, "FAIL", f"Scheme exclusively targets {', '.join(target_genders)}.")
                is_strict_disqualified = True
        else:
            add_check("gender", "Demographics", "Gender Inclusivity", "All Genders", user.gender or "Any", "PASS")
            demographic_points += Decimal("6")

        # -------------------------------------------------------------
        # 3. SOCIAL CATEGORY (SC/ST/OBC/General/Minority)
        # -------------------------------------------------------------
        target_social_cats = getattr(scheme, "target_social_categories", None)
        user_social_cat = (user.social_category or "").strip().lower()

        if target_social_cats:
            target_cats_norm = [c.strip().lower() for c in target_social_cats if isinstance(c, str)]
            if "all" in target_cats_norm or "any" in target_cats_norm:
                add_check("social_category", "Demographics", "Social Group", "All Categories", user.social_category or "All", "PASS", "Universal access across all social groups.")
                demographic_points += Decimal("8")
            elif user_social_cat and user_social_cat in target_cats_norm:
                add_check(
                    "social_category", "Demographics", "Affirmative Category",
                    ", ".join(target_social_cats).upper(), user.social_category.upper(),
                    "PASS", f"Higher subsidy & margin money benefits active for {user.social_category.upper()} category."
                )
                demographic_points += Decimal("8")
                why_list.append(f"Affirmative Category: Priority allocation and reduced margin money (5%) for {user.social_category.upper()} entrepreneurs.")
            elif not user_social_cat:
                add_check("social_category", "Demographics", "Affirmative Category", ", ".join(target_social_cats).upper(), "Not provided", "UNKNOWN", "Provide social category in profile for affirmative quotas.")
                demographic_points += Decimal("3")
            else:
                add_check("social_category", "Demographics", "Affirmative Category", ", ".join(target_social_cats).upper(), user.social_category.upper(), "FAIL", f"Scheme earmarked specifically for {', '.join(target_social_cats).upper()}.")
                is_strict_disqualified = True
        else:
            add_check("social_category", "Demographics", "Social Category", "All Categories", user.social_category or "All", "PASS")
            demographic_points += Decimal("8")

        # -------------------------------------------------------------
        # 4. AGE RESTRICTIONS
        # -------------------------------------------------------------
        has_age_restriction = bool(scheme.min_age or scheme.max_age)
        age = self._calculate_age(user.date_of_birth) if user.date_of_birth else None

        if has_age_restriction:
            if age is not None:
                if scheme.min_age and age < scheme.min_age:
                    add_check("age", "Demographics", "Age Eligibility", f">= {scheme.min_age} yrs", f"{age} yrs", "FAIL", f"Applicant age ({age}) is below minimum requirement of {scheme.min_age} years.")
                    is_strict_disqualified = True
                elif scheme.max_age and age > scheme.max_age:
                    add_check("age", "Demographics", "Age Eligibility", f"<= {scheme.max_age} yrs", f"{age} yrs", "FAIL", f"Applicant age ({age}) exceeds scheme age ceiling of {scheme.max_age} years.")
                    is_strict_disqualified = True
                else:
                    add_check("age", "Demographics", "Age Eligibility", f"{scheme.min_age or 18} - {scheme.max_age or 'No upper limit'} yrs", f"{age} yrs", "PASS", "Applicant age within approved eligibility window.")
            else:
                add_check("age", "Demographics", "Age Eligibility", f"{scheme.min_age or 18} - {scheme.max_age or 65} yrs", "DOB not provided", "UNKNOWN", "Add date of birth in profile to verify age eligibility.")
        else:
            add_check("age", "Demographics", "Age Limit", "Standard (18+)", f"{age} yrs" if age else "Adult", "PASS")

        # -------------------------------------------------------------
        # 5. BUSINESS SECTOR / ACTIVITY TYPE
        # -------------------------------------------------------------
        target_btypes = getattr(scheme, "target_business_types", None)
        raw_user_btype = (business.business_type or "").strip().lower() if business else ""
        
        # Map common legacy synonyms to canonical backend schema enums
        btype_synonyms = {
            "services": "service",
            "farming": "agriculture",
            "agri": "agriculture",
            "dairy": "agriculture",
            "food": "food_processing",
            "foodprocessing": "food_processing",
            "tech": "technology",
            "it": "technology",
            "handicrafts": "handicraft",
            "handloom": "handicraft",
            "handlooms": "handicraft",
            "trade": "trading",
            "startup": "technology",
            "msme": "manufacturing",
            "individual": "other",
            "self_employed": "service",
            "freelance": "service",
            "consulting": "service",
        }
        user_btype = btype_synonyms.get(raw_user_btype, raw_user_btype)

        generic_types = {"other", "general", "unspecified", "all", "any", "misc", "miscellaneous"}

        if target_btypes:
            target_btypes_norm = [t.strip().lower() for t in target_btypes if isinstance(t, str)]
            user_btype_display = (user_btype or "").replace("_", " ").title()
            target_btypes_display = ", ".join(t.replace("_", " ") for t in target_btypes).title()
            if user_btype and user_btype in target_btypes_norm:
                add_check(
                    "business_type", "Enterprise", "Sector Alignment",
                    target_btypes_display, user_btype_display,
                    "PASS", f"Enterprise operational sector ({user_btype_display}) is approved."
                )
                enterprise_points += Decimal("12")
                why_list.append(f"Sector Alignment: Tailored assistance for {user_btype_display} units.")
            elif not user_btype or user_btype in generic_types:
                add_check(
                    "business_type", "Enterprise", "Sector Alignment",
                    target_btypes_display,
                    user_btype_display if user_btype else "Not specified",
                    "UNKNOWN",
                    "Specify your primary commercial activity in profile to confirm sector matching."
                )
                enterprise_points += Decimal("6")
            else:
                add_check("business_type", "Enterprise", "Sector Alignment", target_btypes_display, user_btype_display, "FAIL", f"Sector {user_btype_display} is not covered.")
                is_strict_disqualified = True
        else:
            user_btype_disp = (user_btype or "General").replace("_", " ").title() if business else "All"
            add_check("business_type", "Enterprise", "Sector Scope", "All Commercial Sectors", user_btype_disp, "PASS")
            enterprise_points += Decimal("12")

        # -------------------------------------------------------------
        # 6. BUSINESS STAGE (Idea / Pre-Revenue / Revenue)
        # -------------------------------------------------------------
        target_bstages = getattr(scheme, "target_business_stages", None)
        raw_user_bstage = (business.business_stage or "").strip().lower() if business else ""

        # Map common legacy synonyms to canonical backend schema enums
        bstage_synonyms = {
            "starting": "pre_revenue",
            "starting_up": "pre_revenue",
            "early": "pre_revenue",
            "prerevenue": "pre_revenue",
            "operating": "revenue",
            "running": "revenue",
            "expanding": "growth",
            "scaling": "growth",
            "established": "mature",
            "existing": "revenue",
        }
        user_bstage = bstage_synonyms.get(raw_user_bstage, raw_user_bstage) if raw_user_bstage else None

        if target_bstages:
            target_bstages_norm = [s.strip().lower() for s in target_bstages if isinstance(s, str)]
            
            # Group compatible early stages (idea, pre_revenue, starting_up)
            early_stages = {"idea", "pre_revenue", "starting_up"}
            scheme_has_early = bool(early_stages.intersection(set(target_bstages_norm)))

            if user_bstage and user_bstage in target_bstages_norm:
                add_check(
                    "business_stage", "Enterprise", "Operational Stage",
                    ", ".join(target_bstages).title(), user_bstage.title(),
                    "PASS", f"Supports enterprises at the '{user_bstage.title()}' lifecycle phase."
                )
                enterprise_points += Decimal("13")
            elif user_bstage and (user_bstage in early_stages) and scheme_has_early:
                # Compatible early stage
                add_check(
                    "business_stage", "Enterprise", "Operational Stage",
                    ", ".join(target_bstages).title(), user_bstage.title(),
                    "PASS", f"Early-stage venture compatible with scheme startup provisions."
                )
                enterprise_points += Decimal("10")
            elif not user_bstage:
                # Missing or unset business stage -> UNKNOWN (needs verification, not FAIL)
                add_check(
                    "business_stage", "Enterprise", "Operational Stage",
                    ", ".join(target_bstages).title(), "Not specified in profile",
                    "UNKNOWN", "Add business operational stage in profile to verify lifecycle compatibility."
                )
                enterprise_points += Decimal("6")
            else:
                add_check("business_stage", "Enterprise", "Operational Stage", ", ".join(target_bstages).title(), user_bstage.title(), "FAIL", f"Scheme requires stage to be one of {', '.join(target_bstages)}.")
                is_strict_disqualified = True
        else:
            add_check("business_stage", "Enterprise", "Operational Stage", "All Stages", user_bstage.title() if user_bstage else "All", "PASS")
            enterprise_points += Decimal("13")

        # -------------------------------------------------------------
        # 7. ANNUAL TURNOVER CEILING & RANGE
        # -------------------------------------------------------------
        has_turnover_restriction = bool(scheme.min_turnover_inr or scheme.max_turnover_inr)
        user_turnover = self._to_decimal(business.annual_turnover_inr) if business else None
        min_turnover = self._to_decimal(scheme.min_turnover_inr)
        max_turnover = self._to_decimal(scheme.max_turnover_inr)

        is_early_stage_user = (user_bstage in {"idea", "pre_revenue", "starting_up"} or user_bstage is None)

        if has_turnover_restriction:
            if user_turnover is not None:
                if max_turnover and user_turnover > max_turnover:
                    add_check("turnover", "Financial", "Turnover Ceiling", f"<= ₹{max_turnover:,.0f}", f"₹{user_turnover:,.0f}", "FAIL", "Turnover exceeds maximum ceiling for micro-enterprise support.")
                    is_strict_disqualified = True
                elif min_turnover and user_turnover < min_turnover:
                    # If user is early stage (idea/pre_revenue) or turnover is 0, check if scheme supports early stage
                    scheme_target_stages = getattr(scheme, "target_business_stages", None) or []
                    scheme_target_stages_norm = [s.strip().lower() for s in scheme_target_stages if isinstance(s, str)]
                    scheme_supports_early = bool({"idea", "pre_revenue", "starting_up"}.intersection(set(scheme_target_stages_norm)))

                    if (user_turnover == Decimal("0") or is_early_stage_user) and scheme_supports_early:
                        add_check(
                            "turnover", "Financial", "Turnover Verification",
                            f">= ₹{min_turnover:,.0f} (Revenue stage)",
                            f"₹{user_turnover:,.0f} (Early-Stage / Pre-Revenue)",
                            "UNKNOWN",
                            "New unit eligible under gestation / project finance terms; turnover minimum applies once operational."
                        )
                        financial_points += Decimal("7")
                    else:
                        add_check("turnover", "Financial", "Turnover Range", f">= ₹{min_turnover:,.0f}", f"₹{user_turnover:,.0f}", "FAIL", "Turnover is below minimum threshold for this tranche.")
                        is_strict_disqualified = True
                else:
                    add_check("turnover", "Financial", "Turnover Compliance", f"Up to ₹{max_turnover:,.0f}" if max_turnover else "Compliant", f"₹{user_turnover:,.0f}", "PASS", "Turnover falls within eligible MSME limits.")
                    financial_points += Decimal("12")
            else:
                add_check("turnover", "Financial", "Turnover Verification", f"Up to ₹{max_turnover:,.0f}" if max_turnover else "Eligible", "Not specified", "UNKNOWN", "Add turnover in profile to complete financial qualification.")
                financial_points += Decimal("6")
        else:
            add_check("turnover", "Financial", "Turnover Threshold", "No Cap", f"₹{user_turnover:,.0f}" if user_turnover else "N/A", "PASS")
            financial_points += Decimal("12")

        # -------------------------------------------------------------
        # 8. FUNDING NEED & BENEFIT ALIGNMENT
        # -------------------------------------------------------------
        funding_needed = self._to_decimal(business.funding_needed_inr) if business else Decimal("500000")
        max_benefit = self._to_decimal(scheme.max_benefit_inr)
        min_benefit = self._to_decimal(scheme.min_benefit_inr) or Decimal("10000")

        if funding_needed and max_benefit:
            if funding_needed <= max_benefit * Decimal("1.5"):
                add_check("funding_need", "Financial", "Credit Quantum Fit", f"Up to ₹{max_benefit:,.0f}", f"₹{funding_needed:,.0f}", "PASS", f"Requested capital is well-matched with scheme ceiling of ₹{max_benefit:,.0f}.")
                financial_points += Decimal("13")
                why_list.append(f"Optimal Financing Scale: Covers your project credit requirement of ₹{funding_needed:,.0f}.")
            else:
                add_check("funding_need", "Financial", "Credit Quantum Fit", f"Max ₹{max_benefit:,.0f}", f"₹{funding_needed:,.0f}", "UNKNOWN", f"Requested funding (₹{funding_needed:,.0f}) exceeds maximum single-unit ceiling (₹{max_benefit:,.0f}). Partial tranches available.")
                financial_points += Decimal("7")
        else:
            add_check("funding_need", "Financial", "Credit Allocation", "Standard Support", "₹500,000", "PASS")
            financial_points += Decimal("13")

        # -------------------------------------------------------------
        # 9. COMPLIANCE & READINESS (UDYAM, GST, Collateral)
        # -------------------------------------------------------------
        if scheme.requires_udyam:
            if user.udyam_number:
                add_check("udyam", "Compliance", "UDYAM MSME Registration", "Mandatory", f"Verified ({user.udyam_number})", "PASS", "Active MSME registration verified.")
                compliance_points += Decimal("10")
            else:
                add_check("udyam", "Compliance", "UDYAM MSME Registration", "Mandatory", "Pending Registration", "UNKNOWN", "UDYAM registration required prior to final disbursement (free via udyamregistration.gov.in).")
                compliance_points += Decimal("3")
        else:
            add_check("udyam", "Compliance", "UDYAM Registration", "Optional", "Exempted" if not user.udyam_number else "Registered", "PASS", "No mandatory UDYAM prerequisite.")
            compliance_points += Decimal("10")

        if scheme.requires_gst:
            if user.gstin:
                add_check("gst", "Compliance", "GSTIN Registration", "Required", f"Registered ({user.gstin})", "PASS", "Active GST filing profile confirmed.")
                compliance_points += Decimal("8")
            else:
                add_check("gst", "Compliance", "GSTIN Registration", "Required", "Not Registered", "UNKNOWN", "GST certificate needed for large procurement subsidy claims.")
                compliance_points += Decimal("2")
        else:
            add_check("gst", "Compliance", "GST Registration", "Optional / Micro Exempt", "Exempted" if not user.gstin else "Registered", "PASS", "Micro enterprises exempt from GST prerequisites.")
            compliance_points += Decimal("8")

        # Collateral / Credit evaluation (Self-declared / Document-based)
        requires_collateral = getattr(scheme, "requires_collateral", getattr(scheme, "collateral_required", False))
        if requires_collateral:
            if business and business.has_collateral:
                add_check("collateral", "Compliance", "Collateral Security (Self-declared)", "Required by Lender", "Available (Self-attested)", "PASS", "Collateral reported available for bank appraisal.")
                compliance_points += Decimal("7")
            else:
                add_check("collateral", "Compliance", "Collateral Security (Self-declared)", "Required by Lender", "Not Declared", "UNKNOWN", "Lender may request collateral documentation unless covered under CGTMSE guarantee.")
                compliance_points += Decimal("2")
        else:
            add_check("collateral", "Compliance", "Collateral Guarantee", "Collateral-Free Scheme Guidelines", "Exempted / CGTMSE Eligible", "PASS", "Scheme guidelines mandate collateral-free credit under CGTMSE or nodal agency norms.")
            compliance_points += Decimal("7")
            why_list.append("Zero Collateral Requirement: Scheme provides collateral-free institutional credit per government guidelines.")

        # Women ownership check
        women_min = getattr(scheme, "women_ownership_min_percent", None)
        if women_min:
            is_women_eligible = (business and business.is_women_led) or (user_gender == "female")
            if is_women_eligible:
                add_check("women_ownership", "Demographics", "Women Enterprise Stake", f">= {women_min}%", "Eligible (Women-Led)", "PASS", "Meets women-led enterprise shareholding criteria.")
                demographic_points = min(Decimal("25"), demographic_points + Decimal("5"))
                why_list.append("Women Entrepreneur Preference: Special concessionary interest rates & higher capital subsidy.")
            else:
                add_check("women_ownership", "Demographics", "Women Enterprise Stake", f">= {women_min}%", "Non-compliant", "FAIL", "Scheme requires majority women shareholding.")
                is_strict_disqualified = True

        # Application deadline check
        deadline = self._normalize_deadline(scheme.application_deadline)
        if deadline:
            days_left = (deadline - date.today()).days
            if days_left < 0:
                add_check("deadline", "Compliance", "Application Deadline", f"Before {deadline}", "Expired", "FAIL", "The application deadline for this scheme cycle has expired.")
                is_strict_disqualified = True
            else:
                add_check("deadline", "Compliance", "Application Deadline", f"Before {deadline}", f"{days_left} days left", "PASS", "Application window is currently active.")

        # -------------------------------------------------------------
        # Overall Verdict Calculation (PASS / FAIL / UNKNOWN)
        # -------------------------------------------------------------
        if is_strict_disqualified:
            overall_verdict = "FAIL"
            status = "Not Eligible"
        else:
            has_unknown = any(c.status == "UNKNOWN" for c in checks)
            if has_unknown:
                overall_verdict = "UNKNOWN"
                status = "Possibly Eligible"
            else:
                overall_verdict = "PASS"
                status = "Eligible"

        # Normalize score components (each category max 25)
        demographic_score = min(Decimal("25"), demographic_points)
        enterprise_score = min(Decimal("25"), enterprise_points)
        financial_score = min(Decimal("25"), financial_points)
        compliance_score = min(Decimal("25"), compliance_points)

        total_score = demographic_score + enterprise_score + financial_score + compliance_score
        if is_strict_disqualified:
            total_score = Decimal("0")

        # Rationale bullets
        rationale.append(f"Demographics ({demographic_score}/25): Target category and location compatibility.")
        rationale.append(f"Enterprise Fit ({enterprise_score}/25): Business sector and operational stage alignment.")
        rationale.append(f"Financial Scale ({financial_score}/25): Project turnover and funding requirement fit.")
        rationale.append(f"Compliance ({compliance_score}/25): Documentation, UDYAM, and collateral readiness.")

        score_breakdown = ScoreBreakdown(
            demographic_score=demographic_score,
            enterprise_score=enterprise_score,
            financial_score=financial_score,
            compliance_score=compliance_score,
            total_score=total_score,
            rationale=rationale
        )

        # -------------------------------------------------------------
        # Personalized Loan & Subsidy Recommendation Calculation
        # -------------------------------------------------------------
        loan_rec = self._calculate_loan_recommendation(user, business, scheme, funding_needed)

        # Confidence assessment
        unknown_count = sum(1 for c in checks if c.status == "UNKNOWN")
        if unknown_count == 0:
            confidence = "high"
        elif unknown_count <= 2:
            confidence = "medium"
        else:
            confidence = "low"

        return total_score, status, reasons, confidence, checks, score_breakdown, loan_rec, why_list

    def _calculate_loan_recommendation(
        self, user: User, business: Optional[Business], scheme: Scheme, funding_needed: Optional[Decimal]
    ) -> LoanRecommendation:
        """Compute personalized loan tranche, subsidy calculation, margin money, and monthly EMI."""
        min_benefit = self._to_decimal(scheme.min_benefit_inr) or Decimal("10000")
        max_benefit = self._to_decimal(scheme.max_benefit_inr) or Decimal("1000000")
        requested = funding_needed or Decimal("500000")

        # Recommended loan amount within scheme bounds
        recommended_loan = min(max_benefit, max(min_benefit, requested))

        # Margin money calculation
        user_cat = (user.social_category or "").strip().lower()
        user_gender = (user.gender or "").strip().lower()
        is_special_category = user_cat in ("sc", "st", "obc", "minority") or user_gender == "female" or getattr(user, "is_rural", False)

        if is_special_category:
            margin_percent = Decimal("5.0")  # 5% for SC/ST/Women/Rural in central schemes like PMEGP/Stand-Up
        else:
            margin_percent = Decimal("10.0")

        margin_money = (recommended_loan * margin_percent / Decimal("100.0")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Subsidy calculation
        subsidy_percent = getattr(scheme, "subsidy_percentage", None)
        if subsidy_percent is not None:
            subsidy_rate = self._to_decimal(subsidy_percent) or Decimal("0")
        else:
            # Infer scheme-specific typical subsidy
            scheme_name_lower = (scheme.name or "").lower()
            if "pmfme" in scheme_name_lower:
                subsidy_rate = Decimal("35.0")
            elif "pmegp" in scheme_name_lower:
                subsidy_rate = Decimal("35.0") if getattr(user, "is_rural", True) else Decimal("25.0")
            elif "subsidy" in (scheme.scheme_type or "").lower():
                subsidy_rate = Decimal("25.0")
            else:
                subsidy_rate = Decimal("0.0")

        estimated_subsidy = (recommended_loan * subsidy_rate / Decimal("100.0")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if max_benefit and estimated_subsidy > max_benefit:
            estimated_subsidy = max_benefit

        # Interest rate, Moratorium, and EMI calculation
        interest_rate = self._to_decimal(getattr(scheme, "interest_rate", None)) or Decimal("9.5")
        
        # Determine Scheme-Specific Moratorium & Tenure rules
        scheme_name_lower = (scheme.name or "").lower()
        scheme_desc_lower = (scheme.description or "").lower()
        scheme_type_lower = (scheme.scheme_type or "").lower()

        # Scheme specific moratorium mapping:
        if "stand-up india" in scheme_name_lower or "stand up india" in scheme_name_lower:
            total_tenure_months = 84  # Up to 7 years
            moratorium_months = 18    # Standard moratorium up to 18 months for greenfield setup
            moratorium_note = "Moratorium up to 18 months granted for greenfield project setup and initial stabilization."
        elif "pmegp" in scheme_name_lower or "prime minister's employment generation" in scheme_name_lower:
            total_tenure_months = 84  # 3 to 7 years
            moratorium_months = 6     # 6 months for service, up to 12m for manufacturing gestation
            moratorium_note = "6 months gestation moratorium included. Principal repayment begins from month 7."
        elif "mudra" in scheme_name_lower or "pmmy" in scheme_name_lower:
            total_tenure_months = 60  # 3 to 5 years
            moratorium_months = 6     # 3 to 6 months
            moratorium_note = "6 months moratorium on principal repayment for working capital / asset acquisition."
        elif "svanidhi" in scheme_name_lower or "pm svanidhi" in scheme_name_lower:
            total_tenure_months = 12  # 1 year
            moratorium_months = 1     # 1 month grace
            moratorium_note = "1 month initial grace period before monthly micro-installment cycle."
        elif "nsfdc" in scheme_name_lower or "sc" in scheme_name_lower:
            total_tenure_months = 60  # 5 years
            moratorium_months = 6     # 6 months grace
            moratorium_note = "6 months moratorium on term loan component with concessional SC refinance rate."
        elif "education" in scheme_name_lower or "vidyalakshmi" in scheme_name_lower or "education" in scheme_type_lower:
            total_tenure_months = 120 # 10 years
            moratorium_months = 12    # Course duration + 12 months standard
            moratorium_note = "12 months moratorium post-course completion before active EMI amortisation."
        elif "subsidy" in scheme_type_lower or "grant" in scheme_type_lower:
            total_tenure_months = 60
            moratorium_months = 3
            moratorium_note = "3 months initial moratorium during capital subsidy release and verification."
        else:
            total_tenure_months = 60  # standard 5-year micro loan
            moratorium_months = 6     # standard 6-month MSME moratorium
            moratorium_note = "6 months moratorium on principal repayment; EMI amortized over active tenure."

        # Active repayment tenure after moratorium period
        repayment_tenure_months = max(1, total_tenure_months - moratorium_months)

        # Monthly EMI calculation applied over the active repayment tenure: [P x R x (1+R)^N]/[(1+R)^N-1]
        p = float(recommended_loan)
        r = float(interest_rate) / (12 * 100)
        n = repayment_tenure_months
        if r > 0:
            emi_val = (p * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
        else:
            emi_val = p / n

        estimated_emi = Decimal(str(round(emi_val, 2))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        disclaimer = "Disbursement and subsidy release subject to physical appraisal by financing bank and nodal agency."

        return LoanRecommendation(
            recommended_loan_amount=recommended_loan,
            min_scheme_benefit=min_benefit,
            max_scheme_benefit=max_benefit,
            estimated_subsidy_amount=estimated_subsidy,
            subsidy_percentage=subsidy_rate,
            margin_money_required=margin_money,
            margin_money_percentage=margin_percent,
            interest_rate_percent=interest_rate,
            moratorium_period_months=moratorium_months,
            repayment_tenure_months=repayment_tenure_months,
            total_tenure_months=total_tenure_months,
            estimated_monthly_emi=estimated_emi,
            tenure_months=total_tenure_months,
            moratorium_note=moratorium_note,
            subsidy_disclaimer=disclaimer
        )

    def compare_schemes(self, user_id: UUID, scheme_ids: List[UUID]) -> SchemeCompareResponse:
        """Generate side-by-side comparative analysis of selected schemes."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        business = self.db.query(Business).filter(Business.user_id == user_id).first()

        items: List[SchemeCompareItem] = []
        for sid in scheme_ids:
            scheme = self.db.query(Scheme).filter(Scheme.id == sid).first()
            if not scheme:
                continue

            score, status, reasons, confidence, checks, breakdown, loan_rec, why_list = self._evaluate_scheme(
                user, business, scheme
            )

            # Build match response
            match_resp = SchemeMatchResponse(
                scheme_id=scheme.id,
                name=scheme.name,
                ministry=scheme.ministry,
                match_score=score,
                recommendation_score=score,
                eligibility_status=status,
                overall_verdict="PASS" if status in ("Eligible", "fully_eligible") else ("UNKNOWN" if status == "Possibly Eligible" else "FAIL"),
                confidence_level=confidence,
                reasons=reasons,
                criteria_checks=checks,
                score_breakdown=breakdown,
                loan_recommendation=loan_rec,
                ai_explanation=self._generate_explanation(scheme, reasons, status),
                why_this_scheme=why_list,
                why_you_match=self._extract_why_you_match(scheme, reasons),
                missing_requirements=self._extract_missing_requirements(scheme, reasons),
                potential_issues=self._extract_potential_issues(scheme, reasons),
                next_action=self._extract_next_action(scheme, status),
                benefit_description=scheme.benefit_description,
                scheme_type=scheme.scheme_type or "loan",
                official_url=scheme.official_url,
                helpline_number=scheme.helpline_number,
                application_deadline=scheme.application_deadline,
                is_bookmarked=False,
                is_applied=False
            )

            items.append(SchemeCompareItem(
                scheme=SchemeResponse.model_validate(scheme),
                match_data=match_resp
            ))

        common_criteria = [
            "Valid Indian Citizenship & Resident Proof",
            "Individual or Micro Enterprise operational within India",
            "Active Bank Account with IFSC and Aadhaar seeding"
        ]

        differing_features = [
            {
                "feature": "Max Project Ceiling",
                "values": {str(it.scheme.id): f"₹{float(it.scheme.max_benefit_inr or 0):,.0f}" if it.scheme.max_benefit_inr else "Not Capped" for it in items}
            },
            {
                "feature": "Capital Subsidy Rate",
                "values": {str(it.scheme.id): f"{float(it.match_data.loan_recommendation.subsidy_percentage or 0)}%" if it.match_data and it.match_data.loan_recommendation else "0%" for it in items}
            },
            {
                "feature": "Collateral Requirement",
                "values": {str(it.scheme.id): "Collateral-Free (CGTMSE)" if not it.scheme.collateral_required else "Security Required" for it in items}
            },
            {
                "feature": "Your Eligibility Verdict",
                "values": {str(it.scheme.id): it.match_data.overall_verdict if it.match_data else "UNKNOWN" for it in items}
            },
            {
                "feature": "Estimated Monthly EMI",
                "values": {str(it.scheme.id): f"₹{float(it.match_data.loan_recommendation.estimated_monthly_emi or 0):,.0f}/mo" if it.match_data and it.match_data.loan_recommendation else "N/A" for it in items}
            }
        ]

        # Recommendation summary
        best_item = max(items, key=lambda x: (x.match_data.match_score if x.match_data else Decimal("0")), default=None)
        if best_item and best_item.match_data:
            summary = (
                f"Based on your demographic profile and funding scale, {best_item.scheme.name} offers the highest compatibility "
                f"({best_item.match_data.match_score}% match) with an estimated capital subsidy of "
                f"₹{float(best_item.match_data.loan_recommendation.estimated_subsidy_amount or 0):,.0f} and zero collateral."
            )
        else:
            summary = "Review the criteria checks above to determine the optimal scheme for your enterprise."

        return SchemeCompareResponse(
            schemes=items,
            common_criteria=common_criteria,
            differing_features=differing_features,
            recommendation_summary=summary
        )

    def _save_match(
        self, user_id: UUID, scheme: Scheme, score: Decimal,
        status: str, reasons: List[MatchReason], confidence: str
    ) -> UserSchemeMatch:
        """Save or update match in database."""
        existing = self.db.query(UserSchemeMatch).filter(
            UserSchemeMatch.user_id == user_id,
            UserSchemeMatch.scheme_id == scheme.id
        ).first()

        ai_explanation = self._generate_explanation(scheme, reasons, status)

        if existing:
            existing.match_score = score
            existing.eligibility_status = status
            existing.match_reasons = [r.model_dump() for r in reasons]
            existing.confidence_level = confidence
            existing.ai_explanation = ai_explanation
            existing.updated_at = utc_now()
            match = existing
        else:
            match = UserSchemeMatch(
                user_id=user_id,
                scheme_id=scheme.id,
                match_score=score,
                eligibility_status=status,
                match_reasons=[r.model_dump() for r in reasons],
                confidence_level=confidence,
                ai_explanation=ai_explanation,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            self.db.add(match)

        self.db.commit()
        self.db.refresh(match)
        return match

    def _generate_explanation(self, scheme: Scheme, reasons: List[MatchReason], status: str) -> str:
        """Generate human-readable explanation of why user matches."""
        positive_reasons = [r for r in reasons if r.match]
        negative_reasons = [r for r in reasons if not r.match]

        explanation = f"You match the {scheme.name} scheme because:\n"

        for reason in positive_reasons[:4]:
            if reason.field == "state":
                explanation += f"• You are located in {reason.actual}, which is covered by this scheme.\n"
            elif reason.field == "gender":
                explanation += "• Your gender category qualifies for this scheme.\n"
            elif reason.field == "social_category":
                social_cat_disp = str(reason.actual).upper() if str(reason.actual).lower() in ("sc", "st", "obc", "ews") else str(reason.actual).title()
                explanation += f"• Your social category ({social_cat_disp}) is eligible.\n"
            elif reason.field == "business_type":
                btype_disp = str(reason.actual).replace("_", " ").title()
                explanation += f"• Your business type ({btype_disp}) is supported.\n"
            elif reason.field == "business_stage":
                bstage_disp = str(reason.actual).replace("_", " ").title()
                explanation += f"• Your business stage ({bstage_disp}) meets the scheme criteria.\n"
            elif reason.field == "turnover":
                explanation += "• Your annual turnover falls within the eligible range.\n"
            elif reason.field == "employees":
                explanation += "• Your employee count meets the scheme requirements.\n"
            elif reason.field == "funding_need":
                explanation += "• Your funding requirement aligns with the scheme benefits.\n"
            elif reason.field == "deadline":
                explanation += f"• The application is still open ({reason.actual}).\n"

        if negative_reasons:
            explanation += "\nNote: You may need to address:\n"
            for reason in negative_reasons[:3]:
                if reason.field == "udyam":
                    explanation += "• Register for UDYAM to fully qualify.\n"
                elif reason.field == "gst":
                    explanation += "• GST registration may be required.\n"
                elif reason.field == "collateral":
                    explanation += "• Collateral may be needed for loan schemes.\n"
                elif reason.field == "funding_need":
                    explanation += "• The scheme maximum benefit is lower than your requested funding.\n"
                elif reason.field == "turnover":
                    explanation += "• Turnover requirement needs verification.\n"

        return explanation.strip()

    def _extract_why_you_match(self, scheme: Scheme, reasons: List[MatchReason]) -> List[str]:
        items = []
        for r in reasons:
            if not r.match:
                continue
            if r.field == "state":
                items.append(f"Geographic eligibility: Operating in {r.actual}, which is covered by this scheme.")
            elif r.field == "gender":
                items.append(f"Demographic focus: Beneficiary profile ({r.actual}) qualifies under scheme target group.")
            elif r.field == "social_category":
                social_cat_disp = str(r.actual).upper() if str(r.actual).lower() in ("sc", "st", "obc", "ews") else str(r.actual).title()
                items.append(f"Affirmative action category: {social_cat_disp} category is designated as eligible.")
            elif r.field == "business_type":
                btype_disp = str(r.actual).replace("_", " ").title()
                items.append(f"Sector alignment: Enterprise activity ({btype_disp}) is supported under this program.")
            elif r.field == "business_stage":
                bstage_disp = str(r.actual).replace("_", " ").title()
                items.append(f"Enterprise stage: Business operational stage ({bstage_disp}) meets criteria.")
            elif r.field == "turnover":
                items.append("Turnover compliance: Enterprise annual turnover is within specified ceiling.")
            elif r.field == "employees":
                items.append("Workforce size: Employee count is compliant with micro/small unit thresholds.")
            elif r.field == "udyam":
                items.append("MSME Registration: Verified UDYAM registration confirmed.")
            elif r.field == "funding_need":
                items.append("Financial scale: Required project funding matches scheme benefit limits.")
        return items[:5]

    def _extract_missing_requirements(self, scheme: Scheme, reasons: List[MatchReason]) -> List[str]:
        items = []
        for r in reasons:
            if r.match:
                continue
            if r.field == "udyam":
                items.append("UDYAM Registration Certificate: Active registration required for application submission.")
            elif r.field == "gst":
                items.append("GSTIN Registration: Proof of GST filing or exemption declaration required.")
            elif r.field == "collateral":
                items.append("Collateral Security / Third-Party Guarantee may be required by the lending bank.")
            elif r.field == "funding_need":
                items.append("Budget Adjustment: Requested loan amount exceeds maximum ceiling for this scheme.")
            elif r.field == "turnover":
                items.append("Turnover verification: Updated audited financials or ITR documents required.")
        return items[:4]

    def _extract_potential_issues(self, scheme: Scheme, reasons: List[MatchReason]) -> List[str]:
        items = []
        if scheme.collateral_required:
            items.append("Collateral required: Bank may require tangible security depending on loan quantum.")
        if scheme.application_mode == "offline":
            items.append("Offline processing: Requires physical submission of DPR and KYC at local branch/DIC.")
        if scheme.requires_udyam and any(not r.match and r.field == "udyam" for r in reasons):
            items.append("Mandatory MSME registration pending on Udyam portal.")
        if scheme.max_benefit_inr and scheme.max_benefit_inr < Decimal("1000000"):
            items.append("Capped micro-credit tranche: Useful primarily for working capital, not heavy capex.")
        return items[:3]

    def _extract_next_action(self, scheme: Scheme, status: str) -> str:
        if status in ("Eligible", "fully_eligible", "PASS"):
            if scheme.official_url:
                return f"Review DPR templates and apply online at {scheme.official_url} or visit nearest designated branch."
            return "Assemble KYC, project report, and apply at your nearest District Industries Centre (DIC) or bank."
        elif status in ("Possibly Eligible", "likely_eligible", "partially_eligible", "UNKNOWN"):
            return "Complete missing documentation (e.g., UDYAM or Project Report) to elevate application readiness."
        elif status in ("Needs Verification", "needs_verification"):
            return "Contact helpline or visit nearest CSC center to verify district-specific quotas and guidelines."
        return "Explore alternative schemes aligned with your demographic or enterprise sector."

    def _match_to_response(
        self, 
        match: UserSchemeMatch, 
        user: Optional[User] = None, 
        business: Optional[Business] = None,
        checks: Optional[List[EligibilityRuleCheck]] = None,
        breakdown: Optional[ScoreBreakdown] = None,
        loan_rec: Optional[LoanRecommendation] = None,
        why_list: Optional[List[str]] = None
    ) -> SchemeMatchResponse:
        """Convert DB match to API response."""
        scheme = match.scheme or self.db.query(Scheme).filter(Scheme.id == match.scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme {match.scheme_id} not found for match {match.id}")

        if not user:
            user = self.db.query(User).filter(User.id == match.user_id).first()
        if not business and user:
            business = self.db.query(Business).filter(Business.user_id == user.id).first()

        reasons = [MatchReason(**r) for r in (match.match_reasons or [])]

        if checks is None or breakdown is None or loan_rec is None or why_list is None:
            _, _, _, _, checks, breakdown, loan_rec, why_list = self._evaluate_scheme(user, business, scheme)

        why_you_match = self._extract_why_you_match(scheme, reasons)
        missing_requirements = self._extract_missing_requirements(scheme, reasons)
        potential_issues = self._extract_potential_issues(scheme, reasons)
        next_action = self._extract_next_action(scheme, match.eligibility_status)

        status = match.eligibility_status
        if status in ("fully_eligible", "likely_eligible"):
            status = "Eligible"
        elif status == "partially_eligible":
            status = "Possibly Eligible"
        elif status == "needs_verification":
            status = "Needs Verification"

        verdict = "PASS" if status in ("Eligible", "fully_eligible") else ("UNKNOWN" if status in ("Possibly Eligible", "Needs Verification") else "FAIL")

        return SchemeMatchResponse(
            scheme_id=scheme.id,
            name=scheme.name,
            ministry=scheme.ministry,
            match_score=match.match_score,
            recommendation_score=match.match_score,
            eligibility_status=status,
            overall_verdict=verdict,
            confidence_level=match.confidence_level or "high",
            reasons=reasons,
            criteria_checks=checks or [],
            score_breakdown=breakdown,
            loan_recommendation=loan_rec,
            ai_explanation=match.ai_explanation,
            why_this_scheme=why_list or [],
            why_you_match=why_you_match,
            missing_requirements=missing_requirements,
            potential_issues=potential_issues,
            next_action=next_action,
            benefit_description=scheme.benefit_description,
            scheme_type=scheme.scheme_type or "loan",
            official_url=scheme.official_url,
            helpline_number=scheme.helpline_number,
            application_deadline=scheme.application_deadline,
            is_bookmarked=bool(match.is_bookmarked),
            is_applied=bool(match.is_applied)
        )

    @staticmethod
    def _calculate_age(dob: Any) -> Optional[int]:
        if not dob:
            return None
        if isinstance(dob, str):
            try:
                dob = date.fromisoformat(dob.split("T")[0])
            except ValueError:
                return None
        elif isinstance(dob, datetime):
            dob = dob.date()
        elif not isinstance(dob, date):
            return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @staticmethod
    def _normalize_deadline(deadline: Any) -> Optional[date]:
        if not deadline:
            return None
        if isinstance(deadline, str):
            try:
                return date.fromisoformat(deadline.split("T")[0])
            except ValueError:
                return None
        if isinstance(deadline, datetime):
            return deadline.date()
        if isinstance(deadline, date):
            return deadline
        return None

    @staticmethod
    def _to_decimal(val: Any) -> Optional[Decimal]:
        if val is None or val == "":
            return None
        try:
            return Decimal(str(val))
        except (ValueError, TypeError):
            return None


def get_matching_engine(db: Session) -> SchemeMatchingEngine:
    return SchemeMatchingEngine(db)
