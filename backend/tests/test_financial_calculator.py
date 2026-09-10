"""Regression tests for Financial Calculator & Loan Simulation.

Validates:
- Standard reducing-balance EMI calculations
- Zero-interest subvention/grant handling (r = 0)
- Moratorium gestation grace periods and principal deferral
- Scheme-specific maximum loan ceilings and warning generation
- Invalid input validation (P <= 0, N <= 0, M < 0, M >= N, r < 0)
- API endpoints: POST /schemes/calculate-emi & POST /schemes/{scheme_id}/simulate-loan
"""
from decimal import Decimal
import uuid
import pytest

from app.models import Scheme
from app.services.financial_calculator_service import (
    FinancialCalculatorService,
    get_scheme_moratorium_and_tenure_defaults,
)


# ==================== UNIT TESTS FOR FINANCIAL SERVICE ====================

def test_emi_calculation_formula_precision():
    """Verify standard reducing balance EMI formula produces exact financial benchmark results."""
    # Principal: ₹10,00,000, Annual Rate: 9.5%, Tenure: 60 months (5 years)
    # Monthly rate r = 0.095 / 12 = 0.007916666...
    # EMI = [1,000,000 * r * (1+r)^60] / [(1+r)^60 - 1] ≈ 21,001.91
    principal = Decimal("1000000")
    rate = Decimal("9.5")
    repayment_months = 60

    emi = FinancialCalculatorService.calculate_emi(
        principal=principal,
        annual_rate_percent=rate,
        repayment_months=repayment_months
    )

    assert emi == Decimal("21001.86")


def test_zero_interest_subvention_handling():
    """Verify zero-interest subvention/grant (r = 0) produces clean linear division with zero interest."""
    principal = Decimal("120000")
    rate = Decimal("0.0")
    repayment_months = 12

    emi = FinancialCalculatorService.calculate_emi(
        principal=principal,
        annual_rate_percent=rate,
        repayment_months=repayment_months
    )

    # 120,000 / 12 = 10,000.00
    assert emi == Decimal("10000.00")

    # Verify full simulation with zero interest
    sim = FinancialCalculatorService.simulate_loan(
        principal=principal,
        tenure_months=12,
        moratorium_months=0,
        interest_rate_percent=Decimal("0.0"),
        include_schedule=True
    )

    assert sim["monthly_emi"] == Decimal("10000.00")
    assert sim["total_interest"] == Decimal("0.00")
    assert sim["total_repayment"] == Decimal("120000.00")

    # Verify every schedule row has zero interest
    schedule = sim["monthly_schedule"]
    assert len(schedule) == 12
    for item in schedule:
        assert item["interest_component"] == Decimal("0.00")
        assert item["monthly_payment"] == Decimal("10000.00")
    assert schedule[-1]["closing_balance"] == Decimal("0.00")


def test_moratorium_grace_period_and_schedule():
    """Verify moratorium grace period defers principal and amortizes remaining balance correctly."""
    principal = Decimal("500000")
    total_tenure = 24
    moratorium = 6
    rate = Decimal("10.0")

    sim = FinancialCalculatorService.simulate_loan(
        principal=principal,
        tenure_months=total_tenure,
        moratorium_months=moratorium,
        interest_rate_percent=rate,
        include_schedule=True
    )

    assert sim["total_tenure_months"] == 24
    assert sim["moratorium_months"] == 6
    assert sim["active_repayment_months"] == 18

    schedule = sim["monthly_schedule"]
    assert len(schedule) == 24

    # First 6 months must be in MORATORIUM phase
    for m in range(6):
        row = schedule[m]
        assert row["month_number"] == m + 1
        assert row["phase"] == "MORATORIUM"
        assert row["principal_component"] == Decimal("0.00")
        assert row["monthly_payment"] == Decimal("0.00")
        assert row["closing_balance"] == Decimal("500000.00")
        assert "Deferred" in row["status_note"]

    # Months 7 to 24 must be in REPAYMENT phase
    repayment_rows = schedule[6:]
    assert len(repayment_rows) == 18
    for row in repayment_rows:
        assert row["phase"] == "REPAYMENT"
        assert row["monthly_payment"] > Decimal("0.00")

    # Final month closing balance must reach exactly 0
    assert repayment_rows[-1]["closing_balance"] == Decimal("0.00")
    # Sum of principal components across repayment must equal original principal
    total_principal_paid = sum(r["principal_component"] for r in repayment_rows)
    assert total_principal_paid == principal


