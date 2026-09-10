"""Admin and Partner dashboard router with strict role-based access control."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric, or_, String
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

import uuid
from app.core.database import get_db
from app.core.security import verify_token
from app.schemas import (
    DashboardMetrics, SchemeCreate, SchemeResponse, UserResponse,
    PartnerDashboardApplicationItem, PartnerDashboardApplicationsListResponse,
    PartnerDashboardApplicationDetailResponse, PartnerDashboardKPIResponse,
    PartnerUploadedDocSummary, ApplicationRoutingStatusResponse,
    PartnerResponseActionRequest
)
from app.models import User, Scheme, Application, UserSchemeMatch, Business, Institution, Document
from app.services.partner_routing_status_service import (
    PartnerRoutingStatusService,
    PartnerRoutingStatus,
    PartnerAcknowledgementStatus
)
from app.routers.applications import _compute_application_validation

router = APIRouter(prefix="/admin", tags=["Admin"])
security_bearer = HTTPBearer(auto_error=False)


def get_current_partner_or_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Validate Bearer token and ensure user has admin, super_admin, partner_officer, or nodal_officer role."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    role = payload.get("role", "user")
    if role not in ["admin", "super_admin", "partner_officer", "nodal_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin, Partner Officer, or Nodal Officer authorization required"
        )

    sub_val = payload.get("sub")
    try:
        user_uuid = uuid.UUID(sub_val) if isinstance(sub_val, str) else sub_val
    except Exception:
        user_uuid = None

    user = db.query(User).filter(User.id == user_uuid).first() if user_uuid else None
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or account disabled"
        )

    if user.role not in ["admin", "super_admin", "partner_officer", "nodal_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin, Partner Officer, or Nodal Officer authorization required"
        )

    return user


def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Validate Bearer token and ensure user has admin or super_admin role."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    role = payload.get("role", "user")
    if role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin authorization required"
        )

    sub_val = payload.get("sub")
    try:
        user_uuid = uuid.UUID(sub_val) if isinstance(sub_val, str) else sub_val
    except Exception:
        user_uuid = None

    user = db.query(User).filter(User.id == user_uuid).first() if user_uuid else None
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or account disabled"
        )

    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin authorization required"
        )

    return user


@router.get("/analytics/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard metrics with real database counts."""
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.updated_at >= datetime.utcnow() - timedelta(days=1)
    ).count()
    total_schemes = db.query(Scheme).filter(Scheme.status == "active").count()
    total_matches = db.query(UserSchemeMatch).count()
    total_applications = db.query(Application).count()

    # Applications by status
    status_counts = db.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    applications_by_status = {s: c for s, c in status_counts}

    # Top schemes by match count
    top_schemes = db.query(
        Scheme.name, func.count(UserSchemeMatch.id)
    ).join(UserSchemeMatch, Scheme.id == UserSchemeMatch.scheme_id).group_by(Scheme.name).order_by(
        func.count(UserSchemeMatch.id).desc()
    ).limit(5).all()

    # User demographics
    gender_dist = db.query(
        User.gender, func.count(User.id)
    ).filter(User.gender.isnot(None)).group_by(User.gender).all()

    category_dist = db.query(
        User.social_category, func.count(User.id)
    ).filter(User.social_category.isnot(None)).group_by(User.social_category).all()

    return DashboardMetrics(
        total_users=total_users,
        active_users_today=active_today,
        total_schemes=total_schemes,
        total_matches=total_matches,
        total_applications=total_applications,
        applications_by_status=applications_by_status,
        top_schemes=[{"name": name, "matches": count} for name, count in top_schemes],
        user_demographics={
            "gender": {g or "Unspecified": c for g, c in gender_dist},
            "category": {c or "Unspecified": n for c, n in category_dist}
        }
    )


