"""Regression Tests for Government & Banking Integration (Part 10).

Covers all 5 integration categories across all 4 operational states:
1. Valid (Authorized credentials + successful upstream gateway response)
2. Invalid (Malformed inputs, non-existent entities, replay attacks)
3. Unavailable (Upstream timeouts, connection errors, HTTP 500)
4. Unauthorized (Upstream 401/403, bad HMAC-SHA256 webhook signatures, cross-user violations)
5. Zero Fabrication Enforcement (Never fakes banking, NPA, PFMS, UTR, or DBT data)
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import User, Business, Scheme, Application, Institution, AuditLog
from app.services.banking_service import (
    BankingDataSyncStatus,
    PartnerCapacityTier,
    PartnerNPARiskLevel,
    DirectCBSBankingProvider,
    BankingDataService,
    DirectPFMSGatewayAdapter,
    PFMSDataService,
)
from app.services.integrations_service import BankingWebhookProcessor

settings = get_settings()


@pytest.fixture
def banking_test_setup(test_db):
    """Fixture providing user, admin, partner institution, scheme, and application."""
    user = User(
        id=uuid.uuid4(),
        phone="+919876543210",
        full_name="Lakshmi Narayanan",
        gender="female",
        social_category="OBC",
        state="Tamil Nadu",
        district="Madurai",
        role="user",
        is_active=True
    )
    other_user = User(
        id=uuid.uuid4(),
        phone="+919876543219",
        full_name="Vikram Singh",
        gender="male",
        social_category="general",
        state="Rajasthan",
        district="Jaipur",
        role="user",
        is_active=True
    )
    admin = User(
        id=uuid.uuid4(),
        phone="+919876543299",
        full_name="Admin Officer",
        role="admin",
        is_active=True
    )
    partner = Institution(
        id=uuid.uuid4(),
        name="Canara Bank Lead Branch Madurai",
        short_name="Canara Madurai",
        code="CNRB-MDU-001",
        institution_type="PSB",
        state="Tamil Nadu",
        district="Madurai",
        status="active"
    )
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Pradhan Mantri Mudra Yojana (PMMY)",
        ministry="Ministry of Finance",
        description="Micro enterprise loan facility",
        status="active"
    )
    app_record = Application(
        id=uuid.uuid4(),
        user_id=user.id,
        scheme_id=scheme.id,
        channel="online",
        status="approved",
        form_data={
            "partner_reference_code": "YOJ-CANARA-7788",
            "partner_routing": {
                "assigned_partner_id": str(partner.id),
                "assigned_partner_name": partner.name,
                "routing_status": "APPROVED"
            }
        }
    )

    test_db.add_all([user, other_user, admin, partner, scheme, app_record])
    test_db.commit()

    user_token = create_access_token(data={"sub": str(user.id), "role": "user"})
    other_token = create_access_token(data={"sub": str(other_user.id), "role": "user"})
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    return {
        "user": user,
        "other_user": other_user,
        "admin": admin,
        "partner": partner,
        "scheme": scheme,
        "application": app_record,
        "user_headers": {"Authorization": f"Bearer {user_token}"},
        "other_headers": {"Authorization": f"Bearer {other_token}"},
        "admin_headers": {"Authorization": f"Bearer {admin_token}"}
    }


# ============================================================================
# 1. CORE BANKING SYSTEM (CBS) DATA ADAPTER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_cbs_unconfigured_never_fakes_banking_data(banking_test_setup):
    """Unconfigured CBS provider must strictly return CONFIGURATION_READY without fabricated data."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="", api_key="")
    assert not provider.is_configured()

    metrics = await provider.fetch_cbs_partner_metrics(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name,
        institution_type=partner.institution_type
    )

    assert metrics.sync_status == BankingDataSyncStatus.CONFIGURATION_READY.value
    assert metrics.is_authenticated_live is False
    assert metrics.system_health == "UNCONFIGURED"
    assert metrics.disbursement_sla_days is None
    assert "CONFIGURATION-READY" in metrics.disclosure
    assert "not fabricated" in metrics.disclosure


