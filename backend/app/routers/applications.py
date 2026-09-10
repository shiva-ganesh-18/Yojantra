"""Application management, validation, checklists, and tracking router."""
from datetime import datetime, timezone
import re
import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, check_resource_ownership
from app.models import User, Application, Scheme, Document, Business
from app.schemas import (
    ApplicationCreate, 
    ApplicationUpdate, 
    ApplicationResponse,
    PreSubmissionValidationResponse,
    PreSubmissionCheckItem,
    ApplicationChecklistResponse,
    ApplicationChecklistItem,
    ApplicationTimelineEvent,
    ApplicationPartnerRoutingResponse,
    ApplicationPartnerRoutingItem,
    RoutingStatusUpdateRequest,
    PartnerResponseActionRequest,
    ApplicationRoutingStatusResponse,
    RoutingHistoryEntry,
    DocumentsRequiredAlert,
    ApprovalDetails,
    RejectionDetails,
    DisbursementProgress,
    ClearNextAction,
    ApplicationTrackingResponse,
    ResolveDocumentRequest,
)
from app.services.notification_service import NotificationService
from app.services.document_service import normalize_document_type
from app.services.partner_routing_service import PartnerRoutingService
from app.services.partner_routing_status_service import (
    PartnerRoutingStatusService,
    PartnerRoutingStatus,
    PartnerAcknowledgementStatus,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


def _generate_partner_reference(scheme_name: str, app_id: UUID) -> str:
    """Generate a clean standardized reference code for channel partners / nodal tracking."""
    # Create an acronym from scheme name (e.g., PMEGP, PM-MUDRA, STANDUP)
    words = re.findall(r"[A-Za-z0-9]+", scheme_name.upper())
    scheme_code = "".join(w[:2] for w in words[:3]) if words else "SCHEME"
    short_uuid = str(app_id).replace("-", "")[:6].upper()
    current_year = datetime.now().year
    return f"YOJ-{current_year}-{scheme_code}-{short_uuid}"


def _format_document_display_name(doc_str: str) -> str:
    """Format document name while preserving government acronyms and clean labels."""
    if not doc_str:
        return "Required Document"

    mapping = {
        "aadhaar": "Aadhaar Card",
        "pan": "PAN Card",
        "bank_passbook": "Bank Passbook / Statement",
        "udyam": "UDYAM Registration Certificate",
        "income_certificate": "Income Certificate",
        "caste_certificate": "Caste / Category Certificate",
        "project_report": "Detailed Project Report (DPR)",
        "gst": "GST Registration Certificate",
    }
    if doc_str.lower() in mapping:
        return mapping[doc_str.lower()]

    acronyms = {
        "(TA)", "(IA)", "(DSR)", "(DPR)", "(DIC)", "(MSME)", "(GST)", "(ITR)", "(KYC)",
        "TA", "IA", "DSR", "DPR", "DIC", "PAN", "MSME", "GST", "GSTIN", "KYC", "ITR",
        "UIDAI", "DBT", "PFMS", "SC", "ST", "OBC", "EWS"
    }
    tokens = doc_str.replace("_", " ").split()
    formatted = []
    for tok in tokens:
        upper_tok = tok.upper()
        if upper_tok in acronyms or tok in acronyms:
            formatted.append(upper_tok)
        elif tok.startswith("(") and tok.endswith(")"):
            inner = tok[1:-1].upper()
            if inner in acronyms or len(inner) <= 4:
                formatted.append(f"({inner})")
            else:
                formatted.append(tok.title())
        elif upper_tok in ("CARD", "PROOF", "REPORT", "CONSENT", "DETAILS", "CERTIFICATE", "COPY"):
            formatted.append(tok.capitalize())
        else:
            formatted.append(tok.capitalize())
    return " ".join(formatted)


def _format_checklist_item_title(clean_name: str) -> str:
    """Ensure clean title without awkward redundant Copy suffixes."""
    suffixes = (
        "copy", "certificate", "report", "consent", "details", 
        "statement", "card", "proof", "record", "plan", "format"
    )
    if any(clean_name.lower().endswith(s) for s in suffixes):
        return clean_name
    return f"{clean_name} Copy"


def _build_application_timeline(app: Application, scheme: Optional[Scheme]) -> List[ApplicationTimelineEvent]:
    """Build milestone timeline with status, audit timestamps, and notes reflecting live partner routing states."""
    form_data = app.form_data or {}
    timeline_meta = form_data.get("timeline_events", {})
    partner_routing = form_data.get("partner_routing", {})
    routing_status = partner_routing.get("routing_status") or (
        "NOT_ROUTED" if app.status == "draft" else (
            "ROUTED_TO_PARTNER" if app.status == "submitted" else (
                "UNDER_REVIEW" if app.status == "under_review" else (
                    "APPROVED" if app.status == "approved" else (
                        "DISBURSED" if app.status == "disbursed" else (
                            "REJECTED" if app.status == "rejected" else "NOT_ROUTED"
                        )
                    )
                )
            )
        )
    )
    assigned_name = partner_routing.get("assigned_partner_name") or "Channel Partner"

    steps_def = [
        {
            "step": 1,
            "title": "Application Drafted & Profile Compiled",
            "channel": "Yojantra Platform",
            "default_note": "Application initialized with entrepreneur profile and required scheme criteria."
        },
        {
            "step": 2,
            "title": "Dossier Submitted & Routed to Channel Partner",
            "channel": f"{app.channel.upper()} / Partner Gateway",
            "default_note": f"Application packet transmitted for departmental verification via {assigned_name}."
        },
        {
            "step": 3,
            "title": "Nodal Officer / Bank Verification",
            "channel": "District Industries Centre / Lead Bank",
            "default_note": "Scrutiny of financial viability, caste/MSME credentials, and project report."
        },
        {
            "step": 4,
            "title": "Subsidy Sanction & Direct Benefit Transfer",
            "channel": "PFMS / DBT Aadhaar Gateway",
            "default_note": "Final sanction letter issued and capital subsidy / credit guarantee disbursed."
        }
    ]

    events = []
    for s in steps_def:
        step_num = s["step"]
        meta = timeline_meta.get(str(step_num), {})

        # Compute status for this step
        if step_num == 1:
            st = "completed" if app.status != "draft" else "current"
        elif step_num == 2:
            if routing_status in ["NOT_ROUTED", "PARTNER_ASSIGNED"]:
                st = "pending"
            elif routing_status == "ROUTED_TO_PARTNER":
                st = "current"
            elif app.status == "rejected" and routing_status == "REJECTED" and len(form_data.get("routing_history", [])) <= 2:
                st = "failed"
            else:
                st = "completed"
        elif step_num == 3:
            if routing_status in ["NOT_ROUTED", "PARTNER_ASSIGNED", "ROUTED_TO_PARTNER"]:
                st = "pending"
            elif routing_status == "DOCUMENTS_REQUIRED":
                st = "failed"
            elif routing_status in ["PARTNER_RECEIVED", "UNDER_REVIEW"]:
                st = "current"
            elif routing_status in ["APPROVED", "DISBURSEMENT_PROCESSING", "DISBURSED"]:
                st = "completed"
            elif routing_status == "REJECTED":
                st = "failed"
            else:
                st = "pending"
        elif step_num == 4:
            if routing_status in ["APPROVED", "DISBURSEMENT_PROCESSING"]:
                st = "current"
            elif routing_status == "DISBURSED":
                st = "completed"
            elif routing_status == "REJECTED":
                st = "failed" if app.status == "rejected" and form_data.get("routing_history", []) and any(h.get("to_status") == "APPROVED" for h in form_data.get("routing_history", [])) else "pending"
            else:
                st = "pending"

        ts = meta.get("timestamp")
        if not ts and (st in ["completed", "current"] and step_num == 1):
            ts = app.created_at
        elif not ts and (st in ["completed", "current"] and step_num == 2 and app.status != "draft"):
            ts = app.updated_at or app.created_at

        # Note resolution
        step_note = meta.get("note") or s["default_note"]
        if step_num == 3 and routing_status == "DOCUMENTS_REQUIRED":
            last_reason = partner_routing.get("last_routing_reason")
            if last_reason:
                step_note = f"Action Required: Compliance query raised: {last_reason}"
        elif step_num == 3 and routing_status == "PARTNER_RECEIVED":
            step_note = f"Dossier received and acknowledged by {assigned_name}. Scrutiny scheduled."
        elif step_num == 4 and routing_status == "APPROVED":
            last_reason = partner_routing.get("last_routing_reason")
            step_note = f"Sanction letter issued by {assigned_name}. {last_reason or ''}".strip()
        elif step_num == 4 and routing_status == "DISBURSEMENT_PROCESSING":
            step_note = "PFMS payment batch processing. Aadhaar bridge verification underway."
        elif step_num == 4 and routing_status == "DISBURSED":
            step_note = "Funds credited to Aadhaar-linked bank account. Disbursement completed."

        events.append(ApplicationTimelineEvent(
            step=step_num,
            title=s["title"],
            status=st,
            timestamp=ts if isinstance(ts, datetime) else (datetime.fromisoformat(ts) if isinstance(ts, str) else None),
            note=step_note,
            channel_or_portal=s["channel"]
        ))

    return events


def _compute_application_validation(
    app: Application, 
    user: User, 
    scheme: Scheme, 
    user_docs: List[Document]
) -> PreSubmissionValidationResponse:
    """Run comprehensive pre-submission checks against profile, business data, and required documents."""
    checks: List[PreSubmissionCheckItem] = []
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Profile Verification
    has_name = bool(user.full_name and len(user.full_name.strip()) > 1)
    checks.append(PreSubmissionCheckItem(
        category="profile",
        field_or_doc="full_name",
        label="Applicant Full Name",
        is_valid=has_name,
        message="Full name verified from identity profile" if has_name else "Applicant full name is missing in profile",
        severity="error" if not has_name else "info"
    ))
    if not has_name:
        errors.append("Profile missing full legal name.")

    has_state = bool(user.state)
    checks.append(PreSubmissionCheckItem(
        category="profile",
        field_or_doc="state",
        label="State / Domicile Location",
        is_valid=has_state,
        message=f"Domicile state identified as {user.state}" if has_state else "Applicant state/district not set in profile (recommended for state quota routing)",
        severity="warning" if not has_state else "info"
    ))
    if not has_state:
        warnings.append("State domicile not set; default national quota routing will apply.")

    # 2. Business Entity / Enterprise Checks
    biz: Optional[Business] = user.business
    has_business = biz is not None
    checks.append(PreSubmissionCheckItem(
        category="business",
        field_or_doc="enterprise_profile",
        label="Enterprise Profile Registration",
        is_valid=has_business,
        message="Enterprise details linked" if has_business else "Business profile not linked; individual category applied",
        severity="warning" if not has_business else "info"
    ))
    if not has_business:
        warnings.append("Business profile is empty. You may update unit turnover & asset valuation later.")

    if biz:
        if scheme.requires_udyam and not biz.registration_type:
            checks.append(PreSubmissionCheckItem(
                category="business",
                field_or_doc="udyam_registration",
                label="UDYAM MSME Registration",
                is_valid=False,
                message="Scheme strictly requires an active UDYAM Registration Number",
                severity="error"
            ))
            errors.append("UDYAM registration required for this specific MSME scheme.")
        else:
            checks.append(PreSubmissionCheckItem(
                category="business",
                field_or_doc="udyam_registration",
                label="UDYAM MSME Registration",
                is_valid=True,
                message="Enterprise registration compliance satisfied",
                severity="info"
            ))

        if biz.funding_needed_inr and scheme.max_benefit_inr:
            if biz.funding_needed_inr > (scheme.max_benefit_inr * 2):
                checks.append(PreSubmissionCheckItem(
                    category="business",
                    field_or_doc="funding_amount",
                    label="Requested Funding Feasibility",
                    is_valid=True,
                    message=f"Requested amount ₹{biz.funding_needed_inr:,.0f} exceeds max scheme ceiling of ₹{scheme.max_benefit_inr:,.0f}. Cap will apply.",
                    severity="warning"
                ))
                warnings.append("Requested loan/subsidy exceeds standard scheme ceiling; bank appraisal may scale down.")

    # 3. Document Completeness Checks
    uploaded_doc_types = {d.doc_type: d for d in user_docs if d.verification_status != "rejected"}
    
    # Check scheme documents required (or standard primary docs)
    required_docs = scheme.documents_required if scheme.documents_required else [
        {"name": "Aadhaar Card", "mandatory": True},
        {"name": "PAN Card", "mandatory": True},
        {"name": "Bank Passbook / Statement", "mandatory": True}
    ]
    if isinstance(required_docs, list) and len(required_docs) > 0:
        seen_canonical = set()
        for req_doc in required_docs:
            if isinstance(req_doc, dict):
                raw_name = req_doc.get("name", "")
                is_mand = req_doc.get("mandatory", req_doc.get("is_mandatory", True))
            else:
                raw_name = str(req_doc)
                is_mand = True

            canonical_type = normalize_document_type(raw_name)
            if canonical_type in seen_canonical:
                continue
            seen_canonical.add(canonical_type)

            doc_obj = uploaded_doc_types.get(canonical_type)
            is_present = doc_obj is not None
            is_verified = bool(doc_obj and doc_obj.verification_status == "verified")

            label_name = _format_document_display_name(raw_name) if raw_name else _format_document_display_name(canonical_type)
            checks.append(PreSubmissionCheckItem(
                category="documents",
                field_or_doc=canonical_type,
                label=f"{label_name} Document" if not label_name.lower().endswith("document") else label_name,
                is_valid=is_present,
                message="Document uploaded and verified via internal OCR" if is_verified else (
                    "Document uploaded (pending scrutiny)" if is_present else f"Mandatory document {label_name} is missing"
                ),
                severity="warning" if (not is_present or not is_verified) else "info"
            ))
            if not is_present and is_mand:
                warnings.append(f"Missing mandatory document: {label_name}. Accredited partner will request document upload before final sanction.")
    else:
        # Generic document check
        has_any_doc = len(user_docs) > 0
        checks.append(PreSubmissionCheckItem(
            category="documents",
            field_or_doc="general_docs",
            label="Digital Document Proofs",
            is_valid=has_any_doc,
            message=f"{len(user_docs)} digital documents attached" if has_any_doc else "No identity/business documents uploaded yet (recommended before final bank appraisal)",
            severity="warning" if not has_any_doc else "info"
        ))
        if not has_any_doc:
            warnings.append("No KYC documents attached. Channel partner may request physical copies.")

    # Calculate overall readiness score (0 - 100)
    total_checks = len(checks)
    valid_checks = sum(1 for c in checks if c.is_valid)
    raw_readiness = int((valid_checks / total_checks) * 100) if total_checks > 0 else 100

    # If mandatory documents are missing or other errors exist, cap readiness score at 65%
    has_missing_docs = any(not c.is_valid and c.category == "documents" for c in checks)
    if errors or has_missing_docs:
        readiness_score = min(raw_readiness, 65)
    else:
        readiness_score = min(100, max(0, raw_readiness))

    is_ready = len(errors) == 0

    ref_code = (app.form_data or {}).get("partner_reference_code") or _generate_partner_reference(scheme.name, app.id)

    return PreSubmissionValidationResponse(
        application_id=app.id,
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        is_ready_to_submit=is_ready,
        readiness_score=readiness_score,
        errors=errors,
        warnings=warnings,
        checks=checks,
        official_portal_url=scheme.official_url,
        partner_reference_code=ref_code
    )


def _compute_application_tracking_details(
    app: Application,
    scheme: Optional[Scheme],
    routing_status: str,
    ack_status: str,
    routing_history: List[Dict[str, Any]],
    assigned_partner_name: Optional[str],
    assigned_partner_type: Optional[str]
) -> Dict[str, Any]:
    """Compute rich tracking details: alerts, approval/rejection reasons, disbursement progress, and next actions."""
    form_data = app.form_data or {}
    partner_routing = form_data.get("partner_routing", {})
    ref_code = form_data.get("partner_reference_code") or (scheme and _generate_partner_reference(scheme.name, app.id))

    # 1. Documents Required Alert
    doc_alert = None
    if routing_status == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
        latest_req = next((h for h in reversed(routing_history) if h.get("to_status") == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value), None)
        reason_text = (
            latest_req.get("reason")
            if latest_req and latest_req.get("reason")
            else partner_routing.get("last_routing_reason", "Additional compliance documentation requested by nodal partner.")
        )
        req_by = (
            (latest_req.get("partner_name") if latest_req else None)
            or assigned_partner_name
            or (latest_req.get("actor") if latest_req else None)
            or "Nodal Desk Officer"
        )
        req_ts = None
        if latest_req and latest_req.get("timestamp"):
            ts_val = latest_req.get("timestamp")
            req_ts = datetime.fromisoformat(ts_val) if isinstance(ts_val, str) else ts_val
        if not req_ts:
            req_ts = app.updated_at or app.created_at

        doc_alert = DocumentsRequiredAlert(
            is_active=True,
            reason=reason_text,
            requested_at=req_ts,
            requested_by=req_by,
            action_required="Upload and attach the requested compliance documents to resume nodal scrutiny.",
            can_resolve=True
        )

    # 2. Approval Details
    approval_info = None
    if routing_status in [
        PartnerRoutingStatus.APPROVED.value,
        PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value,
        PartnerRoutingStatus.DISBURSED.value,
    ]:
        latest_appr = next((h for h in reversed(routing_history) if h.get("to_status") == PartnerRoutingStatus.APPROVED.value), None)
        appr_reason = (
            latest_appr.get("reason")
            if latest_appr and latest_appr.get("reason")
            else "Application and credit facility sanctioned by nodal committee."
        )
        appr_by = (
            (latest_appr.get("partner_name") if latest_appr else None)
            or assigned_partner_name
            or (latest_appr.get("actor") if latest_appr else None)
            or "Nodal Approval Committee"
        )
        appr_ts = None
        if latest_appr and latest_appr.get("timestamp"):
            ts_val = latest_appr.get("timestamp")
            appr_ts = datetime.fromisoformat(ts_val) if isinstance(ts_val, str) else ts_val
        if not appr_ts:
            appr_ts = app.updated_at or app.created_at

        requested_amt = form_data.get("requested_amount_inr")
        subsidy_amt = Decimal(str(requested_amt)) if requested_amt else None

        approval_info = ApprovalDetails(
            is_approved=True,
            approved_at=appr_ts,
            sanction_reference=f"SANC-{ref_code}" if ref_code else f"SANC-{str(app.id)[:8].upper()}",
            approved_by=appr_by,
            reason_or_remarks=appr_reason,
            subsidy_amount_inr=subsidy_amt
        )

    # 3. Rejection Details
    rejection_info = None
    if routing_status == PartnerRoutingStatus.REJECTED.value:
        latest_rej = next((h for h in reversed(routing_history) if h.get("to_status") == PartnerRoutingStatus.REJECTED.value), None)
        rej_reason = (
            latest_rej.get("reason")
            if latest_rej and latest_rej.get("reason")
            else partner_routing.get("last_routing_reason", "Application declined during nodal review.")
        )
        rej_by = (
            (latest_rej.get("partner_name") if latest_rej else None)
            or assigned_partner_name
            or (latest_rej.get("actor") if latest_rej else None)
            or "Reviewing Officer"
        )
        rej_ts = None
        if latest_rej and latest_rej.get("timestamp"):
            ts_val = latest_rej.get("timestamp")
            rej_ts = datetime.fromisoformat(ts_val) if isinstance(ts_val, str) else ts_val
        if not rej_ts:
            rej_ts = app.updated_at or app.created_at

        rejection_info = RejectionDetails(
            is_rejected=True,
            rejected_at=rej_ts,
            rejected_by=rej_by,
            reason=rej_reason,
            can_reapply=True
        )

    # 4. Disbursement Progress
    if routing_status == PartnerRoutingStatus.DISBURSED.value:
        latest_disb = next((h for h in reversed(routing_history) if h.get("to_status") == PartnerRoutingStatus.DISBURSED.value), None)
        disb_ts = None
        if latest_disb and latest_disb.get("timestamp"):
            ts_val = latest_disb.get("timestamp")
            disb_ts = datetime.fromisoformat(ts_val) if isinstance(ts_val, str) else ts_val
        if not disb_ts:
            disb_ts = app.updated_at or app.created_at

        disb_reason = (
            latest_disb.get("reason")
            if latest_disb and latest_disb.get("reason")
            else "Direct Benefit Transfer credited to beneficiary Aadhaar-linked account."
        )
        disbursement_info = DisbursementProgress(
            status="DISBURSED",
            channel="Direct Benefit Transfer (PFMS Aadhaar Bridge)",
            disbursed_at=disb_ts,
            reference_number=f"PFMS-DBT-{ref_code}" if ref_code else "PFMS-TXN-SUCCESS",
            remarks=disb_reason
        )
    elif routing_status == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value:
        latest_proc = next((h for h in reversed(routing_history) if h.get("to_status") == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value), None)
        proc_reason = (
            latest_proc.get("reason")
            if latest_proc and latest_proc.get("reason")
            else "Credit batch dispatched; PFMS Aadhaar bridge processing payment."
        )
        disbursement_info = DisbursementProgress(
            status="PROCESSING",
            channel="Direct Benefit Transfer (PFMS Aadhaar Bridge)",
            disbursed_at=None,
            reference_number=None,
            remarks=proc_reason
        )
    else:
        disbursement_info = DisbursementProgress(
            status="NOT_STARTED",
            channel="Direct Benefit Transfer (PFMS Aadhaar Bridge)",
            disbursed_at=None,
            reference_number=None,
            remarks="Disbursement initiated automatically after sanction approval."
        )

    # 5. Clear Next Action
    if routing_status == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
        clear_action = ClearNextAction(
            action_title="Action Required: Upload Compliance Documents",
            action_description=f"Partner requested: {doc_alert.reason if doc_alert else 'Additional compliance documents'}. Upload documents and submit compliance response.",
            action_type="UPLOAD_DOCS",
            action_url="/documents",
            deadline=app.next_action_deadline,
            is_applicant_action_required=True
        )
    elif routing_status in [PartnerRoutingStatus.NOT_ROUTED.value, PartnerRoutingStatus.PARTNER_ASSIGNED.value] or app.status == "draft":
        clear_action = ClearNextAction(
            action_title="Complete Pre-Submission & Submit Dossier",
            action_description="Verify uploaded documents, check readiness score, and route your completed application dossier to your assigned channel partner.",
            action_type="SUBMIT_APPLICATION",
            action_url="/applications",
            deadline=app.next_action_deadline,
            is_applicant_action_required=True
        )
    elif routing_status == PartnerRoutingStatus.ROUTED_TO_PARTNER.value:
        clear_action = ClearNextAction(
            action_title="Awaiting Partner Receipt Acknowledgement",
            action_description=f"Dossier transmitted to {assigned_partner_name or 'channel partner'}. Official receipt acknowledgement is pending.",
            action_type="AWAIT_REVIEW",
            action_url=None,
            is_applicant_action_required=False
        )
    elif routing_status == PartnerRoutingStatus.PARTNER_RECEIVED.value:
        clear_action = ClearNextAction(
            action_title="Dossier Acknowledged; Scrutiny Starting",
            action_description=f"{assigned_partner_name or 'Channel partner'} confirmed docket receipt. Nodal appraisal is queued to commence.",
            action_type="AWAIT_REVIEW",
            action_url=None,
            is_applicant_action_required=False
        )
    elif routing_status == PartnerRoutingStatus.UNDER_REVIEW.value:
        clear_action = ClearNextAction(
            action_title="Technical & Financial Appraisal in Progress",
            action_description=f"Your application is undergoing detailed verification by {assigned_partner_name or 'nodal review desk'}. No action required.",
            action_type="AWAIT_REVIEW",
            action_url=None,
            is_applicant_action_required=False
        )
    elif routing_status == PartnerRoutingStatus.APPROVED.value:
        clear_action = ClearNextAction(
            action_title="Sanction Approved; Queued for DBT",
            action_description="Sanction letter issued. Direct Benefit Transfer disbursement batch is being prepared via PFMS.",
            action_type="AWAIT_DISBURSEMENT",
            action_url=None,
            is_applicant_action_required=False
        )
    elif routing_status == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value:
        clear_action = ClearNextAction(
            action_title="Disbursement Processing in Progress",
            action_description="Payment batch transmitted to the RBI / PFMS Aadhaar payment gateway. Bank credit is imminent.",
            action_type="AWAIT_DISBURSEMENT",
            action_url=None,
            is_applicant_action_required=False
        )
    elif routing_status == PartnerRoutingStatus.DISBURSED.value:
        clear_action = ClearNextAction(
            action_title="Benefit Disbursed Successfully",
            action_description="Direct Benefit Transfer completed. Reference recorded in audit log. Keep records safe.",
            action_type="COMPLETED",
            action_url=None,
            is_applicant_action_required=False
        )
    elif routing_status == PartnerRoutingStatus.REJECTED.value:
        clear_action = ClearNextAction(
            action_title="Application Declined",
            action_description=f"Declined: {rejection_info.reason if rejection_info else 'Review notes'}. You can explore other eligible schemes.",
            action_type="REVIEW_REJECTION",
            action_url="/matches",
            is_applicant_action_required=False
        )
    else:
        clear_action = ClearNextAction(
            action_title="Track Application Status",
            action_description=app.next_action or "Application processing in progress.",
            action_type="AWAIT_REVIEW",
            action_url=None,
            is_applicant_action_required=False
        )

    # 6. Assigned Partner Details
    assigned_partner_details = None
    if partner_routing.get("assigned_partner_id") or assigned_partner_name:
        assigned_partner_details = {
            "partner_id": partner_routing.get("assigned_partner_id"),
            "partner_name": assigned_partner_name or partner_routing.get("assigned_partner_name"),
            "partner_type": assigned_partner_type or partner_routing.get("assigned_partner_type"),
            "location": partner_routing.get("assigned_partner_location"),
            "distance_km": partner_routing.get("distance_km"),
            "geographic_tier": partner_routing.get("geographic_tier"),
            "acknowledgement_status": ack_status,
            "updated_at": partner_routing.get("routing_status_updated_at")
        }

    return {
        "documents_required_alert": doc_alert,
        "approval_details": approval_info,
        "rejection_details": rejection_info,
        "disbursement_progress": disbursement_info,
        "clear_next_action": clear_action,
        "assigned_partner_details": assigned_partner_details
    }


def _enrich_application_response(app: Application, db: Session) -> ApplicationResponse:
    """Helper to convert Application ORM object to enriched ApplicationResponse."""
    scheme = app.scheme
    user = app.user
    
    form_data = app.form_data or {}
    ref_code = form_data.get("partner_reference_code")
    if not ref_code and scheme:
        ref_code = _generate_partner_reference(scheme.name, app.id)

    # Compute validation & timeline
    timeline = _build_application_timeline(app, scheme)
    
    user_docs = db.query(Document).filter(Document.user_id == app.user_id).all() if user else []
    validation = _compute_application_validation(app, user, scheme, user_docs) if (scheme and user) else None

    # Compute partner routing info
    routing_service = PartnerRoutingService(db)
    partner_routing = form_data.get("partner_routing", {})
    scheme_category = partner_routing.get("scheme_category")
    assigned_partner_name = partner_routing.get("assigned_partner_name")
    assigned_partner_type = partner_routing.get("assigned_partner_type")

    if not scheme_category and scheme:
        cat_info = routing_service.determine_scheme_category(scheme)
        scheme_category = cat_info["category_label"]
    if not assigned_partner_name and scheme:
        _, _, assigned = routing_service.find_eligible_partners_for_application(app)
        if assigned:
            assigned_partner_name = assigned.partner_name
            assigned_partner_type = assigned.partner_type

    # Routing status and audit history
    status_service = PartnerRoutingStatusService(db)
    current_routing_status = status_service.get_current_routing_status(app)
    ack_status = status_service.get_partner_acknowledgement_status(app)
    routing_history = status_service.get_routing_history(app)

    # Compute rich tracking details
    tracking = _compute_application_tracking_details(
        app=app,
        scheme=scheme,
        routing_status=current_routing_status,
        ack_status=ack_status,
        routing_history=routing_history,
        assigned_partner_name=assigned_partner_name,
        assigned_partner_type=assigned_partner_type
    )

    return ApplicationResponse(
        id=app.id,
        scheme_id=app.scheme_id,
        scheme_name=scheme.name if scheme else None,
        ministry=scheme.ministry if scheme else None,
        channel=app.channel or "online",
        status=app.status,
        partner_reference_code=ref_code,
        current_step=app.current_step,
        total_steps=app.total_steps,
        next_action=app.next_action,
        next_action_deadline=app.next_action_deadline,
        official_portal_url=scheme.official_url if scheme else None,
        helpline_number=scheme.helpline_number if scheme else None,
        readiness_score=validation.readiness_score if validation else 100,
        is_ready_to_submit=validation.is_ready_to_submit if validation else True,
        submission_disclaimer=(
            "Yojantra prepares and validates your application dossier. "
            "Final processing is conducted by accredited channel partners and official nodal departments."
        ),
        timeline=timeline,
        form_data=app.form_data,
        documents_uploaded=app.documents_uploaded,
        assigned_partner_name=assigned_partner_name,
        assigned_partner_type=assigned_partner_type,
        scheme_category=scheme_category,
        routing_status=current_routing_status,
        partner_acknowledgement_status=ack_status,
        routing_history=routing_history,
        documents_required_alert=tracking["documents_required_alert"],
        approval_details=tracking["approval_details"],
        rejection_details=tracking["rejection_details"],
        disbursement_progress=tracking["disbursement_progress"],
        clear_next_action=tracking["clear_next_action"],
        assigned_partner_details=tracking["assigned_partner_details"],
        created_at=app.created_at,
        updated_at=app.updated_at
    )


@router.post("", response_model=ApplicationResponse)
def create_application(
    app_data: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new application with readiness check, reference code, and initial timeline."""
    scheme = db.query(Scheme).filter(Scheme.id == app_data.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Check for existing active application for this scheme to prevent duplicate applications on retry
    existing_app = (
        db.query(Application)
        .filter(
            Application.user_id == user.id,
            Application.scheme_id == app_data.scheme_id,
            Application.status.in_(["draft", "submitted", "under_review", "approved", "disbursed"])
        )
        .order_by(Application.created_at.desc())
        .first()
    )
    if existing_app:
        return _enrich_application_response(existing_app, db)

    total_steps = len(scheme.application_steps) if scheme.application_steps else 4
    app_uuid = uuid.uuid4()
    ref_code = _generate_partner_reference(scheme.name, app_uuid)

    initial_form_data = {
        "partner_reference_code": ref_code,
        "requested_amount_inr": float(app_data.requested_amount_inr) if app_data.requested_amount_inr else None,
        "user_submitted_data": app_data.application_data or {},
        "timeline_events": {
            "1": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": f"Draft initiated on Yojantra platform for {scheme.name}."
            }
        }
    }

    application = Application(
        id=app_uuid,
        user_id=user.id,
        scheme_id=app_data.scheme_id,
        channel=app_data.channel,
        total_steps=total_steps,
        current_step=1,
        status="draft",
        next_action=f"Verify document readiness and submit application dossier for {scheme.name}",
        form_data=initial_form_data
    )
    application.scheme = scheme
    application.user = user

    # Initialize channel partner routing metadata for this application
    try:
        routing_service = PartnerRoutingService(db)
        cat_info, eligible_partners, assigned = routing_service.find_eligible_partners_for_application(application)
        initial_routing_status = (
            PartnerRoutingStatus.PARTNER_ASSIGNED.value
            if assigned
            else PartnerRoutingStatus.NOT_ROUTED.value
        )
        initial_form_data["partner_routing"] = {
            "scheme_category": cat_info.get("category_label", "General Scheme"),
            "category_code": cat_info.get("category_code", "GEN"),
            "preferred_partner_type": cat_info.get("preferred_type"),
            "total_eligible_partners": len(eligible_partners),
            "assigned_partner_id": str(assigned.partner_id) if assigned else None,
            "assigned_partner_name": assigned.partner_name if assigned else None,
            "assigned_partner_type": assigned.partner_type if assigned else None,
            "assigned_partner_location": assigned.location if assigned else None,
            "routing_status": initial_routing_status,
            "partner_acknowledgement_status": PartnerAcknowledgementStatus.NOT_ROUTED.value,
            "routing_status_updated_at": datetime.now(timezone.utc).isoformat(),
            "last_routing_reason": "Application draft created."
        }
        initial_form_data["routing_history"] = [
            {
                "from_status": None,
                "to_status": initial_routing_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "partner_id": str(assigned.partner_id) if assigned else None,
                "partner_name": assigned.partner_name if assigned else None,
                "reason": (
                    f"Application draft created and initial channel partner {assigned.partner_name} assigned."
                    if assigned
                    else "Application draft created. Awaiting channel partner assignment."
                ),
                "actor": user.email or user.phone or str(user.id),
                "actor_role": user.role,
                "source": "citizen_portal"
            }
        ]
    except Exception as routing_err:
        initial_form_data["partner_routing"] = {
            "scheme_category": "National / State Scheme",
            "category_code": "GEN",
            "preferred_partner_type": "PSB",
            "total_eligible_partners": 0,
            "assigned_partner_id": None,
            "assigned_partner_name": None,
            "assigned_partner_type": None,
            "assigned_partner_location": None,
            "routing_status": PartnerRoutingStatus.NOT_ROUTED.value,
            "partner_acknowledgement_status": PartnerAcknowledgementStatus.NOT_ROUTED.value,
            "routing_status_updated_at": datetime.now(timezone.utc).isoformat(),
            "last_routing_reason": "Application draft created. Partner routing will initialize upon dossier submission."
        }
        initial_form_data["routing_history"] = [
            {
                "from_status": None,
                "to_status": PartnerRoutingStatus.NOT_ROUTED.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "partner_id": None,
                "partner_name": None,
                "reason": "Application draft created. Routing to channel partner queued.",
                "actor": user.email or user.phone or str(user.id),
                "actor_role": user.role,
                "source": "citizen_portal"
            }
        ]
    application.form_data = initial_form_data

    db.add(application)
    db.commit()
    db.refresh(application)

    # Trigger notification
    notif_service = NotificationService(db)
    notif_service.create_notification(
        user_id=user.id,
        notif_type="application_status",
        title=f"Application Started: {scheme.name}",
        body=f"Your draft application (Ref: {ref_code}) has been initialized. Review the required checklist to proceed.",
        action_url="/applications",
        metadata={"application_id": str(application.id), "scheme_id": str(scheme.id)}
    )

    return _enrich_application_response(application, db)


@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all user applications with enriched tracking data."""
    applications = db.query(Application).filter(Application.user_id == user.id).order_by(Application.created_at.desc()).all()
    return [_enrich_application_response(app, db) for app in applications]


@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application details with milestone timeline and verification logs."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    return _enrich_application_response(application, db)


@router.get("/{app_id}/validate", response_model=PreSubmissionValidationResponse)
def validate_application_readiness(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform pre-submission validation checking profile completeness, business compliance, and documents."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    scheme = application.scheme
    if not scheme:
        raise HTTPException(status_code=404, detail="Associated scheme not found")

    target_user = application.user if application.user else user
    user_docs = db.query(Document).filter(Document.user_id == target_user.id).all()
    return _compute_application_validation(application, target_user, scheme, user_docs)


@router.get("/{app_id}/checklist", response_model=ApplicationChecklistResponse)
def get_application_checklist(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return scheme-specific checklist combining required documents, profile status, and portal guidelines."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    scheme = application.scheme
    if not scheme:
        raise HTTPException(status_code=404, detail="Associated scheme not found")

    target_user = application.user if application.user else user
    user_docs = db.query(Document).filter(Document.user_id == target_user.id).all()
    # Map valid (non-rejected) documents by canonical doc_type
    doc_map = {d.doc_type: d for d in user_docs if d.verification_status != "rejected"}

    items: List[ApplicationChecklistItem] = []

    # 1. Profile KYC completeness
    missing_kyc = []
    if not user.full_name:
        missing_kyc.append("Full Name")
    if not user.phone:
        missing_kyc.append("Active Mobile Number")
    if not user.state:
        missing_kyc.append("State Domicile")
    if not user.district:
        missing_kyc.append("District")
    is_profile_done = len(missing_kyc) == 0
    kyc_desc = (
        "Full name, active mobile number, social category, and verified state/district domicile specified."
        if is_profile_done
        else f"Action required: {', '.join(missing_kyc)} missing in profile (required for nodal SMS & verification)."
    )
    items.append(ApplicationChecklistItem(
        id="check_profile",
        title="Beneficiary Profile & KYC",
        category="compliance",
        description=kyc_desc,
        is_completed=is_profile_done,
        is_mandatory=True,
        action_url="/profile"
    ))

    # 2. Enterprise details
    is_business_done = bool(user.business and user.business.business_name)
    items.append(ApplicationChecklistItem(
        id="check_business",
        title="Enterprise / Unit Profile",
        category="compliance",
        description="Business enterprise name, sector, stage, and turnover details registered." if is_business_done else "Action required: Complete business enterprise profile and funding requirement.",
        is_completed=is_business_done,
        is_mandatory=True,
        action_url="/profile"
    ))

    # 3. Scheme Required Documents
    req_docs = scheme.documents_required if scheme.documents_required else [
        {"name": "Aadhaar Card", "mandatory": True},
        {"name": "PAN Card", "mandatory": True},
        {"name": "Bank Passbook / Statement", "mandatory": True}
    ]
    seen_types = set()
    for doc in req_docs:
        if isinstance(doc, dict):
            raw_name = doc.get("name", "")
            is_mand = doc.get("mandatory", doc.get("is_mandatory", True))
        else:
            raw_name = str(doc)
            is_mand = True

        canonical_type = normalize_document_type(raw_name)
        if canonical_type in seen_types:
            continue
        seen_types.add(canonical_type)

        doc_name = _format_document_display_name(raw_name) if raw_name else _format_document_display_name(canonical_type)
        item_title = _format_checklist_item_title(doc_name)

        # STRICT CHECK: Only mark complete if this exact canonical document is uploaded and not rejected!
        doc_obj = doc_map.get(canonical_type)
        has_doc = (doc_obj is not None) and (doc_obj.verification_status != "rejected")
        is_verified = (doc_obj is not None) and (doc_obj.verification_status == "verified")

        if has_doc:
            desc = f"Verified: Digital copy of {doc_name} is uploaded and attached for scrutiny." if is_verified else f"Uploaded: Digital copy of {doc_name} uploaded, pending nodal verification."
        else:
            desc = f"Action required: Upload digital copy of {doc_name} to fulfill mandatory compliance." if is_mand else f"Optional: Digital copy of {doc_name} for additional subsidy appraisal."

        items.append(ApplicationChecklistItem(
            id=f"doc_{canonical_type}",
            title=item_title,
            category="document",
            description=desc,
            is_completed=has_doc,
            is_mandatory=bool(is_mand),
            action_url="/documents"
        ))

    # 4. Official portal guidance step
    # Guarantee that official portal link belongs directly to the selected scheme
    scheme_portal_url = scheme.official_url or "https://myscheme.gov.in"
    items.append(ApplicationChecklistItem(
        id="portal_registration",
        title=f"Official Portal Link ({scheme.ministry or scheme.name})",
        category="step",
        description=f"Direct official portal link for {scheme.name}: {scheme_portal_url}",
        is_completed=application.status != "draft",
        is_mandatory=False,
        action_url=scheme_portal_url
    ))

    total = len(items)
    completed = sum(1 for item in items if item.is_completed)
    pct = int(round((completed / total) * 100)) if total > 0 else 100

    return ApplicationChecklistResponse(
        application_id=application.id,
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        ministry=scheme.ministry,
        total_items=total,
        completed_items=completed,
        completion_percentage=pct,
        items=items,
        official_portal_url=scheme_portal_url,
        helpline_number=scheme.helpline_number
    )


@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: UUID,
    update: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application details or status."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return _enrich_application_response(application, db)


@router.post("/{app_id}/submit")
def submit_application(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate and submit application dossier to channel partners / nodal tracking with honest disclaimer."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    if application.status != "draft":
        raise HTTPException(status_code=400, detail="Application already submitted or in review")

    scheme = application.scheme
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    user_docs = db.query(Document).filter(Document.user_id == user.id).all()
    validation = _compute_application_validation(application, user, scheme, user_docs)

    if not validation.is_ready_to_submit:
        raise HTTPException(
            status_code=422, 
            detail={
                "message": "Pre-submission validation failed. Please fix required items before submitting.",
                "errors": validation.errors,
                "readiness_score": validation.readiness_score
            }
        )

    # Prepare Channel Partner digital routing
    routing_service = PartnerRoutingService(db)
    partner_meta = routing_service.prepare_application_routing(application)
    category_info, eligible_partners, assigned_partner = routing_service.find_eligible_partners_for_application(application)

    ref_code = (application.form_data or {}).get("partner_reference_code") or _generate_partner_reference(scheme.name, application.id)
    assigned_name = partner_meta.get("assigned_partner_name")
    assigned_type = partner_meta.get("assigned_partner_type")
    
    # Transition routing status to ROUTED_TO_PARTNER with audit event
    status_service = PartnerRoutingStatusService(db)
    routing_reason = (
        f"Dossier verified and routed to accredited partner {assigned_name} ({assigned_type}) with ref #{ref_code}."
        if assigned_name
        else f"Dossier verified and prepared for routing (Ref #{ref_code}). Awaiting nodal partner assignment."
    )
    status_service.transition_routing_status(
        application=application,
        to_status=PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        reason=routing_reason,
        actor=user,
        source="citizen_portal",
        partner_id=assigned_partner.partner_id if assigned_partner else None,
        partner_name=assigned_name
    )

    return {
        "message": "Application dossier successfully prepared and routed to channel partner",
        "partner_reference_code": ref_code,
        "application_id": str(application.id),
        "status": application.status,
        "routing_status": PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
        "partner_acknowledgement_status": PartnerAcknowledgementStatus.PENDING.value,
        "scheme_category": partner_meta.get("scheme_category"),
        "category_code": partner_meta.get("category_code"),
        "preferred_partner_type": partner_meta.get("preferred_partner_type"),
        "assigned_partner": assigned_partner.model_dump() if assigned_partner else None,
        "total_eligible_partners": len(eligible_partners),
        "eligible_partners": [p.model_dump() for p in eligible_partners],
        "official_portal_url": scheme.official_url,
        "helpline_number": scheme.helpline_number,
        "disclaimer": (
            "Yojantra compiles, validates, and routes your verified application dossier. "
            "Final biometric authentication or official submission may be finalized on the designated government portal or at your accredited partner center."
        )
    }


@router.get("/{app_id}/partners", response_model=ApplicationPartnerRoutingResponse)
@router.get("/{app_id}/routing-partners", response_model=ApplicationPartnerRoutingResponse)
def get_application_routing_partners(
    app_id: UUID,
    lat: Optional[float] = Query(None, description="Applicant latitude for proximity ranking"),
    lng: Optional[float] = Query(None, description="Applicant longitude for proximity ranking"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find suitable accredited Channel Partners for this application and return routing readiness."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    routing_service = PartnerRoutingService(db)
    return routing_service.get_application_partner_routing(
        application=application,
        applicant_lat=lat,
        applicant_lng=lng
    )


@router.get("/{app_id}/routing-status", response_model=ApplicationRoutingStatusResponse)
def get_application_routing_status(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full routing status lifecycle, partner acknowledgement, and audit trail."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    status_service = PartnerRoutingStatusService(db)
    return status_service.get_routing_status_summary(application)


@router.post("/{app_id}/routing-status", response_model=ApplicationRoutingStatusResponse)
def update_application_routing_status(
    app_id: UUID,
    update_req: RoutingStatusUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transition application routing status with strict state machine validation, role authorization, and audit logging.
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    status_service = PartnerRoutingStatusService(db)
    status_service.transition_routing_status(
        application=application,
        to_status=update_req.to_status,
        reason=update_req.reason,
        actor=user,
        source=update_req.source or "portal",
        partner_id=update_req.partner_id,
        partner_name=update_req.partner_name
    )

    return status_service.get_routing_status_summary(application)


@router.post("/{app_id}/partner-response", response_model=ApplicationRoutingStatusResponse)
def submit_partner_response_action(
    app_id: UUID,
    response_req: PartnerResponseActionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authorized Channel Partner & Nodal Officer action endpoint for:
    - PARTNER_RECEIVED: Official acknowledgement of docket receipt
    - UNDER_REVIEW: Technical and financial appraisal in progress
    - DOCUMENTS_REQUIRED: Query raised requesting additional compliance documents (requires reason)
    - APPROVED: Sanction approved by committee
    - REJECTED: Application declined (requires reason)
    """
    if user.role not in ["admin", "super_admin", "partner_officer", "nodal_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only accredited channel partner officers, nodal officers, or administrators can submit partner responses."
        )

    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    action_status = response_req.action.upper().strip()
    status_service = PartnerRoutingStatusService(db)
    status_service.transition_routing_status(
        application=application,
        to_status=action_status,
        reason=response_req.reason,
        actor=user,
        source=response_req.source or "partner_portal",
        partner_id=response_req.partner_id,
        partner_name=response_req.partner_name
    )

    return status_service.get_routing_status_summary(application)


@router.get("/{app_id}/tracking", response_model=ApplicationTrackingResponse)
def get_application_tracking(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Comprehensive applicant tracking endpoint:
    Returns full timeline, assigned partner, partner receipt acknowledgement,
    documents-required alerts, approval/rejection details, disbursement progress,
    audit history, and clear next action.
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    scheme = application.scheme
    form_data = application.form_data or {}
    ref_code = form_data.get("partner_reference_code") or (scheme and _generate_partner_reference(scheme.name, application.id))

    status_service = PartnerRoutingStatusService(db)
    current_routing_status = status_service.get_current_routing_status(application)
    ack_status = status_service.get_partner_acknowledgement_status(application)
    raw_history = status_service.get_routing_history(application)
    
    partner_routing = form_data.get("partner_routing", {})
    assigned_name = partner_routing.get("assigned_partner_name")
    assigned_type = partner_routing.get("assigned_partner_type")

    tracking_details = _compute_application_tracking_details(
        app=application,
        scheme=scheme,
        routing_status=current_routing_status,
        ack_status=ack_status,
        routing_history=raw_history,
        assigned_partner_name=assigned_name,
        assigned_partner_type=assigned_type
    )

    timeline = _build_application_timeline(application, scheme)

    # Format history entries
    history_entries = []
    for h in raw_history:
        ts = h.get("timestamp")
        if isinstance(ts, str):
            try:
                parsed_ts = datetime.fromisoformat(ts)
            except Exception:
                parsed_ts = datetime.now(timezone.utc)
        elif isinstance(ts, datetime):
            parsed_ts = ts
        else:
            parsed_ts = datetime.now(timezone.utc)

        history_entries.append(RoutingHistoryEntry(
            from_status=h.get("from_status"),
            to_status=h.get("to_status") or current_routing_status,
            timestamp=parsed_ts,
            partner_id=h.get("partner_id"),
            partner_name=h.get("partner_name"),
            reason=h.get("reason", ""),
            actor=h.get("actor", "system"),
            actor_role=h.get("actor_role", "system"),
            source=h.get("source", "system")
        ))

    return ApplicationTrackingResponse(
        application_id=application.id,
        scheme_id=application.scheme_id,
        scheme_name=scheme.name if scheme else "Government Scheme",
        ministry=scheme.ministry if scheme else None,
        partner_reference_code=ref_code,
        status=application.status,
        routing_status=current_routing_status,
        partner_acknowledgement_status=ack_status,
        assigned_partner=tracking_details["assigned_partner_details"],
        timeline=timeline,
        documents_required_alert=tracking_details["documents_required_alert"],
        approval_details=tracking_details["approval_details"],
        rejection_details=tracking_details["rejection_details"],
        disbursement_progress=tracking_details["disbursement_progress"],
        clear_next_action=tracking_details["clear_next_action"],
        routing_history=history_entries,
        created_at=application.created_at,
        updated_at=application.updated_at
    )


@router.post("/{app_id}/resolve-document-request", response_model=ApplicationTrackingResponse)
def resolve_document_request(
    app_id: UUID,
    resolve_req: ResolveDocumentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Applicant endpoint to resolve an active DOCUMENTS_REQUIRED query.
    Transitions status to UNDER_REVIEW, records audit entry, and notifies the partner desk.
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    check_resource_ownership(application.user_id, user, "application")

    status_service = PartnerRoutingStatusService(db)
    curr_status = status_service.get_current_routing_status(application)

    if curr_status != PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resolve document request for application in status '{curr_status}'. Status must be 'DOCUMENTS_REQUIRED'."
        )

    res_comment = resolve_req.comments.strip() if resolve_req.comments else "Uploaded requested compliance documents."
    status_service.transition_routing_status(
        application=application,
        to_status=PartnerRoutingStatus.UNDER_REVIEW.value,
        reason=f"Applicant submitted compliance response: {res_comment}",
        actor=user,
        source="citizen_portal"
    )

    return get_application_tracking(app_id=app_id, user=user, db=db)




