"""Tests for Live Banking Data Provider Integration, Graceful Fallback & Channel Partner Quotas."""
import pytest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models import Institution, Scheme
from app.services.banking_service import (
    BankingDataService,
    DirectCBSBankingProvider,
    BankingDataSyncStatus,
    LiveBankingPartnerData,
    PartnerCapacityTier,
    PartnerNPARiskLevel
)


def test_banking_provider_unconfigured_defaults_to_configuration_ready(test_db):
    """When gateway URL and API key are empty, provider must report CONFIGURATION_READY."""
    provider = DirectCBSBankingProvider(api_url="", api_key="")
    assert provider.is_configured() is False

    service = BankingDataService(provider=provider)
    summary = service.get_sync_summary()

    assert summary["is_configured"] is False
    assert summary["overall_status"] == BankingDataSyncStatus.CONFIGURATION_READY.value
    assert "fund_utilization_percentage" in summary["supported_fields"]
    assert "available_lending_capacity_inr" in summary["supported_fields"]
    assert "npa_risk_indicator" in summary["supported_fields"]


@pytest.mark.asyncio
async def test_partner_enrichment_unconfigured_returns_safe_metadata():
    """Unconfigured provider must return CONFIGURATION_READY status with non-fabricated values."""
    provider = DirectCBSBankingProvider(api_url="", api_key="")
    partner_id = uuid.uuid4()

    data = await provider.fetch_partner_live_data(
        partner_id=partner_id,
        partner_code="PSB-SBI-001",
        partner_name="State Bank of India Main Branch",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune"
    )

    assert data.sync_status == BankingDataSyncStatus.CONFIGURATION_READY
    assert data.is_authenticated_live is False
    assert data.fund_utilization_percentage is None
    assert data.available_lending_capacity_inr is None
    assert data.capacity_tier == PartnerCapacityTier.UNVERIFIED
    assert data.npa_risk_indicator == PartnerNPARiskLevel.UNKNOWN
    assert "CONFIGURATION-READY" in data.disclosure


@pytest.mark.asyncio
async def test_partner_enrichment_offline_failure_returns_fallback_status():
    """When an authenticated provider fails/times out, it must return FALLBACK status."""
    # Configured with URL but unreachable
    provider = DirectCBSBankingProvider(api_url="https://mock.invalid.cbs.bank.gov.in/api", api_key="secret-key")
    assert provider.is_configured() is True

    partner_id = uuid.uuid4()
    data = await provider.fetch_partner_live_data(
        partner_id=partner_id,
        partner_code="RRB-KVG-002",
        partner_name="Karnataka Vikas Grameena Bank",
        institution_type="RRB",
        state="Karnataka",
        district="Dharwad"
    )

    assert data.sync_status == BankingDataSyncStatus.FALLBACK
    assert data.is_authenticated_live is False
    assert "falling back" in data.disclosure.lower() or "fallback" in data.disclosure.lower()


def test_partner_recommendations_api_includes_banking_sync_metadata(client: TestClient, test_db):
    """GET /api/institutions/recommendations must return banking sync summary and partner sync fields."""
    inst = Institution(
        id=uuid.uuid4(),
        name="Bank of Maharashtra Lead Bank",
        short_name="BOM Pune",
        code="BOM-77890",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        status="active"
    )
    test_db.add(inst)
    test_db.commit()

    resp = client.get("/api/institutions/recommendations?state=Maharashtra&district=Pune")
    assert resp.status_code == 200
    data = resp.json()

    assert "banking_integration_status" in data
    assert data["banking_integration_status"]["overall_status"] in ["LIVE", "CONFIGURATION_READY", "FALLBACK"]
    
    assert len(data["partners"]) > 0
    p0 = data["partners"][0]
    assert "sync_status" in p0
    assert p0["sync_status"] in ["LIVE", "CONFIGURATION_READY", "FALLBACK"]
    assert "capacity_tier" in p0
    assert "npa_risk_indicator" in p0
    assert "fund_disclosure" in p0