@pytest.mark.asyncio
async def test_cbs_valid_live_integration(monkeypatch, banking_test_setup):
    """Configured CBS provider with 200 response must emit verified LIVE telemetry."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="secret-bearer-key")
    assert provider.is_configured()

    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "partner_operational_status": "Active (Live Telemetry)",
                "lead_bank_active": True,
                "branch_code": "CNRB0001234",
                "disbursement_sla_days": 4,
                "system_health": "OPTIMAL"
            }

    class MockAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None): return MockResponse()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    metrics = await provider.fetch_cbs_partner_metrics(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name,
        institution_type=partner.institution_type
    )

    assert metrics.sync_status == BankingDataSyncStatus.LIVE.value
    assert metrics.is_authenticated_live is True
    assert metrics.system_health == "OPTIMAL"
    assert metrics.disbursement_sla_days == 4
    assert metrics.branch_code == "CNRB0001234"
    assert "Verified live" in metrics.disclosure


@pytest.mark.asyncio
async def test_cbs_unavailable_integration_falls_back_safely(monkeypatch, banking_test_setup):
    """When CBS gateway times out or returns 500, provider must fall back without crashing."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="secret-key")

    class MockErrorClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None):
            class Res:
                status_code = 503
            return Res()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockErrorClient)

    metrics = await provider.fetch_cbs_partner_metrics(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name,
        institution_type=partner.institution_type
    )

    assert metrics.sync_status == BankingDataSyncStatus.FALLBACK.value
    assert metrics.is_authenticated_live is False
    assert metrics.system_health == "DEGRADED"
    assert "falling back" in metrics.disclosure.lower()


@pytest.mark.asyncio
async def test_cbs_unauthorized_integration(monkeypatch, banking_test_setup):
    """When CBS gateway rejects credentials (HTTP 401), provider must set OFFLINE fallback."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="expired-key")

    class Mock401Client:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None):
            class Res:
                status_code = 401
            return Res()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", Mock401Client)

    metrics = await provider.fetch_cbs_partner_metrics(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name,
        institution_type=partner.institution_type
    )

    assert metrics.sync_status == BankingDataSyncStatus.FALLBACK.value
    assert metrics.is_authenticated_live is False
    assert metrics.system_health == "OFFLINE"


def test_cbs_metrics_endpoint_integration(client: TestClient, banking_test_setup):
    """GET /integrations/banking/partner/{partner_id}/metrics endpoint test."""
    partner = banking_test_setup["partner"]
    headers = banking_test_setup["user_headers"]

    # 1. Valid partner query
    res = client.get(f"/integrations/banking/partner/{partner.id}/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["partner_name"] == partner.name
    assert data["sync_status"] in ["LIVE", "CONFIGURATION_READY", "FALLBACK"]

    # 2. Invalid non-existent partner query
    non_existent_id = uuid.uuid4()
    res_404 = client.get(f"/integrations/banking/partner/{non_existent_id}/metrics", headers=headers)
    assert res_404.status_code == 404


# ============================================================================
# 2. NPA AND FUND UTILIZATION ADAPTER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_npa_unconfigured_never_fabricates_ratios(banking_test_setup):
    """Unconfigured NPA provider must return None/UNKNOWN without fabricated NPA numbers."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="", api_key="")

    resp = await provider.fetch_npa_fund_utilization(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name
    )

    assert resp.sync_status == BankingDataSyncStatus.CONFIGURATION_READY.value
    assert resp.is_authenticated_live is False
    assert resp.gross_npa_ratio is None
    assert resp.net_npa_ratio is None
    assert resp.fund_utilization_percentage is None
    assert resp.npa_risk_indicator == PartnerNPARiskLevel.UNKNOWN.value
    assert "never fabricated" in resp.disclosure.lower()


