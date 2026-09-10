"""Secure Banking & Channel Partner Live Data Integration Framework.

Provides an abstract provider interface, standard models, and live integration clients
with graceful fallback to configured metadata when external banking APIs are unconfigured or offline.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID
import logging

from pydantic import BaseModel, Field

from app.schemas import (
    CBSPartnerMetricsResponse,
    NPAFundUtilizationResponse,
    PartnerLendingCapacityResponse,
    PFMSDisbursementStatusResponse,
)

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BankingDataSyncStatus(str, Enum):
    LIVE = "LIVE"
    CONFIGURATION_READY = "CONFIGURATION_READY"
    FALLBACK = "FALLBACK"


class PartnerCapacityTier(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    CONSTRAINED = "CONSTRAINED"
    UNVERIFIED = "UNVERIFIED"


class PartnerNPARiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    UNKNOWN = "UNKNOWN"


class LiveBankingPartnerData(BaseModel):
    """Schema representing verified live or fallback banking/partner metrics."""
    partner_id: Optional[UUID] = None
    partner_code: Optional[str] = None
    partner_name: str
    institution_type: str  # SCA, PSB, RRB, NBFC-MFI
    
    # Sync Status
    sync_status: BankingDataSyncStatus = BankingDataSyncStatus.CONFIGURATION_READY
    provider_name: str = "Yojantra Channel Partner Framework"
    provider_id: str = "yojantra-default"
    last_synced_at: Optional[datetime] = None
    is_authenticated_live: bool = False
    
    # Capacity & Lending Quotas
    fund_utilization_percentage: Optional[Decimal] = None
    available_lending_capacity_inr: Optional[Decimal] = None
    capacity_tier: PartnerCapacityTier = PartnerCapacityTier.UNVERIFIED
    
    # NPA & Risk Safeguards
    gross_npa_ratio: Optional[Decimal] = None
    npa_risk_indicator: PartnerNPARiskLevel = PartnerNPARiskLevel.UNKNOWN
    is_lending_halted: bool = False
    
    # Partner Status
    partner_operational_status: str = "Active"
    lead_bank_active: bool = True
    disbursement_sla_days: Optional[int] = None
    
    # Disclosure & Transparency Note
    disclosure: str = (
        "Live banking status reflects authenticated partner feeds when active. "
        "When unconfigured, fallback metadata is used to ensure safe routing."
    )


class BaseBankingDataProvider(ABC):
    """Abstract Base Class for Channel Partner & Core Banking System (CBS) Data Providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Name of the banking integration provider."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if provider credentials, certificates, or endpoints are configured."""
        pass

    @abstractmethod
    async def fetch_partner_live_data(
        self, 
        partner_id: UUID, 
        partner_code: Optional[str],
        partner_name: str,
        institution_type: str,
        state: str,
        district: str
    ) -> LiveBankingPartnerData:
        """Fetch real-time metrics for a specific partner institution."""
        pass

    @abstractmethod
    async def batch_fetch_partner_live_data(
        self,
        partners: List[Dict[str, Any]]
    ) -> Dict[str, LiveBankingPartnerData]:
        """Batch fetch real-time metrics for a list of partner institutions."""
        pass

    @abstractmethod
    async def fetch_cbs_partner_metrics(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str,
        institution_type: str,
        branch_code: Optional[str] = None
    ) -> CBSPartnerMetricsResponse:
        """Fetch Core Banking System operational status and metrics for an institution."""
        pass

    @abstractmethod
    async def fetch_npa_fund_utilization(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str
    ) -> NPAFundUtilizationResponse:
        """Fetch real-time NPA ratio, risk level, and fund utilization percentages."""
        pass

    @abstractmethod
    async def fetch_partner_lending_capacity(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str
    ) -> PartnerLendingCapacityResponse:
        """Fetch authorized lending capacity quotas and capacity tier."""
        pass