def test_scheme_limits_and_warnings():
    """Verify scheme maximum loan limits generate clear warnings when exceeded and pass when within limit."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="PM Mudra Yojana (Tarun)",
        ministry="Ministry of Finance",
        description="Loans up to 10 Lakhs",
        max_loan_amount_inr=Decimal("1000000"),
        interest_rate=Decimal("9.25"),
        status="active"
    )

    # 1. Loan within ceiling limit
    res_within = FinancialCalculatorService.simulate_loan(
        principal=Decimal("800000"),
        scheme=scheme
    )
    assert res_within["is_within_limit"] is True
    assert res_within["limit_warning"] is None
    assert res_within["max_loan_limit_inr"] == Decimal("1000000")
    assert res_within["rate_source"] == "scheme_database"
    assert res_within["interest_rate_percent"] == Decimal("9.25")

    # 2. Loan exceeding ceiling limit
    res_exceed = FinancialCalculatorService.simulate_loan(
        principal=Decimal("1500000"),
        scheme=scheme
    )
    assert res_exceed["is_within_limit"] is False
    assert res_exceed["limit_warning"] is not None
    assert "exceeds the scheme ceiling limit of ₹1,000,000.00" in res_exceed["limit_warning"]


def test_scheme_subsidy_deduction():
    """Verify capital subsidy reduces net effective loan liability."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="PMEGP Manufacturing",
        ministry="MSME",
        description="35% capital subsidy for special category",
        max_loan_amount_inr=Decimal("5000000"),
        max_benefit_inr=Decimal("1750000"),
        subsidy_percentage=Decimal("35.0"),
        status="active"
    )

    res = FinancialCalculatorService.simulate_loan(
        principal=Decimal("1000000"),
        scheme=scheme
    )

    # 35% of 10L = 3,50,000
    assert res["estimated_subsidy_amount"] == Decimal("350000.00")
    assert res["subsidy_percentage"] == Decimal("35.0")
    # Net loan liability = 10,00,000 - 3,50,000 = 6,50,000
    assert res["net_effective_loan"] == Decimal("650000.00")


def test_invalid_inputs_validation():
    """Verify strict input validation for principal, tenure, moratorium, and rates."""
    # Principal <= 0
    with pytest.raises(ValueError, match="strictly greater than 0"):
        FinancialCalculatorService.simulate_loan(principal=Decimal("0"))

    with pytest.raises(ValueError, match="strictly greater than 0"):
        FinancialCalculatorService.simulate_loan(principal=Decimal("-50000"))

    # Tenure <= 0
    with pytest.raises(ValueError, match="at least 1 month"):
        FinancialCalculatorService.simulate_loan(principal=Decimal("100000"), tenure_months=0)

    # Negative moratorium
    with pytest.raises(ValueError, match="cannot be negative"):
        FinancialCalculatorService.simulate_loan(principal=Decimal("100000"), moratorium_months=-2)

    # Moratorium >= Tenure
    with pytest.raises(ValueError, match="strictly less than total tenure"):
        FinancialCalculatorService.simulate_loan(
            principal=Decimal("100000"),
            tenure_months=12,
            moratorium_months=12
        )

    with pytest.raises(ValueError, match="strictly less than total tenure"):
        FinancialCalculatorService.simulate_loan(
            principal=Decimal("100000"),
            tenure_months=12,
            moratorium_months=15
        )

    # Negative interest rate
    with pytest.raises(ValueError, match="Interest rate cannot be negative"):
        FinancialCalculatorService.simulate_loan(
            principal=Decimal("100000"),
            interest_rate_percent=Decimal("-3.5")
        )