@pytest.mark.asyncio
async def test_npa_valid_live_response_parsing(monkeypatch, banking_test_setup):
    """Configured NPA provider parses real NPA ratios, risk indicator, and lending halt state."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="secret")

    class MockAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None):
            class Res:
                status_code = 200
                def json(self):
                    return {
                        "fund_allocation_inr": 50000000,
                        "fund_utilized_inr": 37500000,
                        "fund_utilization_percentage": 75.0,
                        "gross_npa_ratio": 2.1,
                        "net_npa_ratio": 0.8,
                        "npa_risk_indicator": "LOW",
                        "is_lending_halted": False
                    }
            return Res()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    resp = await provider.fetch_npa_fund_utilization(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name
    )

    assert resp.sync_status == BankingDataSyncStatus.LIVE.value
    assert resp.is_authenticated_live is True
    assert resp.gross_npa_ratio == Decimal("2.1")
    assert resp.net_npa_ratio == Decimal("0.8")
    assert resp.fund_utilization_percentage == Decimal("75.0")
    assert resp.npa_risk_indicator == "LOW"
    assert resp.is_lending_halted is False


def test_npa_endpoint_integration(client: TestClient, banking_test_setup):
    """GET /integrations/banking/partner/{partner_id}/npa-utilization endpoint test."""
    partner = banking_test_setup["partner"]
    headers = banking_test_setup["user_headers"]

    res = client.get(f"/integrations/banking/partner/{partner.id}/npa-utilization", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["partner_name"] == partner.name
    assert "disclosure" in data


# ============================================================================
# 3. PARTNER LENDING CAPACITY ADAPTER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_lending_capacity_unconfigured_never_fabricates_quotas(banking_test_setup):
    """Unconfigured capacity provider returns None quotas and UNVERIFIED tier."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="", api_key="")

    resp = await provider.fetch_partner_lending_capacity(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name
    )

    assert resp.sync_status == BankingDataSyncStatus.CONFIGURATION_READY.value
    assert resp.is_authenticated_live is False
    assert resp.sanctioned_quota_inr is None
    assert resp.available_lending_capacity_inr is None
    assert resp.capacity_tier == PartnerCapacityTier.UNVERIFIED.value
    assert "No synthetic capacity" in resp.disclosure


@pytest.mark.asyncio
async def test_lending_capacity_valid_live_response_parsing(monkeypatch, banking_test_setup):
    """Configured capacity provider parses real quotas and capacity tier."""
    partner = banking_test_setup["partner"]
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="secret")

    class MockAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None):
            class Res:
                status_code = 200
                def json(self):
                    return {
                        "sanctioned_quota_inr": 100000000,
                        "allocated_quota_inr": 60000000,
                        "available_lending_capacity_inr": 40000000,
                        "capacity_tier": "HIGH",
                        "is_lending_halted": False
                    }
            return Res()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    resp = await provider.fetch_partner_lending_capacity(
        partner_id=partner.id,
        partner_code=partner.code,
        partner_name=partner.name
    )

    assert resp.sync_status == BankingDataSyncStatus.LIVE.value
    assert resp.is_authenticated_live is True
    assert resp.sanctioned_quota_inr == Decimal("100000000")
    assert resp.available_lending_capacity_inr == Decimal("40000000")
    assert resp.capacity_tier == "HIGH"


