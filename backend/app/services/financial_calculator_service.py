"""Financial Calculator & Loan Simulation Service.

Implements statutory and scheme-grounded financial modeling:
- Reducing-balance EMI calculation
- Zero-interest subvention edge-case handling (r = 0)
- Moratorium gestation grace periods with principal deferral
- Real database scheme limit enforcement & ceiling warnings
- Month-by-month payment breakdown / amortization schedule
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from app.models import Scheme


def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def get_scheme_moratorium_and_tenure_defaults(scheme: Scheme) -> Tuple[int, int, str]:
    """Derive standard moratorium, total tenure, and statutory note from real scheme attributes."""
    scheme_name_lower = (scheme.name or "").lower()
    scheme_desc_lower = (scheme.description or "").lower()
    scheme_type_lower = (scheme.scheme_type or "").lower()

    if "stand-up india" in scheme_name_lower or "stand up india" in scheme_name_lower:
        return 84, 18, "Moratorium up to 18 months granted for greenfield project setup and initial stabilization."
    elif "pmegp" in scheme_name_lower or "prime minister's employment generation" in scheme_name_lower:
        return 84, 6, "6 months gestation moratorium included. Principal repayment begins from month 7."
    elif "mudra" in scheme_name_lower or "pmmy" in scheme_name_lower:
        return 60, 6, "6 months moratorium on principal repayment for working capital / asset acquisition."
    elif "svanidhi" in scheme_name_lower or "pm svanidhi" in scheme_name_lower:
        return 12, 1, "1 month initial grace period before monthly micro-installment cycle."
    elif "nsfdc" in scheme_name_lower or "sc" in scheme_name_lower:
        return 60, 6, "6 months moratorium on term loan component with concessional SC refinance rate."
    elif "education" in scheme_name_lower or "vidyalakshmi" in scheme_name_lower or "education" in scheme_type_lower:
        return 120, 12, "12 months moratorium post-course completion before active EMI amortisation."
    elif "subsidy" in scheme_type_lower or "grant" in scheme_type_lower:
        return 60, 3, "3 months initial moratorium during capital subsidy release and verification."
    else:
        return 60, 6, "6 months standard MSME gestation moratorium on principal repayment."


class FinancialCalculatorService:
    """Service handling EMI computation, loan simulation, and repayment breakdowns."""

    @staticmethod
    def calculate_emi(
        principal: Decimal,
        annual_rate_percent: Decimal,
        repayment_months: int
    ) -> Decimal:
        """Calculate monthly EMI using reducing balance formula or linear division when rate is 0.
        
        Formula for r > 0: EMI = [P * r * (1+r)^N] / [(1+r)^N - 1]
        Formula for r = 0: EMI = P / N
        """
        if principal <= Decimal("0"):
            raise ValueError("Principal loan amount must be strictly greater than 0")
        if repayment_months <= 0:
            raise ValueError("Repayment tenure must be at least 1 month")
        if annual_rate_percent < Decimal("0"):
            raise ValueError("Interest rate cannot be negative")

        if annual_rate_percent == Decimal("0"):
            emi = (principal / Decimal(repayment_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return emi

        # Reducing balance monthly rate
        r = float(annual_rate_percent) / (12 * 100)
        n = repayment_months
        p = float(principal)

        factor = (1 + r) ** n
        emi_float = (p * r * factor) / (factor - 1)
        return Decimal(str(round(emi_float, 2))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def generate_monthly_breakdown(
        cls,
        principal: Decimal,
        annual_rate_percent: Decimal,
        tenure_months: int,
        moratorium_months: int,
        monthly_emi: Decimal
    ) -> List[Dict[str, Any]]:
        """Generate month-by-month repayment schedule reflecting moratorium and active amortisation."""
        schedule: List[Dict[str, Any]] = []
        current_balance = principal
        monthly_rate = float(annual_rate_percent) / (12 * 100) if annual_rate_percent > Decimal("0") else 0.0

        # Phase 1: Moratorium months (Principal deferred)
        for m in range(1, moratorium_months + 1):
            schedule.append({
                "month_number": m,
                "phase": "MORATORIUM",
                "opening_balance": current_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "monthly_payment": Decimal("0.00"),
                "principal_component": Decimal("0.00"),
                "interest_component": Decimal("0.00"),
                "closing_balance": current_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "status_note": "Moratorium Period (Principal Repayment Deferred)"
            })

        # Phase 2: Active Repayment
        active_months = tenure_months - moratorium_months
        for i in range(1, active_months + 1):
            month_number = moratorium_months + i
            opening = current_balance

            if annual_rate_percent > Decimal("0"):
                interest_flt = round(float(opening) * monthly_rate, 2)
                interest = Decimal(str(interest_flt)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                # In final month, adjust principal to match exactly remaining balance
                if i == active_months:
                    principal_paid = opening
                    payment = (principal_paid + interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    closing = Decimal("0.00")
                else:
                    principal_paid = (monthly_emi - interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if principal_paid > opening:
                        principal_paid = opening
                    payment = monthly_emi
                    closing = (opening - principal_paid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                # Zero-interest
                interest = Decimal("0.00")
                if i == active_months:
                    principal_paid = opening
                    payment = principal_paid
                    closing = Decimal("0.00")
                else:
                    principal_paid = (principal / Decimal(active_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    payment = principal_paid
                    closing = (opening - principal_paid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            current_balance = closing
            schedule.append({
                "month_number": month_number,
                "phase": "REPAYMENT",
                "opening_balance": opening.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "monthly_payment": payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "principal_component": principal_paid.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "interest_component": interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "closing_balance": closing.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "status_note": "Active Repayment EMI"
            })

        return schedule

    @classmethod
    def simulate_loan(
        cls,
        principal: Decimal,
        tenure_months: Optional[int] = None,
        moratorium_months: Optional[int] = None,
        interest_rate_percent: Optional[Decimal] = None,
        scheme: Optional[Scheme] = None,
        include_schedule: bool = True
    ) -> Dict[str, Any]:
        """Perform comprehensive loan simulation with scheme grounding and limit enforcement."""
        # 1. Input validations
        if principal is None or principal <= Decimal("0"):
            raise ValueError("Principal loan amount must be strictly greater than 0")

        # 2. Scheme-specific grounding for defaults and limits
        scheme_id = scheme.id if scheme else None
        scheme_name = scheme.name if scheme else None
        rate_source = "user_specified"

        default_tenure, default_moratorium, default_note = (60, 6, "6 months gestation moratorium on principal repayment.")
        if scheme:
            default_tenure, default_moratorium, default_note = get_scheme_moratorium_and_tenure_defaults(scheme)

        final_tenure = tenure_months if tenure_months is not None else default_tenure
        final_moratorium = moratorium_months if moratorium_months is not None else default_moratorium

        if final_tenure <= 0:
            raise ValueError("Total tenure must be at least 1 month")
        if final_moratorium < 0:
            raise ValueError("Moratorium period cannot be negative")
        if final_moratorium >= final_tenure:
            raise ValueError(f"Moratorium period ({final_moratorium} months) must be strictly less than total tenure ({final_tenure} months)")

        # Resolve interest rate
        if interest_rate_percent is not None:
            final_rate = _to_decimal(interest_rate_percent)
            rate_source = "user_specified"
        elif scheme and scheme.interest_rate is not None:
            final_rate = _to_decimal(scheme.interest_rate)
            rate_source = "scheme_database"
        else:
            final_rate = Decimal("9.50")
            rate_source = "statutory_benchmark"

        if final_rate < Decimal("0"):
            raise ValueError("Interest rate cannot be negative")

        # 3. Scheme limit enforcement
        max_loan_limit: Optional[Decimal] = None
        is_within_limit = True
        limit_warning: Optional[str] = None

        if scheme:
            limit_candidate = _to_decimal(scheme.max_loan_amount_inr) or _to_decimal(scheme.max_benefit_inr)
            if limit_candidate is not None:
                max_loan_limit = limit_candidate
                if principal > max_loan_limit:
                    is_within_limit = False
                    limit_warning = (
                        f"Requested principal (₹{principal:,.2f}) exceeds the scheme ceiling limit of ₹{max_loan_limit:,.2f}."
                    )

        # 4. Subsidy & Net Loan calculation
        estimated_subsidy: Optional[Decimal] = None
        subsidy_pct: Optional[Decimal] = None
        net_effective_loan: Decimal = principal

        if scheme and scheme.subsidy_percentage:
            subsidy_pct = _to_decimal(scheme.subsidy_percentage)
            if subsidy_pct:
                raw_subsidy = (principal * subsidy_pct / Decimal("100.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                max_benefit = _to_decimal(scheme.max_benefit_inr)
                if max_benefit and raw_subsidy > max_benefit:
                    raw_subsidy = max_benefit
                estimated_subsidy = raw_subsidy
                net_effective_loan = max(Decimal("0.00"), principal - estimated_subsidy)

        # 5. Core EMI & Breakdown
        active_repayment_months = final_tenure - final_moratorium
        monthly_emi = cls.calculate_emi(
            principal=principal,
            annual_rate_percent=final_rate,
            repayment_months=active_repayment_months
        )

        schedule: List[Dict[str, Any]] = []
        if include_schedule:
            schedule = cls.generate_monthly_breakdown(
                principal=principal,
                annual_rate_percent=final_rate,
                tenure_months=final_tenure,
                moratorium_months=final_moratorium,
                monthly_emi=monthly_emi
            )

        # Calculate totals
        if final_rate == Decimal("0"):
            total_repayment = principal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_interest = Decimal("0.00")
        else:
            if schedule:
                total_repayment = sum(s["monthly_payment"] for s in schedule).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_interest = sum(s["interest_component"] for s in schedule).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                total_repayment = (monthly_emi * Decimal(active_repayment_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_interest = (total_repayment - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "principal_amount": principal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "interest_rate_percent": final_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "rate_source": rate_source,
            "total_tenure_months": final_tenure,
            "moratorium_months": final_moratorium,
            "active_repayment_months": active_repayment_months,
            "monthly_emi": monthly_emi,
            "total_interest": total_interest,
            "total_repayment": total_repayment,
            "max_loan_limit_inr": max_loan_limit,
            "is_within_limit": is_within_limit,
            "limit_warning": limit_warning,
            "estimated_subsidy_amount": estimated_subsidy,
            "subsidy_percentage": subsidy_pct,
            "net_effective_loan": net_effective_loan.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "monthly_schedule": schedule,
            "moratorium_note": default_note,
            "disclaimer": "Loan appraisal, sanction, and subsidy disbursal are governed by institutional bank credit policies and nodal DBT rules."
        }
