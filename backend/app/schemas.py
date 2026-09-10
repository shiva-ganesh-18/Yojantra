"""Pydantic schemas for request/response validation."""
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: str = Field(..., min_length=2, max_length=255)
    gender: Optional[str] = Field(None, pattern=r"^(male|female|transgender|other|prefer_not_to_say)$")
    social_category: Optional[str] = Field(None, pattern=r"^(general|sc|st|obc|pwd|minority)$")
    date_of_birth: Optional[date] = None
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    block_tehsil: Optional[str] = None
    village_ward: Optional[str] = None
    is_rural: bool = True
    preferred_language: str = "hi"
    literacy_level: Optional[str] = "literate"


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    social_category: Optional[str] = None
    date_of_birth: Optional[date] = None
    state: Optional[str] = None
    district: Optional[str] = None
    block_tehsil: Optional[str] = None
    village_ward: Optional[str] = None
    is_rural: Optional[bool] = None
    preferred_language: Optional[str] = None
    literacy_level: Optional[str] = None
    aadhaar_hash: Optional[str] = None
    udyam_number: Optional[str] = None
    dpiit_number: Optional[str] = None
    gstin: Optional[str] = None
    fssai_license: Optional[str] = None
    onboarding_completed: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    phone: Optional[str] = None
    email: Optional[str] = None
    full_name: str = ""
    gender: Optional[str] = None
    social_category: Optional[str] = None
    date_of_birth: Optional[date] = None
    literacy_level: Optional[str] = None
    state: str = ""
    district: str = ""
    block_tehsil: Optional[str] = None
    village_ward: Optional[str] = None
    is_rural: bool = True
    preferred_language: str = "hi"
    role: str = "user"
    onboarding_completed: bool = False
    auth_provider: str = "google"
    firebase_uid: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_completion_percentage: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== BUSINESS SCHEMAS ====================

class BusinessCreate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = Field(None, pattern=r"^(manufacturing|service|trading|agriculture|food_processing|technology|handicraft|retail|other)$")
    business_stage: Optional[str] = Field(None, pattern=r"^(idea|pre_revenue|revenue|growth|mature)$")
    annual_turnover_inr: Optional[Decimal] = None
    num_employees: int = 0
    num_women_employees: int = 0
    years_in_operation: Optional[Decimal] = None
    sector: Optional[str] = None
    is_women_led: bool = False
    is_sc_st_led: bool = False
    registration_type: Optional[str] = None
    bank_ifsc: Optional[str] = None
    has_collateral: bool = False
    funding_needed_inr: Optional[Decimal] = None
    funding_purpose: Optional[str] = None


class BusinessResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_stage: Optional[str] = None
    sector: Optional[str] = None
    registration_type: Optional[str] = None
    annual_turnover_inr: Optional[Decimal] = None
    years_in_operation: Optional[Decimal] = None
    num_employees: int = 0
    num_women_employees: int = 0
    is_women_led: bool = False
    is_sc_st_led: bool = False
    has_collateral: bool = False
    funding_needed_inr: Optional[Decimal] = None
    funding_purpose: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEME SCHEMAS ====================

class SchemeBase(BaseModel):
    name: str
    ministry: str
    description: str
    scheme_type: Optional[str] = None
    status: str = "active"
    max_benefit_inr: Optional[Decimal] = None
    min_benefit_inr: Optional[Decimal] = None
    benefit_description: Optional[str] = None
    interest_rate: Optional[Decimal] = None
    subsidy_percentage: Optional[Decimal] = None
    max_loan_amount_inr: Optional[Decimal] = None
    collateral_required: Optional[bool] = None
    application_mode: Optional[str] = None
    official_url: Optional[str] = None
    helpline_number: Optional[str] = None
    application_deadline: Optional[date] = None
    is_national: bool = True
    applicable_states: Optional[List[str]] = None
    target_genders: Optional[List[str]] = None
    target_social_categories: Optional[List[str]] = None
    target_business_types: Optional[List[str]] = None
    target_business_stages: Optional[List[str]] = None
    min_turnover_inr: Optional[Decimal] = None
    max_turnover_inr: Optional[Decimal] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    requires_udyam: bool = False
    requires_gst: bool = False
    requires_dpiit: bool = False
    documents_required: Optional[List[Dict[str, Any]]] = None
    application_steps: Optional[List[Dict[str, Any]]] = None


class SchemeCreate(SchemeBase):
    pass