def test_lending_capacity_endpoint_integration(client: TestClient, banking_test_setup):
    """GET /integrations/banking/partner/{partner_id}/lending-capacity endpoint test."""
    partner = banking_test_setup["partner"]
    headers = banking_test_setup["user_headers"]

    res = client.get(f"/integrations/banking/partner/{partner.id}/lending-capacity", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["partner_name"] == partner.name
    assert "capacity_tier" in data


# ============================================================================
# 4. PFMS / DBT STATUS ADAPTER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_pfms_unconfigured_never_fabricates_utr(banking_test_setup):
    """Unconfigured PFMS adapter must never fabricate UTRs or credit amounts."""
    adapter = DirectPFMSGatewayAdapter(api_url="", api_key="")
    assert not adapter.is_configured()

    resp = await adapter.query_disbursement_status(
        application_id=uuid.uuid4(),
        partner_reference_code="YOJ-REF-1234"
    )

    assert resp.dbt_status == "CONFIGURATION_READY"
    assert resp.sync_status == "CONFIGURATION_READY"
    assert resp.is_authenticated_live is False
    assert resp.transaction_utr is None
    assert resp.pfms_payment_id is None
    assert resp.amount_inr is None
    assert "No synthetic or unverified transaction data is fabricated" in resp.disclosure


@pytest.mark.asyncio
async def test_pfms_valid_live_disbursement_response(monkeypatch):
    """Configured PFMS adapter parses real UTR and settlement metadata."""
    adapter = DirectPFMSGatewayAdapter(api_url="https://pfms.nic.in/api", api_key="pfms-secret-token")
    assert adapter.is_configured()

    class MockAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None):
            class Res:
                status_code = 200
                def json(self):
                    return {
                        "dbt_status": "BENEFICIARY_CREDITED",
                        "amount_inr": 250000.0,
                        "transaction_utr": "PFMS202609100098765",
                        "pfms_payment_id": "PAY-ID-88990",
                        "credit_timestamp": "2026-09-10T05:30:00+00:00",
                        "bank_name": "State Bank of India",
                        "account_number_masked": "XXXXXX4321"
                    }
            return Res()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    resp = await adapter.query_disbursement_status(partner_reference_code="REF-001")
    assert resp.sync_status == "LIVE"
    assert resp.is_authenticated_live is True
    assert resp.dbt_status == "BENEFICIARY_CREDITED"
    assert resp.transaction_utr == "PFMS202609100098765"
    assert resp.amount_inr == Decimal("250000.0")
    assert resp.bank_name == "State Bank of India"


@pytest.mark.asyncio
async def test_pfms_unavailable_gateway_handles_gracefully(monkeypatch):
    """PFMS gateway timeout or 500 error returns UNAVAILABLE without fabricating data."""
    adapter = DirectPFMSGatewayAdapter(api_url="https://pfms.nic.in/api", api_key="pfms-key")

    class MockAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url, headers=None, params=None):
            raise Exception("PFMS gateway connection timed out")

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    resp = await adapter.query_disbursement_status(partner_reference_code="REF-001")
    assert resp.dbt_status == "UNAVAILABLE"
    assert resp.sync_status == "FALLBACK"
    assert resp.is_authenticated_live is False
    assert resp.transaction_utr is None
    assert "timed out" in resp.error_details


def test_pfms_endpoint_cross_user_unauthorized_blocked(client: TestClient, banking_test_setup):
    """A citizen must be blocked from querying disbursement of another citizen's application."""
    app_record = banking_test_setup["application"]
    other_headers = banking_test_setup["other_headers"]

    payload = {
        "application_id": str(app_record.id),
        "partner_reference_code": "YOJ-CANARA-7788"
    }

    # Attempt query with other user's token -> 403 Forbidden
    res = client.post("/integrations/pfms/dbt-status", json=payload, headers=other_headers)
    assert res.status_code == 403
    assert "Unauthorized" in res.json()["detail"]


def test_pfms_endpoint_authorized_citizen_and_admin_allowed(client: TestClient, banking_test_setup):
    """Owner citizen and admin are permitted to query PFMS disbursement status."""
    app_record = banking_test_setup["application"]
    user_headers = banking_test_setup["user_headers"]
    admin_headers = banking_test_setup["admin_headers"]

    payload = {
        "application_id": str(app_record.id),
        "partner_reference_code": "YOJ-CANARA-7788"
    }

    # 1. Citizen owner
    res_owner = client.post("/integrations/pfms/dbt-status", json=payload, headers=user_headers)
    assert res_owner.status_code == 200
    assert res_owner.json()["dbt_status"] in ["CONFIGURATION_READY", "LIVE", "UNAVAILABLE"]

    # 2. Admin
    res_admin = client.post("/integrations/pfms/dbt-status", json=payload, headers=admin_headers)
    assert res_admin.status_code == 200