@router.get("/schemes", response_model=List[SchemeResponse])
def admin_list_schemes(
    page: int = 1,
    page_size: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all schemes for admin."""
    schemes = db.query(Scheme).offset((page - 1) * page_size).limit(page_size).all()
    return [SchemeResponse.model_validate(s) for s in schemes]


@router.post("/schemes", response_model=SchemeResponse)
def admin_create_scheme(
    scheme: SchemeCreate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new scheme (admin only)."""
    db_scheme = Scheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return SchemeResponse.model_validate(db_scheme)


@router.get("/users", response_model=List[UserResponse])
def admin_list_users(
    page: int = 1,
    page_size: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List registered entrepreneurs (admin only)."""
    users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/analytics/bias")
def get_bias_report(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get bias audit report across social categories."""
    results = db.query(
        User.social_category,
        func.avg(cast(UserSchemeMatch.match_score, Numeric)).label("avg_score"),
        func.count(UserSchemeMatch.id).label("count")
    ).join(User, UserSchemeMatch.user_id == User.id).group_by(User.social_category).all()

    return {
        "match_scores_by_category": [
            {
                "category": cat or "Not Specified",
                "avg_score": round(float(score), 2) if score is not None else 0.0,
                "count": count
            }
            for cat, score, count in results
        ]
    }


@router.post("/schemes/match-all")
def admin_match_all_schemes(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Trigger scheme matching for all onboarded entrepreneurs (admin only)."""
    from app.services.matching_engine import get_matching_engine

    users = db.query(User).filter(User.onboarding_completed == True).all()
    engine = get_matching_engine(db)
    total_processed = 0
    total_matches = 0

    for u in users:
        try:
            matches = engine.match_user(u.id, refresh=True)
            total_matches += len(matches)
            total_processed += 1
        except Exception:
            continue

    return {
        "status": "success",
        "users_processed": total_processed,
        "total_matches_generated": total_matches
    }


# ==================== PARTNER & ADMIN DASHBOARD QUEUE ====================

def _build_partner_app_item(
    app: Application,
    status_service: PartnerRoutingStatusService,
    institution_cache: Dict[str, Optional[Institution]],
    db: Session
) -> PartnerDashboardApplicationItem:
    form_data = app.form_data or {}
    pr = form_data.get("partner_routing", {})
    curr_routing_status = status_service.get_current_routing_status(app)
    ack_status = status_service.get_partner_acknowledgement_status(app)
    
    assigned_p_id = pr.get("assigned_partner_id")
    inst = None
    if assigned_p_id:
        if assigned_p_id not in institution_cache:
            try:
                p_uuid = uuid.UUID(assigned_p_id) if isinstance(assigned_p_id, str) else assigned_p_id
                institution_cache[assigned_p_id] = db.query(Institution).filter(Institution.id == p_uuid).first()
            except Exception:
                institution_cache[assigned_p_id] = None
        inst = institution_cache.get(assigned_p_id)
        
    npa_ratio = None
    npa_risk = "UNKNOWN"
    funds_avail = True
    if inst:
        if hasattr(inst, "gross_npa_ratio") and inst.gross_npa_ratio is not None:
            try:
                npa_ratio = float(inst.gross_npa_ratio)
            except Exception:
                pass
        elif getattr(inst, "meta_info", None) and "gross_npa_ratio" in inst.meta_info:
            try:
                npa_ratio = float(inst.meta_info["gross_npa_ratio"])
            except Exception:
                pass
        if hasattr(inst, "npa_risk_indicator") and inst.npa_risk_indicator is not None:
            npa_risk = str(inst.npa_risk_indicator)
        elif getattr(inst, "meta_info", None) and "npa_risk_indicator" in inst.meta_info:
            npa_risk = str(inst.meta_info["npa_risk_indicator"])
        if hasattr(inst, "is_lending_halted") and inst.is_lending_halted is not None:
            funds_avail = not bool(inst.is_lending_halted)
        elif getattr(inst, "meta_info", None) and "is_lending_halted" in inst.meta_info:
            funds_avail = not bool(inst.meta_info["is_lending_halted"])

    # Extract requested amount
    req_amt = form_data.get("requested_amount_inr")
    if req_amt is None and app.scheme and app.scheme.max_benefit_inr:
        try:
            req_amt = float(app.scheme.max_benefit_inr)
        except Exception:
            pass

    applicant = app.user
    biz = applicant.business if applicant else None

    return PartnerDashboardApplicationItem(
        id=app.id,
        user_id=app.user_id,
        scheme_id=app.scheme_id,
        scheme_name=app.scheme.name if app.scheme else "Government Scheme",
        ministry=app.scheme.ministry if app.scheme else None,
        applicant_name=applicant.full_name if applicant and applicant.full_name else "Applicant",
        applicant_phone=applicant.phone if applicant else None,
        applicant_email=applicant.email if applicant else None,
        state=applicant.state if applicant else None,
        district=applicant.district if applicant else None,
        social_category=applicant.social_category if applicant else None,
        business_name=(biz.business_name or getattr(biz, "name", None)) if biz else None,
        requested_amount_inr=float(req_amt) if req_amt is not None else None,
        status=app.status,
        routing_status=curr_routing_status,
        partner_acknowledgement_status=ack_status,
        partner_reference_code=form_data.get("partner_reference_code"),
        assigned_partner_id=assigned_p_id,
        assigned_partner_name=pr.get("assigned_partner_name"),
        assigned_partner_type=pr.get("assigned_partner_type"),
        partner_npa_ratio=npa_ratio,
        partner_npa_risk=npa_risk,
        partner_funds_available=funds_avail,
        created_at=app.created_at,
        updated_at=app.updated_at,
        current_step=app.current_step or 1
    )


@router.get("/partner/overview", response_model=PartnerDashboardKPIResponse)
def get_partner_dashboard_kpis(
    user: User = Depends(get_current_partner_or_admin_user),
    db: Session = Depends(get_db)
):
    """Executive KPI summary for the partner review queue."""
    all_apps = db.query(Application).all()
    status_service = PartnerRoutingStatusService(db)
    
    status_breakdown: Dict[str, int] = {}
    pending_action = 0
    under_review = 0
    docs_required = 0
    approved = 0
    rejected = 0
    total_sanction_amt = 0.0

    for app in all_apps:
        st = status_service.get_current_routing_status(app)
        status_breakdown[st] = status_breakdown.get(st, 0) + 1

        if st in [PartnerRoutingStatus.ROUTED_TO_PARTNER.value, PartnerRoutingStatus.PARTNER_RECEIVED.value]:
            pending_action += 1
        elif st == PartnerRoutingStatus.UNDER_REVIEW.value:
            under_review += 1
            pending_action += 1
        elif st == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
            docs_required += 1
            pending_action += 1
        elif st in [PartnerRoutingStatus.APPROVED.value, PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value, PartnerRoutingStatus.DISBURSED.value]:
            approved += 1
        elif st == PartnerRoutingStatus.REJECTED.value:
            rejected += 1

        form_data = app.form_data or {}
        amt = form_data.get("requested_amount_inr")
        if amt is None and app.scheme and app.scheme.max_benefit_inr:
            amt = float(app.scheme.max_benefit_inr)
        if amt:
            try:
                total_sanction_amt += float(amt)
            except Exception:
                pass

    return PartnerDashboardKPIResponse(
        total_assigned=len(all_apps),
        pending_action_count=pending_action,
        under_review_count=under_review,
        docs_required_count=docs_required,
        approved_count=approved,
        rejected_count=rejected,
        total_sanction_amount_inr=round(total_sanction_amt, 2),
        status_breakdown=status_breakdown
    )


@router.get("/partner/applications", response_model=PartnerDashboardApplicationsListResponse)
def list_partner_applications(
    status: Optional[str] = Query(None, description="Filter by routing status (e.g. ROUTED_TO_PARTNER, UNDER_REVIEW, APPROVED)"),
    search: Optional[str] = Query(None, description="Search by applicant name, phone, email, reference code, scheme name"),
    scheme_id: Optional[UUID] = Query(None, description="Filter by scheme ID"),
    partner_id: Optional[UUID] = Query(None, description="Filter by partner institution ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_partner_or_admin_user),
    db: Session = Depends(get_db)
):
    """
    List applications assigned to partner or all applications for administrative oversight.
    Supports filtering by routing status, search across applicants, and live NPA status.
    """
    query = db.query(Application).join(User, Application.user_id == User.id).join(Scheme, Application.scheme_id == Scheme.id)

    if scheme_id:
        query = query.filter(Application.scheme_id == scheme_id)

    if search:
        s_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(s_term),
                User.phone.ilike(s_term),
                User.email.ilike(s_term),
                Scheme.name.ilike(s_term)
            )
        )

    all_apps = query.order_by(Application.created_at.desc()).all()
    status_service = PartnerRoutingStatusService(db)
    institution_cache: Dict[str, Optional[Institution]] = {}

    status_counts: Dict[str, int] = {}
    filtered_items: List[PartnerDashboardApplicationItem] = []

    for app in all_apps:
        item = _build_partner_app_item(app, status_service, institution_cache, db)
        
        # Track counts across all visible applications
        st = item.routing_status
        status_counts[st] = status_counts.get(st, 0) + 1

        # Check partner_id filter
        if partner_id and item.assigned_partner_id != str(partner_id):
            continue

        # Check status filter
        if status:
            target_statuses = [s.strip().upper() for s in status.split(",")]
            if item.routing_status.upper() not in target_statuses and item.status.upper() not in target_statuses:
                continue

        filtered_items.append(item)

    total_filtered = len(filtered_items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = filtered_items[start_idx:end_idx]

    return PartnerDashboardApplicationsListResponse(
        items=paged_items,
        total=total_filtered,
        page=page,
        page_size=page_size,
        status_counts=status_counts
    )


@router.get("/partner/applications/{app_id}", response_model=PartnerDashboardApplicationDetailResponse)
def get_partner_application_detail(
    app_id: UUID,
    user: User = Depends(get_current_partner_or_admin_user),
    db: Session = Depends(get_db)
):
    """Detailed view of an application including applicant demographics, documents, validation, and live NPA status."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    status_service = PartnerRoutingStatusService(db)
    institution_cache: Dict[str, Optional[Institution]] = {}
    item = _build_partner_app_item(application, status_service, institution_cache, db)

    applicant = application.user
    scheme = application.scheme
    business = applicant.business if applicant else None

    # Documents
    user_docs = db.query(Document).filter(Document.user_id == application.user_id).order_by(Document.created_at.desc()).all()
    doc_summaries = []
    for d in user_docs:
        meta = d.meta_info or {}
        ext_fields = meta.get("extracted_fields") or {}
        masked_num = meta.get("extracted_number") or ext_fields.get("doc_number_masked")
        doc_summaries.append(PartnerUploadedDocSummary(
            id=d.id,
            doc_type=d.doc_type,
            file_format=d.file_format,
            file_size_bytes=d.file_size_bytes,
            verification_status=d.verification_status,
            extracted_number=masked_num,
            ocr_preview=d.ocr_extracted_text[:200] + "..." if d.ocr_extracted_text and len(d.ocr_extracted_text) > 200 else d.ocr_extracted_text,
            created_at=d.created_at
        ))

    # Pre-submission checks
    validation_payload = None
    if applicant and scheme:
        val_res = _compute_application_validation(application, applicant, scheme, user_docs)
        validation_payload = val_res.model_dump()

    # Routing status summary & audit trail
    routing_summary = status_service.get_routing_status_summary(application)

    # Live partner health
    partner_health = None
    if item.assigned_partner_id:
        inst = institution_cache.get(item.assigned_partner_id)
        if inst:
            partner_health = {
                "partner_id": str(inst.id),
                "partner_name": inst.name,
                "short_name": inst.short_name,
                "institution_type": inst.institution_type,
                "state": inst.state,
                "district": inst.district,
                "gross_npa_ratio": item.partner_npa_ratio,
                "npa_risk_indicator": item.partner_npa_risk,
                "funds_available": item.partner_funds_available,
                "status": inst.status
            }

    applicant_profile = {
        "id": str(applicant.id) if applicant else None,
        "full_name": applicant.full_name if applicant else "Anonymous",
        "phone": applicant.phone if applicant else None,
        "email": applicant.email if applicant else None,
        "state": applicant.state if applicant else None,
        "district": applicant.district if applicant else None,
        "social_category": applicant.social_category if applicant else None,
        "gender": applicant.gender if applicant else None,
        "is_rural": applicant.is_rural if applicant else None,
        "date_of_birth": applicant.date_of_birth.isoformat() if applicant and applicant.date_of_birth else None
    }

    biz_profile = None
    if business:
        biz_profile = {
            "id": str(business.id),
            "name": business.name,
            "enterprise_type": business.enterprise_type,
            "registration_type": business.registration_type,
            "udyam_number": business.udyam_number,
            "annual_turnover_inr": float(business.annual_turnover_inr) if business.annual_turnover_inr is not None else None,
            "investment_plant_machinery_inr": float(business.investment_plant_machinery_inr) if business.investment_plant_machinery_inr is not None else None,
            "sector": business.sector
        }

    scheme_details = {
        "id": str(scheme.id) if scheme else None,
        "name": scheme.name if scheme else "Unknown",
        "ministry": scheme.ministry if scheme else None,
        "description": scheme.description if scheme else None,
        "max_benefit_inr": float(scheme.max_benefit_inr) if scheme and scheme.max_benefit_inr else None,
        "status": scheme.status if scheme else None
    }

    return PartnerDashboardApplicationDetailResponse(
        application=item,
        applicant_profile=applicant_profile,
        business_profile=biz_profile,
        scheme_details=scheme_details,
        routing_summary=ApplicationRoutingStatusResponse.model_validate(routing_summary),
        documents=doc_summaries,
        validation=validation_payload,
        partner_health=partner_health
    )


@router.post("/partner/applications/{app_id}/action", response_model=ApplicationRoutingStatusResponse)
def submit_partner_application_action(
    app_id: UUID,
    req: PartnerResponseActionRequest,
    user: User = Depends(get_current_partner_or_admin_user),
    db: Session = Depends(get_db)
):
    """
    Review action by authorized partner officer, nodal officer, or admin:
    PARTNER_RECEIVED, UNDER_REVIEW, DOCUMENTS_REQUIRED, APPROVED, REJECTED
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    action_status = req.action.upper().strip()
    status_service = PartnerRoutingStatusService(db)
    status_service.transition_routing_status(
        application=application,
        to_status=action_status,
        reason=req.reason,
        actor=user,
        source=req.source or "partner_dashboard",
        partner_id=req.partner_id,
        partner_name=req.partner_name
    )

    return status_service.get_routing_status_summary(application)