# ==================== API ENDPOINT REGRESSION TESTS ====================

def test_api_calculate_generic_emi(client):
    """Test POST /schemes/calculate-emi endpoint with valid and invalid requests."""
    # 1. Valid request
    payload = {
        "principal_amount": 300000,
        "tenure_months": 36,
        "moratorium_months": 3,
        "interest_rate_percent": 8.5,
        "include_schedule": True
    }
    response = client.post("/schemes/calculate-emi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["principal_amount"])) == Decimal("300000.00")
    assert data["total_tenure_months"] == 36
    assert data["moratorium_months"] == 3
    assert data["active_repayment_months"] == 33
    assert Decimal(str(data["monthly_emi"])) > 0
    assert len(data["monthly_schedule"]) == 36

    # 2. Invalid request: principal <= 0
    bad_payload = {
        "principal_amount": 0,
        "tenure_months": 24
    }
    resp_bad = client.post("/schemes/calculate-emi", json=bad_payload)
    # Pydantic schema validation catches gt=0
    assert resp_bad.status_code == 422

    # 3. Invalid request: moratorium >= tenure
    bad_moratorium = {
        "principal_amount": 100000,
        "tenure_months": 12,
        "moratorium_months": 12
    }
    resp_bad_m = client.post("/schemes/calculate-emi", json=bad_moratorium)
    assert resp_bad_m.status_code == 400
    assert "strictly less than total tenure" in resp_bad_m.json()["detail"]


def test_api_simulate_scheme_loan(test_db, client):
    """Test POST /schemes/{scheme_id}/simulate-loan using real database scheme data."""
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Stand-Up India Scheme",
        ministry="Ministry of Finance",
        description="Composite loans between 10 lakh and 1 crore for SC/ST and women entrepreneurs.",
        scheme_type="credit_guarantee",
        interest_rate=Decimal("8.75"),
        max_loan_amount_inr=Decimal("10000000"),
        subsidy_percentage=Decimal("0.0"),
        status="active"
    )
    test_db.add(scheme)
    test_db.commit()

    # 1. Within ceiling limit
    res = client.post(
        f"/schemes/{scheme.id}/simulate-loan",
        json={
            "principal_amount": 5000000,
            "include_schedule": True
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scheme_id"] == str(scheme.id)
    assert data["scheme_name"] == "Stand-Up India Scheme"
    assert Decimal(str(data["principal_amount"])) == Decimal("5000000.00")
    # Auto-resolves Stand-Up India's 18 months moratorium and 84 months tenure
    assert data["total_tenure_months"] == 84
    assert data["moratorium_months"] == 18
    assert data["active_repayment_months"] == 66
    assert Decimal(str(data["interest_rate_percent"])) == Decimal("8.75")
    assert data["rate_source"] == "scheme_database"
    assert data["is_within_limit"] is True
    assert data["limit_warning"] is None

    # 2. Exceeding ceiling limit
    res_over = client.post(
        f"/schemes/{scheme.id}/simulate-loan",
        json={
            "principal_amount": 15000000,
            "include_schedule": False
        }
    )
    assert res_over.status_code == 200
    data_over = res_over.json()
    assert data_over["is_within_limit"] is False
    assert "exceeds the scheme ceiling limit of ₹10,000,000.00" in data_over["limit_warning"]

    # 3. Non-existent scheme ID
    random_id = uuid.uuid4()
    res_404 = client.post(
        f"/schemes/{random_id}/simulate-loan",
        json={"principal_amount": 100000}
    )
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "Scheme not found"