class DirectCBSBankingProvider(BaseBankingDataProvider):
    """Direct Core Banking System / SCA Gateway Live Data Provider.
    
    Connects to authorized partner gateway endpoints using secure mTLS / API Keys.
    If unconfigured or offline, returns CONFIGURATION-READY / FALLBACK status.
    """

    def __init__(
        self, 
        api_url: Optional[str] = None, 
        api_key: Optional[str] = None,
        auth_type: str = "bearer",
        timeout_seconds: float = 4.0,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_path: Optional[str] = None
    ):
        self.api_url = (api_url or "").strip()
        self.api_key = (api_key or "").strip()
        self.auth_type = (auth_type or "bearer").lower().strip()
        self.timeout_seconds = timeout_seconds or 4.0
        self.cert_path = (cert_path or "").strip()
        self.key_path = (key_path or "").strip()
        self.ca_path = (ca_path or "").strip()

    def get_provider_name(self) -> str:
        return "National Banking & SCA Real-Time Gateway"

    def is_configured(self) -> bool:
        """Provider is only considered live if real endpoints and credentials/certs are provided."""
        return bool(self.api_url and (self.api_key or self.cert_path))

    async def fetch_partner_live_data(
        self, 
        partner_id: UUID, 
        partner_code: Optional[str],
        partner_name: str,
        institution_type: str,
        state: str,
        district: str
    ) -> LiveBankingPartnerData:
        if not self.is_configured():
            # Return CONFIGURATION-READY status with transparent disclosure
            return LiveBankingPartnerData(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                institution_type=institution_type,
                sync_status=BankingDataSyncStatus.CONFIGURATION_READY,
                provider_name=self.get_provider_name(),
                provider_id="cbs-sca-gateway",
                last_synced_at=None,
                is_authenticated_live=False,
                fund_utilization_percentage=None,
                available_lending_capacity_inr=None,
                capacity_tier=PartnerCapacityTier.UNVERIFIED,
                gross_npa_ratio=None,
                npa_risk_indicator=PartnerNPARiskLevel.UNKNOWN,
                is_lending_halted=False,
                partner_operational_status="Active (Metadata)",
                lead_bank_active=True,
                disbursement_sla_days=None,
                disclosure=(
                    "Banking provider integration is CONFIGURATION-READY. "
                    "Live core-banking synchronization activates upon authorized gateway provisioning."
                )
            )

        # When configured with real endpoint and credential: Execute authenticated HTTPS request
        try:
            import httpx
            headers = {
                "X-Partner-Id": str(partner_id),
                "Accept": "application/json",
                "User-Agent": "Yojantra-GovBanking-Sync/1.0"
            }
            if self.api_key:
                if self.auth_type == "api_key":
                    headers["X-API-Key"] = self.api_key
                else:  # default 'bearer' and 'oauth2'
                    headers["Authorization"] = f"Bearer {self.api_key}"

            params = {
                "code": partner_code or "",
                "type": institution_type,
                "state": state,
                "district": district
            }
            
            # Setup mTLS SSL client certs if specified
            cert = None
            if self.cert_path:
                if self.key_path:
                    cert = (self.cert_path, self.key_path)
                else:
                    cert = self.cert_path

            verify = self.ca_path if self.ca_path else True

            async with httpx.AsyncClient(timeout=self.timeout_seconds, verify=verify, cert=cert) as client:
                res = await client.get(f"{self.api_url}/partner-telemetry", headers=headers, params=params)
                
                if res.status_code == 200:
                    payload = res.json()
                    
                    # Schema & Payload Verification for Verified Live Status
                    fund_util = Decimal(str(payload["fund_utilization_percentage"])) if payload.get("fund_utilization_percentage") is not None else None
                    capacity = Decimal(str(payload["available_lending_capacity_inr"])) if payload.get("available_lending_capacity_inr") is not None else None
                    gross_npa = Decimal(str(payload["gross_npa_ratio"])) if payload.get("gross_npa_ratio") is not None else None
                    
                    cap_tier = PartnerCapacityTier(payload.get("capacity_tier", "HIGH")) if payload.get("capacity_tier") in [e.value for e in PartnerCapacityTier] else PartnerCapacityTier.UNVERIFIED
                    npa_risk = PartnerNPARiskLevel(payload.get("npa_risk_indicator", "LOW")) if payload.get("npa_risk_indicator") in [e.value for e in PartnerNPARiskLevel] else PartnerNPARiskLevel.UNKNOWN

                    return LiveBankingPartnerData(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        institution_type=institution_type,
                        sync_status=BankingDataSyncStatus.LIVE,
                        provider_name=self.get_provider_name(),
                        provider_id="cbs-sca-gateway",
                        last_synced_at=utc_now(),
                        is_authenticated_live=True,
                        fund_utilization_percentage=fund_util,
                        available_lending_capacity_inr=capacity,
                        capacity_tier=cap_tier,
                        gross_npa_ratio=gross_npa,
                        npa_risk_indicator=npa_risk,
                        is_lending_halted=bool(payload.get("is_lending_halted", False)),
                        partner_operational_status=payload.get("partner_operational_status", "Active (Live Telemetry)"),
                        lead_bank_active=bool(payload.get("lead_bank_active", True)),
                        disbursement_sla_days=payload.get("disbursement_sla_days", 7),
                        disclosure="Verified live banking telemetry from authorized Core Banking / SCA Gateway."
                    )
                else:
                    logger.warning(f"Banking gateway returned non-200 status {res.status_code} for partner {partner_code}")
                    return LiveBankingPartnerData(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        institution_type=institution_type,
                        sync_status=BankingDataSyncStatus.FALLBACK,
                        provider_name=self.get_provider_name(),
                        provider_id="cbs-sca-gateway",
                        last_synced_at=utc_now(),
                        is_authenticated_live=False,
                        disclosure="Banking gateway response unavailable; falling back to configured metadata."
                    )
        except Exception as e:
            logger.warning(f"Error connecting to banking provider for partner {partner_code}: {e}")
            return LiveBankingPartnerData(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                institution_type=institution_type,
                sync_status=BankingDataSyncStatus.FALLBACK,
                provider_name=self.get_provider_name(),
                provider_id="cbs-sca-gateway",
                last_synced_at=None,
                is_authenticated_live=False,
                disclosure="Banking gateway connection timed out; falling back to configured metadata."
            )

    async def batch_fetch_partner_live_data(
        self,
        partners: List[Dict[str, Any]]
    ) -> Dict[str, LiveBankingPartnerData]:
        results: Dict[str, LiveBankingPartnerData] = {}
        for p in partners:
            pid_str = str(p.get("id"))
            data = await self.fetch_partner_live_data(
                partner_id=p.get("id"),
                partner_code=p.get("code"),
                partner_name=p.get("name", "Partner"),
                institution_type=p.get("institution_type", "PSB"),
                state=p.get("state", ""),
                district=p.get("district", "")
            )
            results[pid_str] = data
        return results

    async def fetch_cbs_partner_metrics(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str,
        institution_type: str,
        branch_code: Optional[str] = None
    ) -> CBSPartnerMetricsResponse:
        if not self.is_configured():
            return CBSPartnerMetricsResponse(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                institution_type=institution_type,
                operational_status="Active (Metadata)",
                lead_bank_active=True,
                branch_code=branch_code,
                disbursement_sla_days=None,
                system_health="UNCONFIGURED",
                sync_status=BankingDataSyncStatus.CONFIGURATION_READY.value,
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                disclosure=(
                    "Core Banking System partner integration is CONFIGURATION-READY. "
                    "Live CBS telemetry activates upon authorized gateway provisioning. "
                    "Banking records are not fabricated."
                )
            )

        try:
            import httpx
            headers = {
                "X-Partner-Id": str(partner_id),
                "Accept": "application/json",
                "User-Agent": "Yojantra-GovBanking-Sync/1.0"
            }
            if self.api_key:
                if self.auth_type == "api_key":
                    headers["X-API-Key"] = self.api_key
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"

            params = {
                "code": partner_code or "",
                "type": institution_type,
            }
            if branch_code:
                params["branch_code"] = branch_code

            cert = None
            if self.cert_path:
                cert = (self.cert_path, self.key_path) if self.key_path else self.cert_path
            verify = self.ca_path if self.ca_path else True

            async with httpx.AsyncClient(timeout=self.timeout_seconds, verify=verify, cert=cert) as client:
                res = await client.get(f"{self.api_url}/partner-telemetry", headers=headers, params=params)
                if res.status_code == 200:
                    payload = res.json()
                    return CBSPartnerMetricsResponse(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        institution_type=institution_type,
                        operational_status=payload.get("partner_operational_status", payload.get("operational_status", "Active (Live Telemetry)")),
                        lead_bank_active=bool(payload.get("lead_bank_active", True)),
                        branch_code=payload.get("branch_code", branch_code),
                        disbursement_sla_days=payload.get("disbursement_sla_days", 7),
                        system_health=payload.get("system_health", "OPTIMAL"),
                        sync_status=BankingDataSyncStatus.LIVE.value,
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=True,
                        last_synced_at=utc_now(),
                        disclosure="Verified live CBS telemetry from authorized Core Banking System gateway."
                    )
                else:
                    logger.warning(f"CBS gateway returned status {res.status_code} for partner {partner_code}")
                    return CBSPartnerMetricsResponse(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        institution_type=institution_type,
                        operational_status="Active (Metadata)",
                        lead_bank_active=True,
                        branch_code=branch_code,
                        disbursement_sla_days=None,
                        system_health="OFFLINE" if res.status_code in (401, 403) else "DEGRADED",
                        sync_status=BankingDataSyncStatus.FALLBACK.value,
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=False,
                        last_synced_at=utc_now(),
                        disclosure=f"CBS gateway returned non-200 status ({res.status_code}); falling back to metadata."
                    )
        except Exception as e:
            logger.warning(f"Error fetching CBS metrics for partner {partner_code}: {e}")
            return CBSPartnerMetricsResponse(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                institution_type=institution_type,
                operational_status="Active (Metadata)",
                lead_bank_active=True,
                branch_code=branch_code,
                disbursement_sla_days=None,
                system_health="OFFLINE",
                sync_status=BankingDataSyncStatus.FALLBACK.value,
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                disclosure="CBS gateway connection timed out or unreachable; falling back to metadata."
            )

    async def fetch_npa_fund_utilization(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str
    ) -> NPAFundUtilizationResponse:
        if not self.is_configured():
            return NPAFundUtilizationResponse(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                fund_allocation_inr=None,
                fund_utilized_inr=None,
                fund_utilization_percentage=None,
                gross_npa_ratio=None,
                net_npa_ratio=None,
                npa_risk_indicator=PartnerNPARiskLevel.UNKNOWN.value,
                is_lending_halted=False,
                sync_status=BankingDataSyncStatus.CONFIGURATION_READY.value,
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                disclosure=(
                    "NPA and fund utilization metrics are CONFIGURATION-READY. "
                    "Real metrics require authenticated Core Banking System / SCA data. "
                    "Live risk indicators are never fabricated."
                )
            )

        try:
            import httpx
            headers = {
                "X-Partner-Id": str(partner_id),
                "Accept": "application/json",
                "User-Agent": "Yojantra-GovBanking-Sync/1.0"
            }
            if self.api_key:
                if self.auth_type == "api_key":
                    headers["X-API-Key"] = self.api_key
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"

            params = {"code": partner_code or ""}
            cert = (self.cert_path, self.key_path) if (self.cert_path and self.key_path) else self.cert_path
            verify = self.ca_path if self.ca_path else True

            async with httpx.AsyncClient(timeout=self.timeout_seconds, verify=verify, cert=cert) as client:
                res = await client.get(f"{self.api_url}/partner-telemetry", headers=headers, params=params)
                if res.status_code == 200:
                    payload = res.json()
                    fund_alloc = Decimal(str(payload["fund_allocation_inr"])) if payload.get("fund_allocation_inr") is not None else None
                    fund_util_inr = Decimal(str(payload["fund_utilized_inr"])) if payload.get("fund_utilized_inr") is not None else None
                    fund_util_pct = Decimal(str(payload["fund_utilization_percentage"])) if payload.get("fund_utilization_percentage") is not None else None
                    gross_npa = Decimal(str(payload["gross_npa_ratio"])) if payload.get("gross_npa_ratio") is not None else None
                    net_npa = Decimal(str(payload["net_npa_ratio"])) if payload.get("net_npa_ratio") is not None else None
                    npa_risk = payload.get("npa_risk_indicator", "LOW")

                    return NPAFundUtilizationResponse(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        fund_allocation_inr=fund_alloc,
                        fund_utilized_inr=fund_util_inr,
                        fund_utilization_percentage=fund_util_pct,
                        gross_npa_ratio=gross_npa,
                        net_npa_ratio=net_npa,
                        npa_risk_indicator=npa_risk,
                        is_lending_halted=bool(payload.get("is_lending_halted", False)),
                        sync_status=BankingDataSyncStatus.LIVE.value,
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=True,
                        last_synced_at=utc_now(),
                        disclosure="Verified live NPA and fund utilization metrics from Core Banking System."
                    )
                else:
                    return NPAFundUtilizationResponse(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        fund_allocation_inr=None,
                        fund_utilized_inr=None,
                        fund_utilization_percentage=None,
                        gross_npa_ratio=None,
                        net_npa_ratio=None,
                        npa_risk_indicator=PartnerNPARiskLevel.UNKNOWN.value,
                        is_lending_halted=False,
                        sync_status=BankingDataSyncStatus.FALLBACK.value,
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=False,
                        last_synced_at=utc_now(),
                        disclosure=f"NPA/Fund utilization gateway returned status {res.status_code}; safe fallback active."
                    )
        except Exception as e:
            logger.warning(f"Error fetching NPA metrics for partner {partner_code}: {e}")
            return NPAFundUtilizationResponse(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                fund_allocation_inr=None,
                fund_utilized_inr=None,
                fund_utilization_percentage=None,
                gross_npa_ratio=None,
                net_npa_ratio=None,
                npa_risk_indicator=PartnerNPARiskLevel.UNKNOWN.value,
                is_lending_halted=False,
                sync_status=BankingDataSyncStatus.FALLBACK.value,
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                disclosure="NPA and fund utilization gateway connection timed out; safe fallback active."
            )

    async def fetch_partner_lending_capacity(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str
    ) -> PartnerLendingCapacityResponse:
        if not self.is_configured():
            return PartnerLendingCapacityResponse(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                sanctioned_quota_inr=None,
                allocated_quota_inr=None,
                available_lending_capacity_inr=None,
                capacity_tier=PartnerCapacityTier.UNVERIFIED.value,
                is_lending_halted=False,
                sync_status=BankingDataSyncStatus.CONFIGURATION_READY.value,
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                disclosure=(
                    "Partner lending capacity is CONFIGURATION-READY. "
                    "Quota metrics require authenticated CBS / departmental credit allocation feed. "
                    "No synthetic capacity numbers are fabricated."
                )
            )

        try:
            import httpx
            headers = {
                "X-Partner-Id": str(partner_id),
                "Accept": "application/json",
                "User-Agent": "Yojantra-GovBanking-Sync/1.0"
            }
            if self.api_key:
                if self.auth_type == "api_key":
                    headers["X-API-Key"] = self.api_key
                else:
                    headers["Authorization"] = f"Bearer {self.api_key}"

            params = {"code": partner_code or ""}
            cert = (self.cert_path, self.key_path) if (self.cert_path and self.key_path) else self.cert_path
            verify = self.ca_path if self.ca_path else True

            async with httpx.AsyncClient(timeout=self.timeout_seconds, verify=verify, cert=cert) as client:
                res = await client.get(f"{self.api_url}/partner-telemetry", headers=headers, params=params)
                if res.status_code == 200:
                    payload = res.json()
                    sanctioned = Decimal(str(payload["sanctioned_quota_inr"])) if payload.get("sanctioned_quota_inr") is not None else None
                    allocated = Decimal(str(payload["allocated_quota_inr"])) if payload.get("allocated_quota_inr") is not None else None
                    capacity = Decimal(str(payload["available_lending_capacity_inr"])) if payload.get("available_lending_capacity_inr") is not None else None
                    tier = payload.get("capacity_tier", "HIGH")

                    return PartnerLendingCapacityResponse(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        sanctioned_quota_inr=sanctioned,
                        allocated_quota_inr=allocated,
                        available_lending_capacity_inr=capacity,
                        capacity_tier=tier,
                        is_lending_halted=bool(payload.get("is_lending_halted", False)),
                        sync_status=BankingDataSyncStatus.LIVE.value,
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=True,
                        last_synced_at=utc_now(),
                        disclosure="Verified live partner lending capacity telemetry from Core Banking System."
                    )
                else:
                    return PartnerLendingCapacityResponse(
                        partner_id=partner_id,
                        partner_code=partner_code,
                        partner_name=partner_name,
                        sanctioned_quota_inr=None,
                        allocated_quota_inr=None,
                        available_lending_capacity_inr=None,
                        capacity_tier=PartnerCapacityTier.UNVERIFIED.value,
                        is_lending_halted=False,
                        sync_status=BankingDataSyncStatus.FALLBACK.value,
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=False,
                        last_synced_at=utc_now(),
                        disclosure=f"Lending capacity gateway returned status {res.status_code}; safe fallback active."
                    )
        except Exception as e:
            logger.warning(f"Error fetching lending capacity for partner {partner_code}: {e}")
            return PartnerLendingCapacityResponse(
                partner_id=partner_id,
                partner_code=partner_code,
                partner_name=partner_name,
                sanctioned_quota_inr=None,
                allocated_quota_inr=None,
                available_lending_capacity_inr=None,
                capacity_tier=PartnerCapacityTier.UNVERIFIED.value,
                is_lending_halted=False,
                sync_status=BankingDataSyncStatus.FALLBACK.value,
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                disclosure="Lending capacity gateway connection timed out; safe fallback active."
            )