# ============================================================================
# 5. SECURE AUTHENTICATED WEBHOOKS TESTS
# ============================================================================

def _generate_hmac_header(secret: str, raw_body: bytes) -> str:
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def test_webhook_banking_valid_signature_updates_telemetry(client: TestClient, test_db, monkeypatch, banking_test_setup):
    """Valid HMAC signature + fresh timestamp updates institution telemetry and writes AuditLog."""
    partner = banking_test_setup["partner"]
    secret = "banking-webhook-test-secret-32-chars-long"
    monkeypatch.setattr(settings, "BANKING_WEBHOOK_SECRET", secret)

    event_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    payload_dict = {
        "event_id": event_id,
        "event_type": "PARTNER_METRICS_UPDATED",
        "timestamp": now_iso,
        "source": "cbs_webhook_gateway",
        "data": {
            "partner_id": str(partner.id),
            "fund_utilization_percentage": 68.4,
            "available_lending_capacity_inr": 45000000,
            "capacity_tier": "HIGH",
            "gross_npa_ratio": 1.9,
            "net_npa_ratio": 0.7,
            "npa_risk_indicator": "LOW",
            "is_lending_halted": False
        }
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig_header = _generate_hmac_header(secret, raw_body)

    res = client.post(
        "/integrations/webhooks/banking",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": sig_header}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["event_id"] == event_id
    assert data["audit_logged"] is True

    # Verify DB update on Institution
    test_db.refresh(partner)
    assert partner.fund_utilization_percentage == Decimal("68.4")
    assert partner.capacity_tier == "HIGH"
    assert partner.is_authenticated_live is True

    # Verify AuditLog entry
    audit = test_db.query(AuditLog).filter(AuditLog.action == "WEBHOOK_PROCESSED:PARTNER_METRICS_UPDATED").first()
    assert audit is not None
    assert audit.details["event_id"] == event_id


def test_webhook_pfms_settled_transitions_application_to_disbursed(client: TestClient, test_db, monkeypatch, banking_test_setup):
    """Valid PFMS settled webhook updates application state to DISBURSED with real UTR."""
    app_record = banking_test_setup["application"]
    secret = "pfms-webhook-test-secret-32-chars-long"
    monkeypatch.setattr(settings, "PFMS_WEBHOOK_SECRET", secret)

    event_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    utr_val = "PFMS-UTR-2026-LIVE-8899"

    payload_dict = {
        "event_id": event_id,
        "event_type": "PFMS_DISBURSEMENT_SETTLED",
        "timestamp": now_iso,
        "source": "pfms_central_switch",
        "data": {
            "application_id": str(app_record.id),
            "transaction_utr": utr_val,
            "amount_inr": 150000.0,
            "pfms_payment_id": "PFMS-PID-0091",
            "bank_name": "Canara Bank",
            "account_last_four": "5566"
        }
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig_header = _generate_hmac_header(secret, raw_body)

    res = client.post(
        "/integrations/webhooks/pfms",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig_header}
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    test_db.refresh(app_record)
    assert app_record.status == "disbursed"
    disb_prog = app_record.form_data.get("disbursement_progress", {})
    assert disb_prog.get("status") == "DISBURSED"
    assert disb_prog.get("utr") == utr_val


def test_webhook_unauthorized_bad_signature_rejected(client: TestClient, monkeypatch):
    """Webhook with invalid or forged HMAC signature must be rejected with 401."""
    secret = "legitimate-secret-32-chars-long"
    monkeypatch.setattr(settings, "BANKING_WEBHOOK_SECRET", secret)

    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "LENDING_HALTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"partner_code": "SBI-001", "is_lending_halted": True}
    }
    raw_body = json.dumps(payload).encode("utf-8")
    bad_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    res = client.post(
        "/integrations/webhooks/banking",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": bad_sig}
    )
    assert res.status_code == 401
    assert "Invalid or missing" in res.json()["detail"]


def test_webhook_unauthorized_missing_signature_rejected(client: TestClient, monkeypatch):
    """Webhook without any signature header must be rejected with 401."""
    monkeypatch.setattr(settings, "BANKING_WEBHOOK_SECRET", "valid-secret-32-chars")

    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "CAPACITY_UPDATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {}
    }
    res = client.post("/integrations/webhooks/banking", json=payload)
    assert res.status_code == 401


def test_webhook_unconfigured_secret_rejected_with_503(client: TestClient, monkeypatch):
    """When webhook secret is unconfigured on server, incoming webhooks are rejected with 503."""
    monkeypatch.setattr(settings, "BANKING_WEBHOOK_SECRET", "")

    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "CAPACITY_UPDATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {}
    }
    raw_body = json.dumps(payload).encode("utf-8")
    res = client.post(
        "/integrations/webhooks/banking",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": "sha256=abc"}
    )
    assert res.status_code == 503
    assert "not configured" in res.json()["detail"]