class SchemeResponse(SchemeBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchemeSearchParams(BaseModel):
    q: Optional[str] = None
    ministry: Optional[str] = None
    scheme_type: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    page: int = 1
    page_size: int = 20


# ==================== MATCH & ELIGIBILITY SCHEMAS ====================

class MatchReason(BaseModel):
    field: str
    expected: Any
    actual: Any
    match: bool


class EligibilityRuleCheck(BaseModel):
    rule_id: str
    category: str  # e.g., 'Demographics', 'Enterprise', 'Location', 'Compliance'
    label: str
    expected: str
    actual: str
    status: str  # 'PASS' | 'FAIL' | 'UNKNOWN'
    details: Optional[str] = None
    is_mandatory: bool = True


class ScoreBreakdown(BaseModel):
    demographic_score: Decimal = Decimal("0")  # max 25
    enterprise_score: Decimal = Decimal("0")   # max 25
    financial_score: Decimal = Decimal("0")    # max 25
    compliance_score: Decimal = Decimal("0")   # max 25
    total_score: Decimal = Decimal("0")        # sum (0-100)
    rationale: List[str] = Field(default_factory=list)


class LoanRecommendation(BaseModel):
    recommended_loan_amount: Optional[Decimal] = None
    min_scheme_benefit: Optional[Decimal] = None
    max_scheme_benefit: Optional[Decimal] = None
    estimated_subsidy_amount: Optional[Decimal] = None
    subsidy_percentage: Optional[Decimal] = None
    margin_money_required: Optional[Decimal] = None
    margin_money_percentage: Optional[Decimal] = None
    interest_rate_percent: Optional[Decimal] = None
    moratorium_period_months: Optional[int] = 6
    repayment_tenure_months: Optional[int] = 54
    total_tenure_months: Optional[int] = 60
    estimated_monthly_emi: Optional[Decimal] = None
    tenure_months: Optional[int] = 60
    moratorium_note: Optional[str] = None
    subsidy_disclaimer: Optional[str] = None


class SchemeMatchResponse(BaseModel):
    scheme_id: UUID
    name: str
    ministry: str
    match_score: Decimal
    recommendation_score: Optional[Decimal] = None
    eligibility_status: str  # 'PASS' | 'FAIL' | 'UNKNOWN' or 'Eligible'
    overall_verdict: str = "PASS"  # 'PASS' | 'FAIL' | 'UNKNOWN'
    confidence_level: str
    reasons: List[MatchReason]
    criteria_checks: List[EligibilityRuleCheck] = Field(default_factory=list)
    score_breakdown: Optional[ScoreBreakdown] = None
    loan_recommendation: Optional[LoanRecommendation] = None
    ai_explanation: Optional[str] = None
    why_this_scheme: List[str] = Field(default_factory=list)
    why_you_match: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    potential_issues: List[str] = Field(default_factory=list)
    next_action: Optional[str] = None
    benefit_description: Optional[str] = None
    scheme_type: Optional[str] = "loan"
    official_url: Optional[str] = None
    helpline_number: Optional[str] = None
    application_deadline: Optional[date] = None
    is_bookmarked: bool = False
    is_applied: bool = False


class MatchRequest(BaseModel):
    refresh: bool = False


class SchemeCompareRequest(BaseModel):
    scheme_ids: List[UUID] = Field(..., min_length=2, max_length=4)


class SchemeCompareItem(BaseModel):
    scheme: SchemeResponse
    match_data: Optional[SchemeMatchResponse] = None


class SchemeCompareResponse(BaseModel):
    schemes: List[SchemeCompareItem]
    common_criteria: List[str]
    differing_features: List[Dict[str, Any]]
    recommendation_summary: str


# ==================== DOCUMENT & READINESS SCHEMAS ====================

class ExtractedDocFields(BaseModel):
    doc_type: str
    doc_number_masked: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    address: Optional[str] = None
    business_name: Optional[str] = None
    registration_type: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account_masked: Optional[str] = None
    income_annual_inr: Optional[Union[float, int]] = None
    social_category: Optional[str] = None
    confidence_score: float = 0.85
    verification_tier: str = "Internal Heuristic OCR (Not Official Govt API)"


class DocumentChecklistItem(BaseModel):
    doc_type: str
    name: str
    description: str
    is_mandatory: bool = True
    is_uploaded: bool = False
    is_verified: bool = False
    document_id: Optional[UUID] = None
    uploaded_at: Optional[datetime] = None
    status: str = "missing"  # 'missing' | 'uploaded' | 'verified' | 'rejected'
    extracted_preview: Optional[Dict[str, Any]] = None


class DocumentReadinessResponse(BaseModel):
    scheme_id: Optional[UUID] = None
    scheme_name: Optional[str] = "General Enterprise Readiness"
    readiness_score: int  # 0 to 100
    is_ready_to_apply: bool
    total_required: int
    total_uploaded: int
    total_verified: int
    missing_mandatory_count: int
    checklist: List[DocumentChecklistItem]
    missing_documents: List[str]
    readiness_summary: str
    tamper_duplicate_warnings: List[str] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    id: UUID
    doc_type: str
    verification_status: str
    verification_tier: str = "Internal Heuristic OCR (Not Official Govt API)"
    ocr_preview: Optional[str] = None
    extracted_fields: Optional[ExtractedDocFields] = None
    duplicate_warning: Optional[str] = None
    message: str


class AutoFillProfileResponse(BaseModel):
    success: bool
    updated_fields: List[str]
    message: str
    user_profile: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None



# ==================== APPLICATION SCHEMAS ====================

class ApplicationTimelineEvent(BaseModel):
    step: int
    title: str
    status: str  # 'completed' | 'current' | 'pending' | 'failed'
    timestamp: Optional[datetime] = None
    note: Optional[str] = None
    channel_or_portal: Optional[str] = None


class PreSubmissionCheckItem(BaseModel):
    category: str  # 'profile' | 'business' | 'documents' | 'eligibility'
    field_or_doc: str
    label: str
    is_valid: bool
    message: str
    severity: str = "error"  # 'error' | 'warning' | 'info'


class PreSubmissionValidationResponse(BaseModel):
    application_id: UUID
    scheme_id: UUID
    scheme_name: str
    is_ready_to_submit: bool
    readiness_score: int  # 0 to 100
    errors: List[str]
    warnings: List[str]
    checks: List[PreSubmissionCheckItem]
    official_portal_url: Optional[str] = None
    partner_reference_code: Optional[str] = None
    submission_mode: str = "Channel Partner / Nodal Portal Hand-off"
    disclaimer: str = (
        "Yojantra compiles, validates, and routes your verified application dossier. "
        "Final biometric authentication or official submission may be finalized on the designated government portal or at your accredited partner center."
    )


class ApplicationChecklistItem(BaseModel):
    id: str
    title: str
    category: str  # 'document' | 'compliance' | 'step'
    description: str
    is_completed: bool
    is_mandatory: bool = True
    action_url: Optional[str] = None
    # Shared Document Vault reuse status (exact canonical match only).
    is_verified: bool = False
    document_id: Optional[UUID] = None
    vault_status: str = "missing"  # 'verified' | 'uploaded' | 'missing'


class ApplicationChecklistResponse(BaseModel):
    application_id: UUID
    scheme_id: UUID
    scheme_name: str
    ministry: Optional[str] = None
    total_items: int
    completed_items: int
    completion_percentage: int
    items: List[ApplicationChecklistItem]
    official_portal_url: Optional[str] = None
    helpline_number: Optional[str] = None


class ApplicationCreate(BaseModel):
    scheme_id: UUID
    channel: str = Field(default="online", pattern=r"^(online|offline|csc)$")
    requested_amount_inr: Optional[Decimal] = None
    application_data: Optional[Dict[str, Any]] = None


class ApplicationUpdate(BaseModel):
    form_data: Optional[Dict[str, Any]] = None
    documents_uploaded: Optional[List[Dict[str, Any]]] = None
    current_step: Optional[int] = None
    status: Optional[str] = None
    next_action: Optional[str] = None
    next_action_deadline: Optional[date] = None


class DocumentsRequiredAlert(BaseModel):
    is_active: bool = True
    reason: str
    requested_at: Optional[datetime] = None
    requested_by: Optional[str] = None
    action_required: str = "Please upload the requested documents to resume scrutiny."
    can_resolve: bool = True


class ApprovalDetails(BaseModel):
    is_approved: bool = True
    approved_at: Optional[datetime] = None
    sanction_reference: Optional[str] = None
    approved_by: Optional[str] = None
    reason_or_remarks: Optional[str] = None
    subsidy_amount_inr: Optional[Decimal] = None


class RejectionDetails(BaseModel):
    is_rejected: bool = True
    rejected_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    reason: str
    can_reapply: bool = False


class DisbursementProgress(BaseModel):
    status: str = "NOT_STARTED"  # NOT_STARTED | PROCESSING | DISBURSED
    channel: str = "Direct Benefit Transfer (PFMS Aadhaar Bridge)"
    disbursed_at: Optional[datetime] = None
    reference_number: Optional[str] = None
    remarks: Optional[str] = None


class ClearNextAction(BaseModel):
    action_title: str
    action_description: str
    action_type: str = "AWAIT_REVIEW"  # UPLOAD_DOCS | SUBMIT_APPLICATION | AWAIT_REVIEW | AWAIT_DISBURSEMENT | COMPLETED | REVIEW_REJECTION
    action_url: Optional[str] = None
    deadline: Optional[date] = None
    is_applicant_action_required: bool = False


class RoutingHistoryEntry(BaseModel):
    from_status: Optional[str] = None
    to_status: str
    timestamp: datetime
    partner_id: Optional[str] = None
    partner_name: Optional[str] = None
    reason: str
    actor: str
    actor_role: str
    source: str


class ApplicationTrackingResponse(BaseModel):
    application_id: UUID
    scheme_id: UUID
    scheme_name: str
    ministry: Optional[str] = None
    partner_reference_code: Optional[str] = None
    status: str
    routing_status: str
    partner_acknowledgement_status: str
    assigned_partner: Optional[Dict[str, Any]] = None
    timeline: List[ApplicationTimelineEvent] = Field(default_factory=list)
    documents_required_alert: Optional[DocumentsRequiredAlert] = None
    approval_details: Optional[ApprovalDetails] = None
    rejection_details: Optional[RejectionDetails] = None
    disbursement_progress: Optional[DisbursementProgress] = None
    clear_next_action: ClearNextAction
    routing_history: List[RoutingHistoryEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


class ResolveDocumentRequest(BaseModel):
    comments: Optional[str] = Field(default="", description="Applicant explanation or notes regarding compliance documents")
    uploaded_doc_ids: Optional[List[UUID]] = Field(default_factory=list, description="IDs of newly uploaded documents")


class ApplicationResponse(BaseModel):
    id: UUID
    scheme_id: UUID
    scheme_name: Optional[str] = None
    ministry: Optional[str] = None
    channel: str = "online"
    status: str
    partner_reference_code: Optional[str] = None
    current_step: int
    total_steps: Optional[int]
    next_action: Optional[str]
    next_action_deadline: Optional[date]
    official_portal_url: Optional[str] = None
    helpline_number: Optional[str] = None
    readiness_score: Optional[int] = 0
    is_ready_to_submit: Optional[bool] = False
    submission_disclaimer: Optional[str] = None
    timeline: List[ApplicationTimelineEvent] = Field(default_factory=list)
    form_data: Optional[Dict[str, Any]] = None
    assigned_partner_name: Optional[str] = None
    assigned_partner_type: Optional[str] = None
    scheme_category: Optional[str] = None
    routing_status: Optional[str] = "NOT_ROUTED"
    partner_acknowledgement_status: Optional[str] = "NOT_ROUTED"
    routing_history: List[Dict[str, Any]] = Field(default_factory=list)
    documents_required_alert: Optional[DocumentsRequiredAlert] = None
    approval_details: Optional[ApprovalDetails] = None
    rejection_details: Optional[RejectionDetails] = None
    disbursement_progress: Optional[DisbursementProgress] = None
    clear_next_action: Optional[ClearNextAction] = None
    assigned_partner_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationPartnerRoutingItem(BaseModel):
    """Channel Partner details for application digital routing."""
    partner_id: UUID
    partner_name: str
    short_name: Optional[str] = None
    partner_type: str
    supported_scheme_category: str
    location: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    is_eligible: bool = True
    is_preferred: bool = False
    status: str = "active"
    routing_status: str = "Eligible Channel Partner"
    eligibility_verdict: str = "NEEDS_VERIFICATION"  # 'ELIGIBLE' | 'INELIGIBLE' | 'NEEDS_VERIFICATION'
    eligibility_reason: Optional[str] = None
    geographic_tier: Optional[str] = None  # 'district' | 'state' | 'national'
    distance_km: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sync_status: Optional[str] = "CONFIGURATION_READY"
    is_authenticated_live: bool = False
    gross_npa_ratio: Optional[Decimal] = None
    npa_risk_indicator: Optional[str] = "UNKNOWN"
    capacity_tier: Optional[str] = "UNVERIFIED"
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    recommendation_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationPartnerRoutingResponse(BaseModel):
    """Eligible Channel Partners and routing readiness response for an application."""
    application_id: UUID
    scheme_id: UUID
    scheme_name: str
    scheme_category: str
    category_code: str
    preferred_partner_type: Optional[str] = None
    routing_channel: str = "online"
    partner_reference_code: Optional[str] = None
    total_eligible_partners: int
    total_needs_verification_partners: int = 0
    assigned_partner: Optional[ApplicationPartnerRoutingItem] = None
    eligible_partners: List[ApplicationPartnerRoutingItem] = Field(default_factory=list)
    excluded_partners: List[ApplicationPartnerRoutingItem] = Field(default_factory=list)
    routing_note: str
    disclaimer: str = (
        "Yojantra compiles, validates, and routes your verified application dossier to accredited channel partners. "
        "Final appraisal and disbursement are conducted by the designated nodal bank or channelizing agency."
    )


class RoutingStatusUpdateRequest(BaseModel):
    to_status: str
    reason: str
    partner_id: Optional[UUID] = None
    partner_name: Optional[str] = None
    source: Optional[str] = "portal"


class PartnerResponseActionRequest(BaseModel):
    action: str = Field(description="Partner response action: PARTNER_RECEIVED, UNDER_REVIEW, DOCUMENTS_REQUIRED, APPROVED, REJECTED")
    reason: Optional[str] = Field(default="", description="Reason for action. Required when requesting documents or rejecting.")
    partner_id: Optional[UUID] = None
    partner_name: Optional[str] = None
    source: Optional[str] = "partner_portal"


class ApplicationRoutingStatusResponse(BaseModel):
    application_id: UUID
    current_routing_status: str
    partner_acknowledgement_status: str
    assigned_partner_id: Optional[str] = None
    assigned_partner_name: Optional[str] = None
    assigned_partner_type: Optional[str] = None
    partner_reference_code: Optional[str] = None
    allowed_next_transitions: List[str]
    history: List[RoutingHistoryEntry] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class PartnerUploadedDocSummary(BaseModel):
    id: UUID
    doc_type: str
    file_format: Optional[str] = None
    file_size_bytes: Optional[int] = None
    verification_status: str
    extracted_number: Optional[str] = None
    ocr_preview: Optional[str] = None
    created_at: datetime


class PartnerDashboardApplicationItem(BaseModel):
    id: UUID
    user_id: UUID
    scheme_id: UUID
    scheme_name: str
    ministry: Optional[str] = None
    applicant_name: str
    applicant_phone: Optional[str] = None
    applicant_email: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    social_category: Optional[str] = None
    business_name: Optional[str] = None
    requested_amount_inr: Optional[float] = None
    status: str
    routing_status: str
    partner_acknowledgement_status: str
    partner_reference_code: Optional[str] = None
    assigned_partner_id: Optional[str] = None
    assigned_partner_name: Optional[str] = None
    assigned_partner_type: Optional[str] = None
    partner_npa_ratio: Optional[float] = None
    partner_npa_risk: Optional[str] = None
    partner_funds_available: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    current_step: int = 1


class PartnerDashboardApplicationsListResponse(BaseModel):
    items: List[PartnerDashboardApplicationItem]
    total: int
    page: int
    page_size: int
    status_counts: Dict[str, int] = Field(default_factory=dict)


class PartnerDashboardApplicationDetailResponse(BaseModel):
    application: PartnerDashboardApplicationItem
    applicant_profile: Dict[str, Any]
    business_profile: Optional[Dict[str, Any]] = None
    scheme_details: Dict[str, Any]
    routing_summary: ApplicationRoutingStatusResponse
    documents: List[PartnerUploadedDocSummary] = Field(default_factory=list)
    validation: Optional[Dict[str, Any]] = None
    partner_health: Optional[Dict[str, Any]] = None


class PartnerDashboardKPIResponse(BaseModel):
    total_assigned: int
    pending_action_count: int
    under_review_count: int
    docs_required_count: int
    approved_count: int
    rejected_count: int
    total_sanction_amount_inr: float
    status_breakdown: Dict[str, int] = Field(default_factory=dict)
    partner_summary: Optional[Dict[str, Any]] = None





# ==================== CHAT SCHEMAS ====================

class ChatMessageRequest(BaseModel):
    message: str
    language: Optional[str] = "hi"
    channel: str = Field(default="text", pattern=r"^(text|voice)$")
    session_id: Optional[str] = None


class SchemeCitation(BaseModel):
    id: Optional[UUID] = None
    name: str
    ministry: Optional[str] = None
    max_benefit_inr: Optional[Decimal] = None
    subsidy_percentage: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    official_url: Optional[str] = None
    helpline_number: Optional[str] = None
    effective_date: Optional[str] = "FY 2024-25"
    last_updated: Optional[str] = "March 2025"
    source_agency: Optional[str] = "Official Central/State Gazette"


class ChatMessageResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    schemes_mentioned: Optional[List[UUID]] = None
    cited_schemes: Optional[List[SchemeCitation]] = Field(default_factory=list)
    actions: Optional[List[Dict[str, Any]]] = None
    session_id: str
    source: str = Field(default="ai", description="Response source: 'gemini_ai', 'openai_ai', or 'rule_based_fallback'")
    disclaimer: str = Field(
        default=(
            "Statutory Notice: Yojantra AI provides informational guidance grounded in official scheme gazettes. "
            "This guidance does NOT constitute an official government sanction, letter of intent, or guaranteed loan approval. "
            "Final sanction and subsidy disbursement depend on nodal bank scrutiny and DBT rules."
        ),
        description="Statutory informational notice"
    )


class ChatStatusResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    provider: str
    is_ai_live: bool
    model_name: Optional[str] = None
    indexed_schemes_count: int
    fallback_engine: str = "rule_based_deterministic_rag"
    disclaimer: str = (
        "Statutory Advisory: Yojantra AI is strictly informational and does not guarantee government approval or loan sanction."
    )
    capabilities: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class EligibilityExplanationRequest(BaseModel):
    scheme_id: UUID
    custom_profile: Optional[Dict[str, Any]] = None


class EligibilityExplanationResponse(BaseModel):
    scheme_id: UUID
    scheme_name: str
    ministry: Optional[str] = None
    overall_status: str
    match_score_percentage: float
    satisfied_conditions: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    affirmative_benefits: List[str] = Field(default_factory=list)
    explanation: str
    required_documents_explanation: List[Dict[str, str]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    official_url: Optional[str] = None
    helpline_number: Optional[str] = None
    disclaimer: str = (
        "Statutory Notice: This eligibility evaluation is an indicative guidance match based on published scheme rules. "
        "It does NOT constitute an official government sanction or loan approval. Final approval depends on lending bank credit appraisal and nodal department scrutiny."
    )


class LoanEMICalculationRequest(BaseModel):
    scheme_id: UUID
    loan_amount_inr: float = Field(..., gt=0)
    tenure_months: Optional[int] = Field(None, gt=0)


class LoanEMICalculationResponse(BaseModel):
    scheme_id: UUID
    scheme_name: str
    loan_amount_inr: float
    benchmark_interest_rate_percent: float
    tenure_months: int
    moratorium_months: int
    indicative_monthly_emi_inr: float
    total_repayment_inr: float
    total_interest_inr: float
    capital_subsidy_amount_inr: Optional[float] = None
    effective_net_loan_inr: Optional[float] = None
    collateral_free_status: str
    formula_used: str = "EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]"
    disclaimer: str = (
        "Indicative Estimate: EMI and interest amounts are calculated at the scheme benchmark rate. "
        "Actual interest rates, moratorium, processing charges, and repayment schedules are subject to financing bank terms and appraisal."
    )



# ==================== AUTH SCHEMAS ====================

class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=10, description="Firebase ID token from frontend Google Sign-In")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== NOTIFICATION SCHEMAS ====================

class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    is_read: bool
    action_url: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== ADMIN SCHEMAS ====================

class DashboardMetrics(BaseModel):
    total_users: int
    active_users_today: int
    total_schemes: int
    total_matches: int
    total_applications: int
    applications_by_status: Dict[str, int]
    top_schemes: List[Dict[str, Any]]
    user_demographics: Dict[str, Any]


# ==================== LOCATION & INSTITUTION SCHEMAS ====================

class StateResponse(BaseModel):
    code: str
    name: str
    type: str = "State"  # State or Union Territory
    districts_count: int = 0


class DistrictResponse(BaseModel):
    name: str
    state: str


class CityResponse(BaseModel):
    name: str
    district: str
    state: str


class InstitutionResponse(BaseModel):
    id: UUID
    name: str
    short_name: Optional[str] = None
    code: Optional[str] = None
    institution_type: Optional[str] = None  # SCA, PSB, RRB, NBFC-MFI, Facilitation Center
    state: str
    district: str
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    affiliation: Optional[str] = None
    nirf_rank: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = "active"
    distance_km: Optional[float] = None
    geographic_tier: Optional[str] = None
    is_eligible_for_scheme: bool = True
    eligibility_verdict: Optional[str] = "ELIGIBLE"
    navigation_url: Optional[str] = None
    schemes_handled: List[str] = Field(default_factory=list)
    fund_availability_status: str = "Eligible Channel Type"  # "Eligible Channel Type" | "Availability Not Verified"
    fund_disclosure: str = "Fund availability and current quota are not verified in real time. Contact the partner to confirm current availability."
    recommendation_rank: int = 1
    is_best_partner: bool = False
    recommendation_reason: Optional[str] = None
    contact_phone: Optional[str] = None
    working_hours: Optional[str] = "10:00 AM - 5:00 PM (Mon-Fri)"
    
    # Live Banking & CBS Integration Fields (LIVE / CONFIGURATION_READY / FALLBACK)
    sync_status: str = "CONFIGURATION_READY"  # LIVE | CONFIGURATION_READY | FALLBACK
    provider_name: Optional[str] = "Yojantra Channel Partner Framework"
    provider_id: Optional[str] = "cbs-sca-gateway"
    last_synced_at: Optional[datetime] = None
    is_authenticated_live: bool = False
    fund_utilization_percentage: Optional[Decimal] = None
    available_lending_capacity_inr: Optional[Decimal] = None
    capacity_tier: str = "UNVERIFIED"  # HIGH | MODERATE | CONSTRAINED | UNVERIFIED
    gross_npa_ratio: Optional[Decimal] = None
    npa_risk_indicator: str = "UNKNOWN"  # LOW | MODERATE | ELEVATED | UNKNOWN
    is_lending_halted: bool = False
    disbursement_sla_days: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PartnerRecommendationSummary(BaseModel):
    selected_scheme_id: Optional[UUID] = None
    selected_scheme_name: Optional[str] = None
    total_partners_found: int
    best_partner: Optional[InstitutionResponse] = None
    best_partner_reason: Optional[str] = None
    partners_by_type: Dict[str, int] = Field(default_factory=dict)
    partners: List[InstitutionResponse] = Field(default_factory=list)
    banking_integration_status: Optional[Dict[str, Any]] = None


class InstitutionRequestCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    city: Optional[str] = None
    requested_by_email: Optional[str] = None


class InstitutionRequestResponse(BaseModel):
    id: UUID
    name: str
    state: str
    district: str
    city: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PRODUCTION GOVERNMENT INTEGRATIONS SCHEMAS ====================

class IntegrationStatusResponse(BaseModel):
    service_name: str
    is_available: bool
    status: str  # "connected" | "mock_sandbox" | "unconfigured"
    auth_tier: str
    description: str
    official_portal_url: Optional[str] = None


class DigiLockerAuthURLResponse(BaseModel):
    auth_url: str
    state: str
    environment: str
    disclaimer: str


class DigiLockerPullRequest(BaseModel):
    doc_type: str = Field(..., description="Document type to pull: 'aadhaar' | 'pan' | 'udyam' | 'caste_certificate'")
    auth_code: Optional[str] = None


class AadhaarVerifyRequest(BaseModel):
    aadhaar_last_four: str = Field(..., pattern=r"^[0-9]{4}$", description="Last 4 digits only (Never collect full 12 digits)")
    consent_given: bool = Field(..., description="Citizen explicit consent under DPDP Act 2023")


class AadhaarVerifyResponse(BaseModel):
    success: bool
    status: str
    masked_aadhaar: str
    verification_tier: str
    verified_at: datetime
    message: str


class PANVerifyRequest(BaseModel):
    pan_number: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", description="Standard 10-character alphanumeric PAN")
    consent_given: bool = Field(..., description="Citizen explicit consent for Income Tax Department database verification")


class PANVerifyResponse(BaseModel):
    success: bool
    status: str
    masked_pan: str
    category: str
    verification_tier: str
    verified_at: datetime
    message: str


class UdyamVerifyRequest(BaseModel):
    udyam_number: str = Field(..., pattern=r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$", description="Official UDYAM registration number")
    consent_given: bool = Field(..., description="Citizen consent for MSME portal verification")


class UdyamVerifyResponse(BaseModel):
    success: bool
    status: str
    udyam_number: str
    enterprise_name: Optional[str] = None
    enterprise_type: Optional[str] = None
    major_activity: Optional[str] = None
    verification_tier: str
    verified_at: datetime
    message: str


class GovSchemeSyncResponse(BaseModel):
    total_schemes_checked: int
    schemes_updated: int
    sync_source: str
    synced_at: datetime
    status: str
    message: str


class ApplicationStatusSyncResponse(BaseModel):
    application_id: UUID
    partner_reference_code: str
    current_status: str
    last_synced_at: datetime
    sync_source: str
    official_portal_url: Optional[str] = None
    message: str


# ==================== FINANCIAL CALCULATOR & LOAN SIMULATION SCHEMAS ====================

class MonthlyPaymentBreakdown(BaseModel):
    month_number: int
    phase: str
    opening_balance: Decimal
    monthly_payment: Decimal
    principal_component: Decimal
    interest_component: Decimal
    closing_balance: Decimal
    status_note: str


class LoanSimulationRequest(BaseModel):
    principal_amount: Decimal = Field(..., gt=0, description="Requested principal loan amount in INR")
    tenure_months: Optional[int] = Field(None, gt=0, le=360, description="Total tenure in months (defaults to scheme standard)")
    moratorium_months: Optional[int] = Field(None, ge=0, description="Moratorium / gestation period in months")
    interest_rate_percent: Optional[Decimal] = Field(None, ge=0, description="Annual interest rate percentage (defaults to scheme database rate)")
    include_schedule: bool = Field(True, description="Whether to include full month-by-month repayment breakdown")


class LoanSimulationResponse(BaseModel):
    scheme_id: Optional[UUID] = None
    scheme_name: Optional[str] = None
    principal_amount: Decimal
    interest_rate_percent: Decimal
    rate_source: str
    total_tenure_months: int
    moratorium_months: int
    active_repayment_months: int
    monthly_emi: Decimal
    total_interest: Decimal
    total_repayment: Decimal
    max_loan_limit_inr: Optional[Decimal] = None
    is_within_limit: bool = True
    limit_warning: Optional[str] = None
    estimated_subsidy_amount: Optional[Decimal] = None
    subsidy_percentage: Optional[Decimal] = None
    net_effective_loan: Optional[Decimal] = None
    monthly_schedule: List[MonthlyPaymentBreakdown] = []
    moratorium_note: Optional[str] = None
    disclaimer: str


# ==================== PART 10: GOVERNMENT & BANKING INTEGRATION SCHEMAS ====================

class CBSPartnerMetricsResponse(BaseModel):
    partner_id: Optional[UUID] = None
    partner_code: Optional[str] = None
    partner_name: str
    institution_type: str
    operational_status: str = "Active"
    lead_bank_active: bool = True
    branch_code: Optional[str] = None
    disbursement_sla_days: Optional[int] = None
    system_health: str = "OPTIMAL"  # "OPTIMAL" | "DEGRADED" | "OFFLINE" | "UNCONFIGURED"
    sync_status: str = "CONFIGURATION_READY"  # "LIVE" | "CONFIGURATION_READY" | "FALLBACK"
    provider_name: str = "National Core Banking (CBS) & SCA Gateway"
    is_authenticated_live: bool = False
    last_synced_at: Optional[datetime] = None
    disclosure: str


class NPAFundUtilizationResponse(BaseModel):
    partner_id: Optional[UUID] = None
    partner_code: Optional[str] = None
    partner_name: str
    fund_allocation_inr: Optional[Decimal] = None
    fund_utilized_inr: Optional[Decimal] = None
    fund_utilization_percentage: Optional[Decimal] = None
    gross_npa_ratio: Optional[Decimal] = None
    net_npa_ratio: Optional[Decimal] = None
    npa_risk_indicator: str = "UNKNOWN"  # "LOW" | "MODERATE" | "ELEVATED" | "UNKNOWN"
    is_lending_halted: bool = False
    sync_status: str = "CONFIGURATION_READY"
    provider_name: str = "National Core Banking (CBS) & SCA Gateway"
    is_authenticated_live: bool = False
    last_synced_at: Optional[datetime] = None
    disclosure: str


class PartnerLendingCapacityResponse(BaseModel):
    partner_id: Optional[UUID] = None
    partner_code: Optional[str] = None
    partner_name: str
    sanctioned_quota_inr: Optional[Decimal] = None
    allocated_quota_inr: Optional[Decimal] = None
    available_lending_capacity_inr: Optional[Decimal] = None
    capacity_tier: str = "UNVERIFIED"  # "HIGH" | "MODERATE" | "CONSTRAINED" | "UNVERIFIED"
    is_lending_halted: bool = False
    sync_status: str = "CONFIGURATION_READY"
    provider_name: str = "National Core Banking (CBS) & SCA Gateway"
    is_authenticated_live: bool = False
    last_synced_at: Optional[datetime] = None
    disclosure: str


class PFMSDisbursementQueryRequest(BaseModel):
    application_id: Optional[UUID] = None
    partner_reference_code: Optional[str] = None
    sanction_reference_number: Optional[str] = None
    beneficiary_account_last_four: Optional[str] = None


class PFMSDisbursementStatusResponse(BaseModel):
    application_id: Optional[UUID] = None
    partner_reference_code: Optional[str] = None
    sanction_reference_number: Optional[str] = None
    dbt_status: str = "CONFIGURATION_READY"  # "BENEFICIARY_CREDITED" | "IN_PROCESS" | "PFMS_INITIATED" | "PAYMENT_REJECTED" | "CONFIGURATION_READY" | "UNAVAILABLE"
    amount_inr: Optional[Decimal] = None
    transaction_utr: Optional[str] = None
    pfms_payment_id: Optional[str] = None
    credit_timestamp: Optional[datetime] = None
    bank_name: Optional[str] = None
    account_number_masked: Optional[str] = None
    sync_status: str = "CONFIGURATION_READY"  # "LIVE" | "CONFIGURATION_READY" | "FALLBACK"
    provider_name: str = "PFMS / Aadhaar Payment Bridge (APB)"
    is_authenticated_live: bool = False
    last_synced_at: Optional[datetime] = None
    error_details: Optional[str] = None
    disclosure: str


class InboundWebhookPayload(BaseModel):
    event_id: str
    event_type: str  # "PARTNER_METRICS_UPDATED" | "NPA_THRESHOLD_EXCEEDED" | "CAPACITY_UPDATED" | "LENDING_HALTED" | "PFMS_DISBURSEMENT_SETTLED" | "PFMS_DISBURSEMENT_FAILED"
    timestamp: datetime
    data: Dict[str, Any]
    source: Optional[str] = "gov_banking_gateway"


class BankingWebhookResponse(BaseModel):
    success: bool
    event_id: str
    event_type: str
    processed_at: datetime
    message: str
    audit_logged: bool = False



