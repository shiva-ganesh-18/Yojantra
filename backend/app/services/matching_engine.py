"""AI-powered scheme matching engine.

Hybrid approach:
1. Rule-based hard filters (fast, deterministic)
2. ML scoring for nuanced matches
3. LLM explanation generation
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID
import json
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import User, Business, Scheme, UserSchemeMatch
from app.schemas import MatchReason, SchemeMatchResponse


class SchemeMatchingEngine:
    """Engine to match users with eligible government schemes."""

    def __init__(self, db: Session):
        self.db = db

    def match_user(self, user_id: UUID, refresh: bool = False) -> List[SchemeMatchResponse]:
        """
        Main entry point: find all matching schemes for a user.

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
                return [self._match_to_response(m) for m in cached]

        # Get all active schemes
        schemes = self.db.query(Scheme).filter(Scheme.status == "active").all()

        matches = []
        for scheme in schemes:
            score, status, reasons, confidence = self._evaluate_scheme(user, business, scheme)
            if status != "not_eligible":
                match = self._save_match(user_id, scheme, score, status, reasons, confidence)
                matches.append(self._match_to_response(match))

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
    ) -> Tuple[Decimal, str, List[MatchReason], str]:
        """
        Evaluate a single scheme against user profile.

        Returns:
            (match_score, eligibility_status, reasons, confidence)
        """
        reasons: List[MatchReason] = []
        total_checks = 0
        passed_checks = 0

        # Helper to add reason
        def add_reason(field: str, expected: Any, actual: Any, matched: bool):
            reasons.append(MatchReason(
                field=field,
                expected=str(expected) if expected is not None else "any",
                actual=str(actual) if actual is not None else "not provided",
                match=matched
            ))

        # 1. LOCATION CHECK
        is_national = getattr(scheme, "is_national", True)
        applicable_states = getattr(scheme, "applicable_states", None)
        user_state = (user.state or "").strip()

        if is_national:
            add_reason("state", "National (All States)", user_state or "All", True)
            passed_checks += 1
            total_checks += 1
        elif applicable_states:
            states_norm = [s.strip().lower() for s in applicable_states if isinstance(s, str)]
            user_state_norm = user_state.lower()
            total_checks += 1
            if user_state_norm and user_state_norm in states_norm:
                add_reason("state", applicable_states, user_state, True)
                passed_checks += 1
            elif not user_state_norm:
                add_reason("state", applicable_states, "Not specified", False)
                return Decimal("0"), "not_eligible", reasons, "high"
            else:
                add_reason("state", applicable_states, user_state, False)
                return Decimal("0"), "not_eligible", reasons, "high"
        else:
            add_reason("state", "Any", user_state or "Any", True)
            passed_checks += 1
            total_checks += 1

        # 2. GENDER CHECK
        target_genders = getattr(scheme, "target_genders", None)
        user_gender = (user.gender or "").strip()

        if target_genders:
            target_genders_norm = [g.strip().lower() for g in target_genders if isinstance(g, str)]
            user_gender_norm = user_gender.lower()
            total_checks += 1
            if "all" in target_genders_norm or "any" in target_genders_norm:
                add_reason("gender", "Any", user_gender or "Any", True)
                passed_checks += 1
            elif user_gender_norm and user_gender_norm in target_genders_norm:
                add_reason("gender", target_genders, user_gender, True)
                passed_checks += 1
            elif not user_gender_norm:
                add_reason("gender", target_genders, "Not provided", False)
                return Decimal("0"), "not_eligible", reasons, "high"
            else:
                add_reason("gender", target_genders, user_gender, False)
                return Decimal("0"), "not_eligible", reasons, "high"
        else:
            add_reason("gender", "Any", user_gender or "Any", True)
            passed_checks += 1
            total_checks += 1

        # 3. SOCIAL CATEGORY CHECK
        target_social_cats = getattr(scheme, "target_social_categories", None)
        user_social_cat = (user.social_category or "").strip()

        if target_social_cats:
            target_cats_norm = [c.strip().lower() for c in target_social_cats if isinstance(c, str)]
            user_cat_norm = user_social_cat.lower()
            total_checks += 1
            if "all" in target_cats_norm or "any" in target_cats_norm:
                add_reason("social_category", "Any", user_social_cat or "Any", True)
                passed_checks += 1
            elif user_cat_norm and user_cat_norm in target_cats_norm:
                add_reason("social_category", target_social_cats, user_social_cat, True)
                passed_checks += 1
            elif not user_cat_norm:
                add_reason("social_category", target_social_cats, "Not provided", False)
                return Decimal("0"), "not_eligible", reasons, "high"
            else:
                add_reason("social_category", target_social_cats, user_social_cat, False)
                return Decimal("0"), "not_eligible", reasons, "high"
        else:
            add_reason("social_category", "Any", user_social_cat or "Any", True)
            passed_checks += 1
            total_checks += 1

        # 4. AGE CHECK
        has_age_restriction = bool(scheme.min_age or scheme.max_age)
        age = self._calculate_age(user.date_of_birth) if user.date_of_birth else None

        if has_age_restriction:
            total_checks += 1
            if age is not None:
                if scheme.min_age and age < scheme.min_age:
                    add_reason("age", f">= {scheme.min_age}", age, False)
                    return Decimal("0"), "not_eligible", reasons, "high"
                if scheme.max_age and age > scheme.max_age:
                    add_reason("age", f"<= {scheme.max_age}", age, False)
                    return Decimal("0"), "not_eligible", reasons, "high"
                add_reason("age", f"{scheme.min_age or 'Any'} - {scheme.max_age or 'Any'}", age, True)
                passed_checks += 1
            else:
                add_reason("age", f"{scheme.min_age or 'Any'} - {scheme.max_age or 'Any'}", "Unknown", False)
        else:
            add_reason("age", "Any", age if age is not None else "Any", True)
            passed_checks += 1
            total_checks += 1

        # 5. BUSINESS TYPE CHECK
        target_btypes = getattr(scheme, "target_business_types", None)
        user_btype = (business.business_type or "").strip() if business else ""

        if target_btypes:
            target_btypes_norm = [t.strip().lower() for t in target_btypes if isinstance(t, str)]
            user_btype_norm = user_btype.lower()
            total_checks += 1
            if user_btype_norm and user_btype_norm in target_btypes_norm:
                add_reason("business_type", target_btypes, user_btype, True)
                passed_checks += 1
            elif not user_btype_norm:
                add_reason("business_type", target_btypes, "Not specified", False)
                return Decimal("0"), "not_eligible", reasons, "high"
            else:
                add_reason("business_type", target_btypes, user_btype, False)
                return Decimal("0"), "not_eligible", reasons, "high"
        else:
            add_reason("business_type", "Any", user_btype or "Any", True)
            passed_checks += 1
            total_checks += 1

        # 6. BUSINESS STAGE CHECK
        target_bstages = getattr(scheme, "target_business_stages", None)
        user_bstage = (business.business_stage or "idea").strip() if business else "idea"

        if target_bstages:
            target_bstages_norm = [s.strip().lower() for s in target_bstages if isinstance(s, str)]
            user_bstage_norm = user_bstage.lower()
            total_checks += 1
            if user_bstage_norm in target_bstages_norm:
                add_reason("business_stage", target_bstages, user_bstage, True)
                passed_checks += 1
            else:
                add_reason("business_stage", target_bstages, user_bstage, False)
                return Decimal("0"), "not_eligible", reasons, "high"
        else:
            add_reason("business_stage", "Any", user_bstage or "Any", True)
            passed_checks += 1
            total_checks += 1

        # 7. TURNOVER CHECK
        has_turnover_restriction = bool(scheme.min_turnover_inr or scheme.max_turnover_inr)
        user_turnover = self._to_decimal(business.annual_turnover_inr) if business else None
        min_turnover = self._to_decimal(scheme.min_turnover_inr)
        max_turnover = self._to_decimal(scheme.max_turnover_inr)

        if has_turnover_restriction:
            total_checks += 1
            if user_turnover is not None:
                if min_turnover and user_turnover < min_turnover:
                    add_reason("turnover", f">= ₹{min_turnover}", f"₹{user_turnover}", False)
                    return Decimal("0"), "not_eligible", reasons, "high"
                if max_turnover and user_turnover > max_turnover:
                    add_reason("turnover", f"<= ₹{max_turnover}", f"₹{user_turnover}", False)
                    return Decimal("0"), "not_eligible", reasons, "high"
                add_reason("turnover", f"₹{min_turnover or '0'} - ₹{max_turnover or 'Any'}", f"₹{user_turnover}", True)
                passed_checks += 1
            else:
                add_reason("turnover", f"₹{min_turnover or '0'} - ₹{max_turnover or 'Any'}", "Not provided", False)
        else:
            add_reason("turnover", "Any", f"₹{user_turnover}" if user_turnover is not None else "Not provided", True)
            passed_checks += 1
            total_checks += 1

        # 8. EMPLOYEES CHECK
        has_emp_restriction = bool(scheme.min_employees or scheme.max_employees)
        emp = business.num_employees if (business and business.num_employees is not None) else None

        if has_emp_restriction:
            total_checks += 1
            if emp is not None:
                if scheme.min_employees and emp < scheme.min_employees:
                    add_reason("employees", f">= {scheme.min_employees}", emp, False)
                    return Decimal("0"), "not_eligible", reasons, "high"
                if scheme.max_employees and emp > scheme.max_employees:
                    add_reason("employees", f"<= {scheme.max_employees}", emp, False)
                    return Decimal("0"), "not_eligible", reasons, "high"
                add_reason("employees", f"{scheme.min_employees or '0'} - {scheme.max_employees or 'Any'}", emp, True)
                passed_checks += 1
            else:
                add_reason("employees", f"{scheme.min_employees or '0'} - {scheme.max_employees or 'Any'}", "Not provided", False)
        else:
            add_reason("employees", "Any", emp if emp is not None else "Not provided", True)
            passed_checks += 1
            total_checks += 1

        # 9. REGISTRATION CHECKS (UDYAM & GST)
        if scheme.requires_udyam:
            total_checks += 1
            if user.udyam_number:
                add_reason("udyam", "Required", "Registered", True)
                passed_checks += 1
            else:
                add_reason("udyam", "Required", "Not registered", False)
        else:
            add_reason("udyam", "Not required", "Registered" if user.udyam_number else "Not registered", True)

        if scheme.requires_gst:
            total_checks += 1
            if user.gstin:
                add_reason("gst", "Required", "Registered", True)
                passed_checks += 1
            else:
                add_reason("gst", "Required", "Not registered", False)
        else:
            add_reason("gst", "Not required", "Registered" if user.gstin else "Not registered", True)

        # 10. COLLATERAL CHECK
        requires_collateral = getattr(scheme, "requires_collateral", getattr(scheme, "collateral_required", False))
        if requires_collateral:
            total_checks += 1
            if business and business.has_collateral:
                add_reason("collateral", "Required", "Available", True)
                passed_checks += 1
            else:
                add_reason("collateral", "Required", "Not available", False)
        else:
            add_reason("collateral", "Not required", "Available" if (business and business.has_collateral) else "N/A", True)

        # 11. WOMEN OWNERSHIP CHECK
        women_min_percent = getattr(scheme, "women_ownership_min_percent", None)
        if women_min_percent:
            total_checks += 1
            is_women_eligible = (business and business.is_women_led) or (user_gender.lower() == "female")
            if is_women_eligible:
                add_reason("women_ownership", f">= {women_min_percent}%", "Eligible", True)
                passed_checks += 1
            else:
                add_reason("women_ownership", f">= {women_min_percent}%", "Not eligible", False)
                return Decimal("0"), "not_eligible", reasons, "high"

        # 12. FUNDING NEED ALIGNMENT
        funding_needed = self._to_decimal(business.funding_needed_inr) if business else None
        max_benefit = self._to_decimal(scheme.max_benefit_inr)
        if funding_needed and max_benefit:
            total_checks += 1
            if funding_needed <= max_benefit * Decimal("1.5"):
                add_reason("funding_need", f"Up to ₹{max_benefit}", f"₹{funding_needed}", True)
                passed_checks += 1
            else:
                add_reason("funding_need", f"Up to ₹{max_benefit}", f"₹{funding_needed}", False)

        # 13. DEADLINE URGENCY
        deadline = self._normalize_deadline(scheme.application_deadline)
        if deadline:
            days_left = (deadline - date.today()).days
            total_checks += 1
            if days_left < 0:
                add_reason("deadline", f"Before {deadline}", "Expired", False)
                return Decimal("0"), "not_eligible", reasons, "high"
            else:
                add_reason("deadline", f"Before {deadline}", f"{days_left} days left", True)
                passed_checks += 1

        # Calculate score
        if total_checks > 0:
            base_score = (Decimal(passed_checks) / Decimal(total_checks)) * Decimal("100")
        else:
            base_score = Decimal("50")

        # Adjust for benefit relevance
        if funding_needed and max_benefit and funding_needed > Decimal("0"):
            relevance = min(Decimal("1.0"), max_benefit / funding_needed)
            base_score = base_score * (Decimal("0.7") + relevance * Decimal("0.3"))

        # Adjust for deadline urgency (boost near-deadline schemes)
        if deadline:
            days_left = (deadline - date.today()).days
            if 0 <= days_left < 7:
                base_score = min(Decimal("100"), base_score * Decimal("1.1"))

        score = min(Decimal("100"), max(Decimal("0"), round(base_score, 2)))

        # Determine status and confidence
        if score >= 90:
            status = "fully_eligible"
            confidence = "high"
        elif score >= 70:
            status = "likely_eligible"
            confidence = "high"
        elif score >= 50:
            status = "partially_eligible"
            confidence = "medium"
        else:
            status = "partially_eligible"
            confidence = "low"

        return score, status, reasons, confidence

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
            existing.updated_at = datetime.now()
            match = existing
        else:
            match = UserSchemeMatch(
                user_id=user_id,
                scheme_id=scheme.id,
                match_score=score,
                eligibility_status=status,
                match_reasons=[r.model_dump() for r in reasons],
                confidence_level=confidence,
                ai_explanation=ai_explanation
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
                explanation += f"• Your social category ({reason.actual}) is eligible.\n"
            elif reason.field == "business_type":
                explanation += f"• Your business type ({reason.actual}) is supported.\n"
            elif reason.field == "business_stage":
                explanation += f"• Your business stage ({reason.actual}) meets the scheme criteria.\n"
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

    def _match_to_response(self, match: UserSchemeMatch) -> SchemeMatchResponse:
        """Convert DB match to API response."""
        scheme = match.scheme or self.db.query(Scheme).filter(Scheme.id == match.scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme {match.scheme_id} not found for match {match.id}")

        return SchemeMatchResponse(
            scheme_id=scheme.id,
            name=scheme.name,
            ministry=scheme.ministry,
            match_score=match.match_score,
            eligibility_status=match.eligibility_status,
            confidence_level=match.confidence_level,
            reasons=[MatchReason(**r) for r in (match.match_reasons or [])],
            ai_explanation=match.ai_explanation,
            benefit_description=scheme.benefit_description,
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