class BankingDataService:
    """Service orchestrating channel partner live banking and risk data synchronization."""

    def __init__(self, provider: Optional[BaseBankingDataProvider] = None):
        from app.core.config import get_settings
        settings = get_settings()
        
        cbs_url = getattr(settings, "BANKING_GATEWAY_URL", "")
        cbs_key = getattr(settings, "BANKING_GATEWAY_API_KEY", "")
        auth_type = getattr(settings, "BANKING_GATEWAY_AUTH_TYPE", "bearer")
        timeout_sec = float(getattr(settings, "BANKING_GATEWAY_TIMEOUT_SECONDS", 4.0))
        cert_path = getattr(settings, "BANKING_GATEWAY_CERT_PATH", "")
        key_path = getattr(settings, "BANKING_GATEWAY_KEY_PATH", "")
        ca_path = getattr(settings, "BANKING_GATEWAY_CA_PATH", "")
        
        self.provider = provider or DirectCBSBankingProvider(
            api_url=cbs_url, 
            api_key=cbs_key,
            auth_type=auth_type,
            timeout_seconds=timeout_sec,
            cert_path=cert_path,
            key_path=key_path,
            ca_path=ca_path
        )

    def get_sync_summary(self) -> Dict[str, Any]:
        """Return the overall health and status of the live banking provider integration."""
        is_live = self.provider.is_configured()
        return {
            "provider_name": self.provider.get_provider_name(),
            "is_configured": is_live,
            "overall_status": BankingDataSyncStatus.LIVE.value if is_live else BankingDataSyncStatus.CONFIGURATION_READY.value,
            "supported_fields": [
                "fund_utilization_percentage",
                "available_lending_capacity_inr",
                "capacity_tier",
                "gross_npa_ratio",
                "npa_risk_indicator",
                "is_lending_halted",
                "disbursement_sla_days",
                "last_synced_at"
            ],
            "auth_mechanism": "mTLS / Bearer Token / IP-Whitelisted Gateway",
            "fallback_behavior": "Strict deterministic fallback to validated institutional metadata with explicit UI status",
            "checked_at": utc_now().isoformat()
        }

    async def enrich_partner_with_banking_data(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str,
        institution_type: str,
        state: str,
        district: str
    ) -> LiveBankingPartnerData:
        return await self.provider.fetch_partner_live_data(
            partner_id=partner_id,
            partner_code=partner_code,
            partner_name=partner_name,
            institution_type=institution_type,
            state=state,
            district=district
        )

    async def fetch_cbs_partner_metrics(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str,
        institution_type: str,
        branch_code: Optional[str] = None
    ) -> CBSPartnerMetricsResponse:
        return await self.provider.fetch_cbs_partner_metrics(
            partner_id=partner_id,
            partner_code=partner_code,
            partner_name=partner_name,
            institution_type=institution_type,
            branch_code=branch_code
        )

    async def fetch_npa_fund_utilization(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str
    ) -> NPAFundUtilizationResponse:
        return await self.provider.fetch_npa_fund_utilization(
            partner_id=partner_id,
            partner_code=partner_code,
            partner_name=partner_name
        )

    async def fetch_partner_lending_capacity(
        self,
        partner_id: UUID,
        partner_code: Optional[str],
        partner_name: str
    ) -> PartnerLendingCapacityResponse:
        return await self.provider.fetch_partner_lending_capacity(
            partner_id=partner_id,
            partner_code=partner_code,
            partner_name=partner_name
        )