@pytest.mark.asyncio
async def test_authenticated_live_banking_response_parsing(monkeypatch):
    """When a real authorized provider returns 200 with schema payload, parser must emit VERIFIED LIVE."""
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="valid-bearer-token")
    partner_id = uuid.uuid4()

    mock_payload = {
        "fund_utilization_percentage": 68.5,
        "available_lending_capacity_inr": 25000000,
        "capacity_tier": "HIGH",
        "gross_npa_ratio": 2.4,
        "npa_risk_indicator": "LOW",
        "is_lending_halted": False,
        "partner_operational_status": "Active (Live Telemetry)",
        "lead_bank_active": True,
        "disbursement_sla_days": 5
    }

    class MockResponse:
        status_code = 200
        def json(self):
            return mock_payload

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, headers=None, params=None):
            return MockResponse()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    data = await provider.fetch_partner_live_data(
        partner_id=partner_id,
        partner_code="PSB-BOM-001",
        partner_name="Bank of Maharashtra Lead Bank",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune"
    )

    assert data.sync_status == BankingDataSyncStatus.LIVE
    assert data.is_authenticated_live is True
    assert data.fund_utilization_percentage == Decimal("68.5")
    assert data.available_lending_capacity_inr == Decimal("25000000")
    assert data.capacity_tier == PartnerCapacityTier.HIGH
    assert data.gross_npa_ratio == Decimal("2.4")
    assert data.npa_risk_indicator == PartnerNPARiskLevel.LOW
    assert data.is_lending_halted is False
    assert data.disbursement_sla_days == 5
    assert "Verified live" in data.disclosure


@pytest.mark.asyncio
async def test_reject_invalid_or_unauthenticated_banking_response(monkeypatch):
    """When an upstream server returns 401 Unauthorized or 500 error, provider must fall back safely."""
    provider = DirectCBSBankingProvider(api_url="https://cbs.bank.gov.in/api", api_key="invalid-key")
    partner_id = uuid.uuid4()

    class MockErrorResponse:
        status_code = 401
        def json(self):
            return {"error": "Invalid client certificate or expired API key"}

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, headers=None, params=None):
            return MockErrorResponse()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    data = await provider.fetch_partner_live_data(
        partner_id=partner_id,
        partner_code="PSB-BOM-001",
        partner_name="Bank of Maharashtra Lead Bank",
        institution_type="PSB",
        state="Maharashtra",
        district="Pune"
    )

    assert data.sync_status == BankingDataSyncStatus.FALLBACK
    assert data.is_authenticated_live is False
    assert "falling back" in data.disclosure.lower() or "unavailable" in data.disclosure.lower()


@pytest.mark.asyncio
async def test_api_key_and_mtls_auth_header_configuration(monkeypatch):
    """Provider configured with auth_type='api_key' must dispatch X-API-Key header and timeout settings."""
    captured_headers = {}
    
    class MockAsyncClient:
        def __init__(self, timeout=None, verify=None, cert=None):
            self.timeout = timeout
            self.verify = verify
            self.cert = cert

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, headers=None, params=None):
            nonlocal captured_headers
            captured_headers = headers or {}
            class Res:
                status_code = 200
                def json(self):
                    return {
                        "fund_utilization_percentage": 42.0,
                        "available_lending_capacity_inr": 10000000,
                        "capacity_tier": "HIGH",
                        "gross_npa_ratio": 1.5,
                        "npa_risk_indicator": "LOW",
                        "is_lending_halted": False
                    }
            return Res()

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    provider = DirectCBSBankingProvider(
        api_url="https://psb-gateway.bank.in",
        api_key="secret-api-key-value",
        auth_type="api_key",
        timeout_seconds=6.5,
        cert_path="/path/to/cert.pem",
        key_path="/path/to/key.pem"
    )

    data = await provider.fetch_partner_live_data(
        partner_id=uuid.uuid4(),
        partner_code="PSB-001",
        partner_name="State Bank of India",
        institution_type="PSB",
        state="Delhi",
        district="New Delhi"
    )

    assert data.sync_status == BankingDataSyncStatus.LIVE
    assert captured_headers.get("X-API-Key") == "secret-api-key-value"