def test_webhook_replay_attack_expired_timestamp_rejected(client: TestClient, monkeypatch):
    """Webhook with timestamp older than max age (300s) must be rejected with 400."""
    secret = "valid-secret-key-32-chars-long"
    monkeypatch.setattr(settings, "BANKING_WEBHOOK_SECRET", secret)
    monkeypatch.setattr(settings, "INTEGRATIONS_WEBHOOK_MAX_AGE_SECONDS", 300)

    # Stale timestamp: 10 minutes ago
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "CAPACITY_UPDATED",
        "timestamp": stale_timestamp,
        "data": {}
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _generate_hmac_header(secret, raw_body)

    res = client.post(
        "/integrations/webhooks/banking",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower() or "tolerance" in res.json()["detail"].lower()


def test_webhook_idempotency_duplicate_event_skipped(client: TestClient, monkeypatch):
    """Sending the same event_id twice must be processed idempotently without duplicate side effects."""
    secret = "idempotency-test-secret-32-chars"
    monkeypatch.setattr(settings, "BANKING_WEBHOOK_SECRET", secret)

    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "event_type": "CAPACITY_UPDATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"available_lending_capacity_inr": 5000000}
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = _generate_hmac_header(secret, raw_body)

    # 1. First execution
    res1 = client.post(
        "/integrations/webhooks/banking",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert res1.status_code == 200

    # 2. Second execution with identical event_id
    res2 = client.post(
        "/integrations/webhooks/banking",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert res2.status_code == 200
    assert "idempotently" in res2.json()["message"]


# ============================================================================
# 6. INTEGRATION STATUS PORTAL LISTING VERIFICATION
# ============================================================================

def test_all_official_integration_portals_listed(client: TestClient):
    """GET /integrations/status must report accurate connection statuses for all 7 portals."""
    res = client.get("/integrations/status")
    assert res.status_code == 200
    portals = res.json()
    assert len(portals) >= 7

    portal_map = {p["service_name"]: p for p in portals}
    assert "DigiLocker (National Digital Locker)" in portal_map
    assert "UIDAI Aadhaar Verification" in portal_map
    assert "Income Tax Department PAN Verification" in portal_map
    assert "Ministry of MSME UDYAM Portal" in portal_map
    assert "National Scheme Gazette & DBT Sync" in portal_map
    assert "National Core Banking (CBS) & SCA Live Gateway" in portal_map
    assert "Public Financial Management System (PFMS / DBT)" in portal_map

    cbs_portal = portal_map["National Core Banking (CBS) & SCA Live Gateway"]
    assert cbs_portal["status"] in ["connected", "unconfigured"]
    assert "official_portal_url" in cbs_portal

    pfms_portal = portal_map["Public Financial Management System (PFMS / DBT)"]
    assert pfms_portal["status"] in ["connected", "unconfigured"]
    assert pfms_portal["official_portal_url"] == "https://pfms.nic.in"
