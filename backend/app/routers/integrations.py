"""Government Portals & Verification Integrations router."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models import User, Institution, Application
from app.schemas import (
    IntegrationStatusResponse,
    DigiLockerAuthURLResponse,
    AadhaarVerifyRequest,
    AadhaarVerifyResponse,
    PANVerifyRequest,
    PANVerifyResponse,
    UdyamVerifyRequest,
    UdyamVerifyResponse,
    GovSchemeSyncResponse,
    ApplicationStatusSyncResponse,
    CBSPartnerMetricsResponse,
    NPAFundUtilizationResponse,
    PartnerLendingCapacityResponse,
    PFMSDisbursementQueryRequest,
    PFMSDisbursementStatusResponse,
    InboundWebhookPayload,
    BankingWebhookResponse,
)
from app.services.integrations_service import (
    get_gov_integrations_service,
    get_banking_webhook_processor,
)
from app.services.banking_service import (
    get_banking_data_service,
    get_pfms_data_service,
)
from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/integrations", tags=["Government Integrations"])
webhook_limiter = RateLimiter(requests=120, window_seconds=60, key_prefix="rl_webhook")


@router.get("/status", response_model=List[IntegrationStatusResponse])
def get_integration_statuses(
    db: Session = Depends(get_db)
):
    """List status and connection tier for all official government portals."""
    service = get_gov_integrations_service(db)
    return service.list_integration_statuses()


@router.get("/digilocker/auth-url", response_model=DigiLockerAuthURLResponse)
def get_digilocker_auth_url(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate official DigiLocker OAuth2 redirect link."""
    service = get_gov_integrations_service(db)
    return service.get_digilocker_auth_url(user.id)


@router.post("/aadhaar/verify-last-four", response_model=AadhaarVerifyResponse)
def verify_aadhaar(
    payload: AadhaarVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aadhaar: Format Validation + Masking with privacy-preserving last 4 digits under DPDP Act 2023."""
    service = get_gov_integrations_service(db)
    return service.verify_aadhaar_last_four(user, payload)


@router.post("/pan/verify", response_model=PANVerifyResponse)
def verify_pan(
    payload: PANVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """PAN: Format Validation (entity category code and structural syntax)."""
    service = get_gov_integrations_service(db)
    return service.verify_pan(user, payload)


@router.post("/udyam/verify", response_model=UdyamVerifyResponse)
def verify_udyam(
    payload: UdyamVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UDYAM: Format/Structure Validation against Ministry of MSME standard nomenclature."""
    service = get_gov_integrations_service(db)
    return service.verify_udyam(user, payload)


@router.post("/schemes/sync", response_model=GovSchemeSyncResponse)
def sync_government_schemes(
    user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Synchronize schemes with official Gazette & ministry guidelines (Admin only)."""
    service = get_gov_integrations_service(db)
    return service.sync_government_schemes()


@router.get("/applications/{app_id}/sync", response_model=ApplicationStatusSyncResponse)
def sync_application_status(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Synchronize application tracking state with designated channel partner / nodal server."""
    service = get_gov_integrations_service(db)
    try:
        return service.sync_application_status(app_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== CBS & BANKING ADAPTER ENDPOINTS ====================

@router.get("/banking/partner/{partner_id}/metrics", response_model=CBSPartnerMetricsResponse)
async def get_cbs_partner_metrics(
    partner_id: UUID,
    branch_code: Optional[str] = Query(None, description="Specific CBS branch IFSC or identifier"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Query Core Banking System (CBS) live telemetry, health, and SLA metrics for a partner."""
    inst = db.query(Institution).filter(Institution.id == partner_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Partner institution not found in directory.")

    banking_svc = get_banking_data_service()
    return await banking_svc.fetch_cbs_partner_metrics(
        partner_id=inst.id,
        partner_code=inst.code,
        partner_name=inst.name,
        institution_type=inst.institution_type or "PSB",
        branch_code=branch_code
    )


@router.get("/banking/partner/{partner_id}/npa-utilization", response_model=NPAFundUtilizationResponse)
async def get_npa_fund_utilization(
    partner_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Query NPA risk indicators and fund utilization metrics for a lending partner."""
    inst = db.query(Institution).filter(Institution.id == partner_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Partner institution not found in directory.")

    banking_svc = get_banking_data_service()
    return await banking_svc.fetch_npa_fund_utilization(
        partner_id=inst.id,
        partner_code=inst.code,
        partner_name=inst.name
    )


@router.get("/banking/partner/{partner_id}/lending-capacity", response_model=PartnerLendingCapacityResponse)
async def get_partner_lending_capacity(
    partner_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Query authorized lending capacity quotas and tier for an accredited partner."""
    inst = db.query(Institution).filter(Institution.id == partner_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Partner institution not found in directory.")

    banking_svc = get_banking_data_service()
    return await banking_svc.fetch_partner_lending_capacity(
        partner_id=inst.id,
        partner_code=inst.code,
        partner_name=inst.name
    )


# ==================== PFMS / DBT DISBURSEMENT ENDPOINTS ====================

@router.post("/pfms/dbt-status", response_model=PFMSDisbursementStatusResponse)
async def query_pfms_dbt_status(
    payload: PFMSDisbursementQueryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query real-time Public Financial Management System (PFMS) Aadhaar bridge disbursement status."""
    # Authorization check: If application_id is provided, verify citizen ownership or admin/officer
    if payload.application_id:
        app = db.query(Application).filter(Application.id == payload.application_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found.")
        if app.user_id != user.id and user.role not in ("admin", "partner_officer"):
            raise HTTPException(status_code=403, detail="Unauthorized to query disbursement for this application.")
        if not payload.partner_reference_code:
            payload.partner_reference_code = (app.form_data or {}).get("partner_reference_code")

    pfms_svc = get_pfms_data_service()
    return await pfms_svc.query_disbursement_status(
        application_id=payload.application_id,
        partner_reference_code=payload.partner_reference_code,
        sanction_reference_number=payload.sanction_reference_number,
        beneficiary_account_last_four=payload.beneficiary_account_last_four
    )


# ==================== SECURE AUTHENTICATED WEBHOOKS ====================

@router.post("/webhooks/banking", response_model=BankingWebhookResponse, dependencies=[Depends(webhook_limiter)])
async def handle_banking_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp")
):
    """Inbound authenticated webhook for Core Banking System (CBS) partner telemetry updates."""
    raw_body = await request.body()
    sig = x_signature or x_hub_signature_256

    try:
        payload = InboundWebhookPayload.model_validate_json(raw_body)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid webhook JSON schema: {err}")

    processor = get_banking_webhook_processor(db)
    return processor.process_webhook(
        raw_body=raw_body,
        signature_header=sig,
        payload=payload,
        webhook_type="banking",
        timestamp_header=x_timestamp
    )


@router.post("/webhooks/pfms", response_model=BankingWebhookResponse, dependencies=[Depends(webhook_limiter)])
async def handle_pfms_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp")
):
    """Inbound authenticated webhook for PFMS / DBT Aadhaar Payment Bridge settlement updates."""
    raw_body = await request.body()
    sig = x_signature or x_hub_signature_256

    try:
        payload = InboundWebhookPayload.model_validate_json(raw_body)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid webhook JSON schema: {err}")

    processor = get_banking_webhook_processor(db)
    return processor.process_webhook(
        raw_body=raw_body,
        signature_header=sig,
        payload=payload,
        webhook_type="pfms",
        timestamp_header=x_timestamp
    )
