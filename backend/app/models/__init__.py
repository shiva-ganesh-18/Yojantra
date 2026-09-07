"""SQLAlchemy ORM models for SchemeMatch AI."""
from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, DateTime, 
    Text, Numeric, ForeignKey, JSON, Uuid
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    """User entity representing entrepreneurs."""
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    full_name = Column(String(255), default="")
    gender = Column(String(50), nullable=True)
    social_category = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    state = Column(String(100), default="")
    district = Column(String(100), default="")
    block_tehsil = Column(String(100), nullable=True)
    village_ward = Column(String(100), nullable=True)
    is_rural = Column(Boolean, default=True)
    preferred_language = Column(String(10), default="hi")
    literacy_level = Column(String(50), default="literate")
    aadhaar_hash = Column(String(64), nullable=True)
    udyam_number = Column(String(50), nullable=True)
    dpiit_number = Column(String(50), nullable=True)
    gstin = Column(String(20), nullable=True)
    fssai_license = Column(String(50), nullable=True)
    role = Column(String(20), default="user", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    @property
    def age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    # Relationships
    business = relationship("Business", back_populates="user", uselist=False, cascade="all, delete-orphan")
    matches = relationship("UserSchemeMatch", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user")


class Business(Base):
    """Enterprise/Business entity associated with a user."""
    __tablename__ = "businesses"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    business_name = Column(String(255), nullable=True)
    business_type = Column(String(100), nullable=True)
    business_stage = Column(String(50), nullable=True)
    annual_turnover_inr = Column(Numeric(14, 2), nullable=True)
    num_employees = Column(Integer, default=0)
    num_women_employees = Column(Integer, default=0)
    years_in_operation = Column(Numeric(6, 2), nullable=True)
    sector = Column(String(100), nullable=True)
    is_women_led = Column(Boolean, default=False)
    is_sc_st_led = Column(Boolean, default=False)
    registration_type = Column(String(100), nullable=True)
    bank_ifsc = Column(String(20), nullable=True)
    has_collateral = Column(Boolean, default=False)
    funding_needed_inr = Column(Numeric(14, 2), nullable=True)
    funding_purpose = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationship
    user = relationship("User", back_populates="business")


class Scheme(Base):
    """Government welfare & credit scheme entity."""
    __tablename__ = "schemes"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    ministry = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    scheme_type = Column(String(50), nullable=True, index=True)
    status = Column(String(20), default="active", index=True)
    max_benefit_inr = Column(Numeric(14, 2), nullable=True)
    min_benefit_inr = Column(Numeric(14, 2), nullable=True)
    benefit_description = Column(Text, nullable=True)
    interest_rate = Column(Numeric(5, 2), nullable=True)
    subsidy_percentage = Column(Numeric(5, 2), nullable=True)
    max_loan_amount_inr = Column(Numeric(14, 2), nullable=True)
    collateral_required = Column(Boolean, default=False)
    application_mode = Column(String(20), nullable=True)
    official_url = Column(String(500), nullable=True)
    helpline_number = Column(String(50), nullable=True)
    application_deadline = Column(Date, nullable=True)
    is_national = Column(Boolean, default=True)
    applicable_states = Column(JSON, nullable=True)
    target_genders = Column(JSON, nullable=True)
    target_social_categories = Column(JSON, nullable=True)
    target_business_types = Column(JSON, nullable=True)
    target_business_stages = Column(JSON, nullable=True)
    min_turnover_inr = Column(Numeric(14, 2), nullable=True)
    max_turnover_inr = Column(Numeric(14, 2), nullable=True)
    min_employees = Column(Integer, nullable=True)
    max_employees = Column(Integer, nullable=True)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    women_ownership_min_percent = Column(Integer, nullable=True)
    requires_udyam = Column(Boolean, default=False)
    requires_gst = Column(Boolean, default=False)
    requires_dpiit = Column(Boolean, default=False)
    documents_required = Column(JSON, nullable=True)
    application_steps = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    @property
    def requires_collateral(self) -> bool:
        return bool(self.collateral_required)

    @requires_collateral.setter
    def requires_collateral(self, value: bool):
        self.collateral_required = value

    # Relationships
    matches = relationship("UserSchemeMatch", back_populates="scheme", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="scheme")
    rules = relationship("EligibilityRule", back_populates="scheme", cascade="all, delete-orphan")
    benefits = relationship("Benefit", back_populates="scheme", cascade="all, delete-orphan")


class UserSchemeMatch(Base):
    """Calculated match record between a user and a scheme."""
    __tablename__ = "user_scheme_matches"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(Uuid(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Numeric(5, 2), nullable=False)
    eligibility_status = Column(String(50), nullable=False)
    confidence_level = Column(String(20), nullable=False)
    match_reasons = Column(JSON, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    is_recommended = Column(Boolean, default=False, index=True)
    is_bookmarked = Column(Boolean, default=False, index=True)
    is_applied = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="matches")
    scheme = relationship("Scheme", back_populates="matches")


class Application(Base):
    """Scheme application tracking entity."""
    __tablename__ = "applications"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(Uuid(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(20), default="online")
    status = Column(String(50), default="draft", index=True)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=3)
    next_action = Column(String(255), nullable=True)
    next_action_deadline = Column(Date, nullable=True)
    form_data = Column(JSON, nullable=True)
    documents_uploaded = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="applications")
    scheme = relationship("Scheme", back_populates="applications")


class CSCCenter(Base):
    """Common Service Center entity."""
    __tablename__ = "csc_centers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    csc_id = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    block = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    pincode = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    services_offered = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)


class Document(Base):
    """Uploaded and OCR-verified document entity."""
    __tablename__ = "documents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)
    doc_number_hash = Column(String(64), nullable=True)
    file_url = Column(String(500), nullable=False)
    file_format = Column(String(20), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    ocr_extracted_text = Column(Text, nullable=True)
    verification_status = Column(String(50), default="pending")
    verified_at = Column(DateTime, nullable=True)
    meta_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def __init__(self, **kwargs):
        if "metadata" in kwargs:
            kwargs["meta_info"] = kwargs.pop("metadata")
        super().__init__(**kwargs)

    # Relationship
    user = relationship("User", back_populates="documents")


class Notification(Base):
    """Multi-channel user notification entity."""
    __tablename__ = "notifications"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    channel = Column(String(50), default="push")
    priority = Column(String(20), default="medium")
    is_read = Column(Boolean, default=False, index=True)
    action_url = Column(String(500), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    meta_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    def __init__(self, **kwargs):
        if "metadata" in kwargs:
            kwargs["meta_info"] = kwargs.pop("metadata")
        super().__init__(**kwargs)

    # Relationship
    user = relationship("User", back_populates="notifications")


class Conversation(Base):
    """AI Chat session and messages history entity."""
    __tablename__ = "conversations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    channel = Column(String(20), default="text")
    language = Column(String(10), default="hi")
    messages = Column(JSON, default=list)
    intent_detected = Column(String(50), nullable=True)
    schemes_discussed = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationship
    user = relationship("User", back_populates="conversations")


class AuditLog(Base):
    """Audit log entity for compliance and tracking."""
    __tablename__ = "audit_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=utc_now)


class SchemeBookmark(Base):
    """Explicit bookmark tracking entity."""
    __tablename__ = "scheme_bookmarks"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(Uuid(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)


class EligibilityRule(Base):
    """Structured eligibility condition for a scheme."""
    __tablename__ = "eligibility_rules"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(Uuid(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    operator = Column(String(20), nullable=False, default="in")
    rule_value = Column(JSON, nullable=True)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationship
    scheme = relationship("Scheme", back_populates="rules")


class Benefit(Base):
    """Financial or service benefit provided by a scheme."""
    __tablename__ = "scheme_benefits"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(Uuid(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    benefit_type = Column(String(50), nullable=False)
    amount_min = Column(Numeric(14, 2), nullable=True)
    amount_max = Column(Numeric(14, 2), nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)
    interest_rate = Column(Numeric(5, 2), nullable=True)
    description = Column(Text, nullable=True)
    disbursement_mode = Column(String(50), default="bank_loan")
    created_at = Column(DateTime, default=utc_now)

    # Relationship
    scheme = relationship("Scheme", back_populates="benefits")


class OTPVerification(Base):
    """Persistent OTP tracking with attempt limiting and expiry."""
    __tablename__ = "otp_verifications"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), nullable=False, index=True)
    otp_hash = Column(String(128), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)


__all__ = [
    "User",
    "Business",
    "Scheme",
    "EligibilityRule",
    "Benefit",
    "OTPVerification",
    "UserSchemeMatch",
    "Application",
    "CSCCenter",
    "Document",
    "Notification",
    "Conversation",
    "AuditLog",
    "SchemeBookmark",
    "UserFeedback",
]
