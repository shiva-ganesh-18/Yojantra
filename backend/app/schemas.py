"""Pydantic schemas for request/response validation."""
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
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


class UserResponse(BaseModel):
    id: UUID
    phone: str
    email: Optional[str] = None
    full_name: str = ""
    gender: Optional[str] = None
    social_category: Optional[str] = None
    state: str = ""
    district: str = ""
    is_rural: bool = True
    preferred_language: str = "hi"
    role: str = "user"
    onboarding_completed: bool = False
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
    business_name: Optional[str]
    business_type: Optional[str]
    business_stage: Optional[str]
    annual_turnover_inr: Optional[Decimal]
    num_employees: int
    is_women_led: bool
    has_collateral: bool
    funding_needed_inr: Optional[Decimal]

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


# ==================== MATCH SCHEMAS ====================

class MatchReason(BaseModel):
    field: str
    expected: Any
    actual: Any
    match: bool


class SchemeMatchResponse(BaseModel):
    scheme_id: UUID
    name: str
    ministry: str
    match_score: Decimal
    eligibility_status: str
    confidence_level: str
    reasons: List[MatchReason]
    ai_explanation: Optional[str] = None
    benefit_description: Optional[str] = None
    official_url: Optional[str] = None
    helpline_number: Optional[str] = None
    application_deadline: Optional[date] = None
    is_bookmarked: bool = False
    is_applied: bool = False


class MatchRequest(BaseModel):
    refresh: bool = False


# ==================== APPLICATION SCHEMAS ====================

class ApplicationCreate(BaseModel):
    scheme_id: UUID
    channel: str = Field(default="online", pattern=r"^(online|offline|csc)$")


class ApplicationUpdate(BaseModel):
    form_data: Optional[Dict[str, Any]] = None
    documents_uploaded: Optional[List[Dict[str, Any]]] = None
    current_step: Optional[int] = None
    status: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: UUID
    scheme_id: UUID
    scheme_name: Optional[str] = None
    status: str
    current_step: int
    total_steps: Optional[int]
    next_action: Optional[str]
    next_action_deadline: Optional[date]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== CHAT SCHEMAS ====================

class ChatMessageRequest(BaseModel):
    message: str
    language: Optional[str] = "hi"
    channel: str = Field(default="text", pattern=r"^(text|voice)$")
    session_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    schemes_mentioned: Optional[List[UUID]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    session_id: str
    source: str = Field(default="ai", description="Response source: 'ai' or 'rule_based_fallback'")


# ==================== AUTH SCHEMAS ====================

class OTPSendRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")


class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    otp: str = Field(..., pattern=r"^[0-9]{6}$")


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