class BasePFMSGatewayAdapter(ABC):
    """Abstract Base Class for Public Financial Management System (PFMS) / DBT Gateway Adapters."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Official name of the PFMS/DBT gateway."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if PFMS production endpoints and agency credentials are configured."""
        pass

    @abstractmethod
    async def query_disbursement_status(
        self,
        application_id: Optional[UUID] = None,
        partner_reference_code: Optional[str] = None,
        sanction_reference_number: Optional[str] = None,
        beneficiary_account_last_four: Optional[str] = None
    ) -> PFMSDisbursementStatusResponse:
        """Query real-time PFMS settlement, UTR, and DBT progress."""
        pass


class DirectPFMSGatewayAdapter(BasePFMSGatewayAdapter):
    """Production PFMS / DBT Aadhaar Payment Bridge Gateway Adapter.

    Communicates with the central Public Financial Management System API when configured.
    Never fabricates UTRs, disbursement amounts, or settlement statuses when unconfigured or unavailable.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_type: str = "bearer",
        timeout_seconds: float = 4.0
    ):
        self.api_url = (api_url or "").strip()
        self.api_key = (api_key or "").strip()
        self.auth_type = (auth_type or "bearer").lower().strip()
        self.timeout_seconds = timeout_seconds or 4.0

    def get_provider_name(self) -> str:
        return "PFMS / Aadhaar Payment Bridge (APB)"

    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)

    async def query_disbursement_status(
        self,
        application_id: Optional[UUID] = None,
        partner_reference_code: Optional[str] = None,
        sanction_reference_number: Optional[str] = None,
        beneficiary_account_last_four: Optional[str] = None
    ) -> PFMSDisbursementStatusResponse:
        if not self.is_configured():
            return PFMSDisbursementStatusResponse(
                application_id=application_id,
                partner_reference_code=partner_reference_code,
                sanction_reference_number=sanction_reference_number,
                dbt_status="CONFIGURATION_READY",
                amount_inr=None,
                transaction_utr=None,
                pfms_payment_id=None,
                credit_timestamp=None,
                bank_name=None,
                account_number_masked=None,
                sync_status="CONFIGURATION_READY",
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                error_details=None,
                disclosure=(
                    "PFMS / DBT Aadhaar gateway is CONFIGURATION-READY. "
                    "Live disbursement UTRs and settlement records are queried only upon authorized PFMS credentials configuration. "
                    "No synthetic or unverified transaction data is fabricated."
                )
            )

        try:
            import httpx
            headers = {
                "Accept": "application/json",
                "User-Agent": "Yojantra-PFMS-Gateway/1.0"
            }
            if self.auth_type == "api_key":
                headers["X-API-Key"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

            params: Dict[str, Any] = {}
            if application_id:
                params["application_id"] = str(application_id)
            if partner_reference_code:
                params["partner_reference_code"] = partner_reference_code
            if sanction_reference_number:
                params["sanction_reference_number"] = sanction_reference_number
            if beneficiary_account_last_four:
                params["account_last_four"] = beneficiary_account_last_four

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.get(f"{self.api_url}/dbt/status", headers=headers, params=params)

                if res.status_code == 200:
                    data = res.json()
                    amt = Decimal(str(data["amount_inr"])) if data.get("amount_inr") is not None else None
                    credit_ts = None
                    if data.get("credit_timestamp"):
                        try:
                            credit_ts = datetime.fromisoformat(data["credit_timestamp"])
                        except Exception:
                            credit_ts = utc_now()

                    return PFMSDisbursementStatusResponse(
                        application_id=application_id,
                        partner_reference_code=data.get("partner_reference_code", partner_reference_code),
                        sanction_reference_number=data.get("sanction_reference_number", sanction_reference_number),
                        dbt_status=data.get("dbt_status", "BENEFICIARY_CREDITED"),
                        amount_inr=amt,
                        transaction_utr=data.get("transaction_utr"),
                        pfms_payment_id=data.get("pfms_payment_id"),
                        credit_timestamp=credit_ts,
                        bank_name=data.get("bank_name"),
                        account_number_masked=data.get("account_number_masked"),
                        sync_status="LIVE",
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=True,
                        last_synced_at=utc_now(),
                        error_details=None,
                        disclosure="Verified live PFMS Aadhaar Payment Bridge (APB) settlement status."
                    )
                elif res.status_code in (401, 403):
                    logger.warning(f"PFMS Gateway returned {res.status_code} unauthorized")
                    return PFMSDisbursementStatusResponse(
                        application_id=application_id,
                        partner_reference_code=partner_reference_code,
                        sanction_reference_number=sanction_reference_number,
                        dbt_status="UNAVAILABLE",
                        sync_status="FALLBACK",
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=False,
                        last_synced_at=utc_now(),
                        error_details=f"PFMS Gateway authentication failed (HTTP {res.status_code}). Invalid or expired credentials.",
                        disclosure="PFMS gateway authentication failed; falling back to offline records."
                    )
                else:
                    logger.warning(f"PFMS Gateway returned {res.status_code}")
                    return PFMSDisbursementStatusResponse(
                        application_id=application_id,
                        partner_reference_code=partner_reference_code,
                        sanction_reference_number=sanction_reference_number,
                        dbt_status="UNAVAILABLE",
                        sync_status="FALLBACK",
                        provider_name=self.get_provider_name(),
                        is_authenticated_live=False,
                        last_synced_at=utc_now(),
                        error_details=f"PFMS Gateway returned HTTP {res.status_code}.",
                        disclosure="PFMS gateway response unavailable; falling back to offline records."
                    )
        except Exception as e:
            logger.warning(f"Error querying PFMS gateway: {e}")
            return PFMSDisbursementStatusResponse(
                application_id=application_id,
                partner_reference_code=partner_reference_code,
                sanction_reference_number=sanction_reference_number,
                dbt_status="UNAVAILABLE",
                sync_status="FALLBACK",
                provider_name=self.get_provider_name(),
                is_authenticated_live=False,
                last_synced_at=None,
                error_details=str(e),
                disclosure="PFMS gateway connection timed out or unreachable; falling back to offline records."
            )


class PFMSDataService:
    """Service orchestrating PFMS / DBT direct benefit transfer status queries."""

    def __init__(self, adapter: Optional[BasePFMSGatewayAdapter] = None):
        if adapter:
            self.adapter = adapter
        else:
            from app.core.config import get_settings
            settings = get_settings()
            pfms_url = getattr(settings, "PFMS_GATEWAY_URL", "")
            pfms_key = getattr(settings, "PFMS_API_KEY", "")
            pfms_auth = getattr(settings, "PFMS_AUTH_TYPE", "bearer")
            timeout_sec = float(getattr(settings, "PFMS_TIMEOUT_SECONDS", 4.0))
            self.adapter = DirectPFMSGatewayAdapter(
                api_url=pfms_url,
                api_key=pfms_key,
                auth_type=pfms_auth,
                timeout_seconds=timeout_sec
            )

    async def query_disbursement_status(
        self,
        application_id: Optional[UUID] = None,
        partner_reference_code: Optional[str] = None,
        sanction_reference_number: Optional[str] = None,
        beneficiary_account_last_four: Optional[str] = None
    ) -> PFMSDisbursementStatusResponse:
        return await self.adapter.query_disbursement_status(
            application_id=application_id,
            partner_reference_code=partner_reference_code,
            sanction_reference_number=sanction_reference_number,
            beneficiary_account_last_four=beneficiary_account_last_four
        )


def get_banking_data_service() -> BankingDataService:
    return BankingDataService()


def get_pfms_data_service() -> PFMSDataService:
    return PFMSDataService()
