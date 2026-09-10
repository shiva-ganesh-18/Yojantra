"""Application Channel Partner Routing Status Service.
Enforces the 10-state lifecycle state machine, transitions, audit trails, and security checks.
"""
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Application, User, Institution
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class PartnerRoutingStatus(str, Enum):
    """The 10 channel partner digital routing lifecycle states."""
    NOT_ROUTED = "NOT_ROUTED"
    PARTNER_ASSIGNED = "PARTNER_ASSIGNED"
    ROUTED_TO_PARTNER = "ROUTED_TO_PARTNER"
    PARTNER_RECEIVED = "PARTNER_RECEIVED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DOCUMENTS_REQUIRED = "DOCUMENTS_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSEMENT_PROCESSING = "DISBURSEMENT_PROCESSING"
    DISBURSED = "DISBURSED"


class PartnerAcknowledgementStatus(str, Enum):
    """Partner receipt acknowledgement status."""
    NOT_ROUTED = "NOT_ROUTED"
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"


# Permitted state transitions in the lifecycle
ALLOWED_ROUTING_TRANSITIONS: Dict[str, List[str]] = {
    PartnerRoutingStatus.NOT_ROUTED.value: [
        PartnerRoutingStatus.PARTNER_ASSIGNED.value,
        PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
    ],
    PartnerRoutingStatus.PARTNER_ASSIGNED.value: [
        PartnerRoutingStatus.NOT_ROUTED.value,
        PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
    ],
    PartnerRoutingStatus.ROUTED_TO_PARTNER.value: [
        PartnerRoutingStatus.PARTNER_RECEIVED.value,
        PartnerRoutingStatus.REJECTED.value,
    ],
    PartnerRoutingStatus.PARTNER_RECEIVED.value: [
        PartnerRoutingStatus.UNDER_REVIEW.value,
        PartnerRoutingStatus.DOCUMENTS_REQUIRED.value,
        PartnerRoutingStatus.REJECTED.value,
    ],
    PartnerRoutingStatus.UNDER_REVIEW.value: [
        PartnerRoutingStatus.DOCUMENTS_REQUIRED.value,
        PartnerRoutingStatus.APPROVED.value,
        PartnerRoutingStatus.REJECTED.value,
    ],
    PartnerRoutingStatus.DOCUMENTS_REQUIRED.value: [
        PartnerRoutingStatus.UNDER_REVIEW.value,
        PartnerRoutingStatus.REJECTED.value,
    ],
    PartnerRoutingStatus.APPROVED.value: [
        PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value,
        PartnerRoutingStatus.DISBURSED.value,
        PartnerRoutingStatus.REJECTED.value,
    ],
    PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value: [
        PartnerRoutingStatus.DISBURSED.value,
        PartnerRoutingStatus.REJECTED.value,
    ],
    PartnerRoutingStatus.REJECTED.value: [],
    PartnerRoutingStatus.DISBURSED.value: [],
}

# Transitions that a standard citizen user is authorized to perform
CITIZEN_ALLOWED_TRANSITIONS: List[str] = [
    PartnerRoutingStatus.PARTNER_ASSIGNED.value,
    PartnerRoutingStatus.ROUTED_TO_PARTNER.value,
    PartnerRoutingStatus.UNDER_REVIEW.value,  # Allowed only when resolving DOCUMENTS_REQUIRED
]


class PartnerRoutingStatusService:
    """Service to manage, validate, and audit partner routing statuses."""

    def __init__(self, db: Session):
        self.db = db

    def get_current_routing_status(self, application: Application) -> str:
        """Resolve current routing status, mapping legacy statuses if uninitialized."""
        form_data = application.form_data or {}
        partner_routing = form_data.get("partner_routing", {})
        existing_status = partner_routing.get("routing_status")
        
        # If valid enum state already present
        valid_values = {s.value for s in PartnerRoutingStatus}
        if existing_status in valid_values:
            return existing_status

        # Map legacy application status
        app_status = (application.status or "draft").lower()
        if app_status == "draft":
            if partner_routing.get("assigned_partner_id"):
                return PartnerRoutingStatus.PARTNER_ASSIGNED.value
            return PartnerRoutingStatus.NOT_ROUTED.value
        elif app_status == "submitted":
            return PartnerRoutingStatus.ROUTED_TO_PARTNER.value
        elif app_status == "under_review":
            return PartnerRoutingStatus.UNDER_REVIEW.value
        elif app_status == "approved":
            return PartnerRoutingStatus.APPROVED.value
        elif app_status == "disbursed":
            return PartnerRoutingStatus.DISBURSED.value
        elif app_status == "rejected":
            return PartnerRoutingStatus.REJECTED.value

        return PartnerRoutingStatus.NOT_ROUTED.value

    def get_partner_acknowledgement_status(self, application: Application) -> str:
        """Determine whether the channel partner has acknowledged receipt of the dossier."""
        current_status = self.get_current_routing_status(application)
        form_data = application.form_data or {}
        partner_routing = form_data.get("partner_routing", {})

        if current_status in [
            PartnerRoutingStatus.PARTNER_RECEIVED.value,
            PartnerRoutingStatus.UNDER_REVIEW.value,
            PartnerRoutingStatus.DOCUMENTS_REQUIRED.value,
            PartnerRoutingStatus.APPROVED.value,
            PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value,
            PartnerRoutingStatus.DISBURSED.value,
        ]:
            return PartnerAcknowledgementStatus.ACKNOWLEDGED.value
        elif current_status == PartnerRoutingStatus.ROUTED_TO_PARTNER.value:
            # Strictly do NOT fake partner acknowledgement: show pending
            return PartnerAcknowledgementStatus.PENDING.value
        elif current_status == PartnerRoutingStatus.REJECTED.value:
            return PartnerAcknowledgementStatus.REJECTED.value

        return PartnerAcknowledgementStatus.NOT_ROUTED.value

    def get_allowed_next_transitions(self, application: Application) -> List[str]:
        """Return list of valid next status transitions from current status."""
        current = self.get_current_routing_status(application)
        return ALLOWED_ROUTING_TRANSITIONS.get(current, [])

    def transition_routing_status(
        self,
        application: Application,
        to_status: str,
        reason: str,
        actor: User,
        source: str = "portal",
        partner_id: Optional[UUID] = None,
        partner_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transition application to a new routing status with validation, audit logging, and security checks.
        """
        valid_statuses = {s.value for s in PartnerRoutingStatus}
        if to_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid routing status '{to_status}'. Must be one of: {sorted(list(valid_statuses))}"
            )

        current_status = self.get_current_routing_status(application)
        allowed = ALLOWED_ROUTING_TRANSITIONS.get(current_status, [])

        # 1. Security / Role Checks
        is_admin_or_officer = actor.role in ["admin", "super_admin", "partner_officer", "nodal_officer"]
        is_owner = application.user_id == actor.id

        if not is_owner and not is_admin_or_officer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to access or transition this application."
            )

        if not is_admin_or_officer:
            # Standard citizen (applicant) constraints
            if to_status not in CITIZEN_ALLOWED_TRANSITIONS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Forbidden: Beneficiaries cannot self-verify, approve, disburse, or transition to '{to_status}'. "
                        "Action requires authorized nodal officer or administrator privileges."
                    )
                )
            if to_status == PartnerRoutingStatus.UNDER_REVIEW.value and current_status != PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Beneficiaries may only resume review status when submitting requested compliance documents."
                )

        # 2. Mandatory Reason Requirement
        clean_reason = (reason or "").strip()
        if to_status in [PartnerRoutingStatus.DOCUMENTS_REQUIRED.value, PartnerRoutingStatus.REJECTED.value]:
            if not clean_reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A reason is strictly required when transitioning application to '{to_status}'."
                )

        # 3. State Machine Transition Validation
        if to_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid routing status transition from '{current_status}' to '{to_status}'. "
                    f"Permitted next transitions: {allowed}"
                )
            )

        # 3. Resolve Partner Identity
        form_data = dict(application.form_data or {})
        partner_routing = dict(form_data.get("partner_routing", {}))

        final_partner_id = partner_id or partner_routing.get("assigned_partner_id")
        final_partner_name = partner_name or partner_routing.get("assigned_partner_name")

        if final_partner_id and not final_partner_name:
            inst = self.db.query(Institution).filter(Institution.id == final_partner_id).first()
            if inst:
                final_partner_name = inst.name

        now_iso = datetime.now(timezone.utc).isoformat()

        # 4. Record Audit Event
        history = list(form_data.get("routing_history", []))
        actor_identifier = actor.email or actor.phone or str(actor.id)

        audit_entry = {
            "from_status": current_status,
            "to_status": to_status,
            "timestamp": now_iso,
            "partner_id": str(final_partner_id) if final_partner_id else None,
            "partner_name": final_partner_name,
            "reason": reason.strip(),
            "actor": actor_identifier,
            "actor_role": actor.role,
            "source": source
        }
        history.append(audit_entry)
        form_data["routing_history"] = history

        # 5. Determine Acknowledgement Status
        ack_status = (
            PartnerAcknowledgementStatus.ACKNOWLEDGED.value
            if to_status in [
                PartnerRoutingStatus.PARTNER_RECEIVED.value,
                PartnerRoutingStatus.UNDER_REVIEW.value,
                PartnerRoutingStatus.DOCUMENTS_REQUIRED.value,
                PartnerRoutingStatus.APPROVED.value,
                PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value,
                PartnerRoutingStatus.DISBURSED.value,
            ]
            else (
                PartnerAcknowledgementStatus.PENDING.value
                if to_status == PartnerRoutingStatus.ROUTED_TO_PARTNER.value
                else (
                    PartnerAcknowledgementStatus.REJECTED.value
                    if to_status == PartnerRoutingStatus.REJECTED.value
                    else PartnerAcknowledgementStatus.NOT_ROUTED.value
                )
            )
        )

        partner_routing.update({
            "routing_status": to_status,
            "partner_acknowledgement_status": ack_status,
            "routing_status_updated_at": now_iso,
            "last_routing_reason": reason.strip(),
            "assigned_partner_id": str(final_partner_id) if final_partner_id else None,
            "assigned_partner_name": final_partner_name
        })
        form_data["partner_routing"] = partner_routing

        # 6. Synchronize Application Status and Step
        timeline_events = dict(form_data.get("timeline_events", {}))

        if to_status == PartnerRoutingStatus.NOT_ROUTED.value:
            application.status = "draft"
            application.current_step = 1
            application.next_action = "Select or configure accredited channel partner for scheme routing"
        elif to_status == PartnerRoutingStatus.PARTNER_ASSIGNED.value:
            application.status = "draft"
            application.current_step = 1
            application.next_action = f"Complete application validation for routing to {final_partner_name or 'channel partner'}"
        elif to_status == PartnerRoutingStatus.ROUTED_TO_PARTNER.value:
            application.status = "submitted"
            application.current_step = 2
            application.next_action = f"Under review by {final_partner_name}" if final_partner_name else "Under review by authorities"
            timeline_events["2"] = {
                "timestamp": now_iso,
                "note": f"Dossier transmitted to channel partner {final_partner_name or ''}. {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.PARTNER_RECEIVED.value:
            application.status = "submitted"
            application.current_step = 2
            application.next_action = f"Docket acknowledged by {final_partner_name or 'channel partner'}; awaiting scrutiny start"
            timeline_events["2"] = {
                "timestamp": now_iso,
                "note": f"Partner receipt confirmed by {final_partner_name or 'nodal officer'}. {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.UNDER_REVIEW.value:
            application.status = "under_review"
            application.current_step = 3
            application.next_action = f"Under financial & eligibility review by {final_partner_name or 'nodal committee'}"
            timeline_events["3"] = {
                "timestamp": now_iso,
                "note": f"Detailed appraisal in progress. {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
            application.status = "under_review"
            application.current_step = 3
            application.next_action = f"Additional documents requested: {reason.strip()}"
            timeline_events["3"] = {
                "timestamp": now_iso,
                "note": f"Compliance query raised by partner: {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.APPROVED.value:
            application.status = "approved"
            application.current_step = 4
            application.next_action = "Sanction letter issued; proceeding to direct benefit transfer / PFMS"
            timeline_events["4"] = {
                "timestamp": now_iso,
                "note": f"Subsidy / loan facility sanctioned by {final_partner_name or 'lead bank'}. {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.DISBURSEMENT_PROCESSING.value:
            application.status = "approved"
            application.current_step = 4
            application.next_action = "PFMS / DBT Aadhaar credit payment batch processing"
            timeline_events["4"] = {
                "timestamp": now_iso,
                "note": f"Credit transfer initiated via PFMS gateway. {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.DISBURSED.value:
            application.status = "disbursed"
            application.current_step = 4
            application.next_action = "Credit / capital subsidy successfully disbursed"
            timeline_events["4"] = {
                "timestamp": now_iso,
                "note": f"Disbursement completed. Reference confirmed. {reason.strip()}"
            }
        elif to_status == PartnerRoutingStatus.REJECTED.value:
            application.status = "rejected"
            application.next_action = f"Application rejected: {reason.strip()}"

        form_data["timeline_events"] = timeline_events
        application.form_data = form_data

        self.db.commit()
        self.db.refresh(application)

        # 7. Notify Citizen of Status Update
        try:
            notif = NotificationService(self.db)
            scheme_name = application.scheme.name if application.scheme else "Scheme Application"

            if to_status == PartnerRoutingStatus.PARTNER_RECEIVED.value:
                notif_title = f"Dossier Acknowledged: {scheme_name}"
                notif_body = f"Your application dossier has been received and acknowledged by {final_partner_name or 'channel partner'}. Nodal scrutiny will commence shortly."
                priority = "medium"
            elif to_status == PartnerRoutingStatus.UNDER_REVIEW.value:
                notif_title = f"Application Under Review: {scheme_name}"
                notif_body = f"Detailed scrutiny of your project viability and MSME credentials is underway by {final_partner_name or 'nodal committee'}."
                priority = "medium"
            elif to_status == PartnerRoutingStatus.DOCUMENTS_REQUIRED.value:
                notif_title = f"Action Required: Documents Requested for {scheme_name}"
                notif_body = f"Channel partner {final_partner_name or 'officer'} requested additional compliance documents: {clean_reason}. Please upload them to proceed."
                priority = "high"
            elif to_status == PartnerRoutingStatus.APPROVED.value:
                notif_title = f"Sanction Approved: {scheme_name}"
                notif_body = f"Your application for {scheme_name} has been approved by {final_partner_name or 'nodal committee'}: {clean_reason}."
                priority = "high"
            elif to_status == PartnerRoutingStatus.REJECTED.value:
                notif_title = f"Application Update: {scheme_name}"
                notif_body = f"Your application for {scheme_name} was not approved by {final_partner_name or 'channel partner'}. Reason: {clean_reason}."
                priority = "high"
            elif to_status == PartnerRoutingStatus.DISBURSED.value:
                notif_title = f"Subsidy Disbursed: {scheme_name}"
                notif_body = f"Disbursement completed for {scheme_name}. Funds credited via DBT gateway: {clean_reason}."
                priority = "high"
            else:
                notif_title = f"Application Routing Update: {to_status}"
                notif_body = f"Status updated to '{to_status}' for partner {final_partner_name or 'institution'}: {clean_reason}."
                priority = "medium"

            notif.create_notification(
                user_id=application.user_id,
                notif_type="application_status",
                title=notif_title,
                body=notif_body,
                priority=priority,
                action_url="/applications",
                metadata={
                    "application_id": str(application.id),
                    "routing_status": to_status,
                    "reason": clean_reason,
                    "partner_name": final_partner_name
                }
            )
        except Exception as e:
            logger.warning("Failed to emit notification on status update: %s", e)

        return {
            "application_id": str(application.id),
            "from_status": current_status,
            "current_routing_status": to_status,
            "partner_acknowledgement_status": ack_status,
            "assigned_partner_id": str(final_partner_id) if final_partner_id else None,
            "assigned_partner_name": final_partner_name,
            "updated_at": now_iso,
            "reason": reason.strip(),
            "actor": actor_identifier,
            "actor_role": actor.role,
            "allowed_next_transitions": ALLOWED_ROUTING_TRANSITIONS.get(to_status, []),
            "history_count": len(history)
        }

    def get_routing_history(self, application: Application) -> List[Dict[str, Any]]:
        """Retrieve audit history entries for routing status changes."""
        form_data = application.form_data or {}
        history = list(form_data.get("routing_history", []))
        if not history:
            curr = self.get_current_routing_status(application)
            partner_routing = form_data.get("partner_routing", {})
            created_ts = (
                application.created_at.isoformat()
                if isinstance(application.created_at, datetime)
                else (str(application.created_at) if application.created_at else datetime.now(timezone.utc).isoformat())
            )
            history.append({
                "from_status": None,
                "to_status": curr,
                "timestamp": created_ts,
                "partner_id": partner_routing.get("assigned_partner_id"),
                "partner_name": partner_routing.get("assigned_partner_name"),
                "reason": "Application initiated in platform.",
                "actor": "system",
                "actor_role": "system",
                "source": "yojantra_core"
            })
        return history

    def get_routing_status_summary(self, application: Application) -> Dict[str, Any]:
        """Return comprehensive status and audit payload matching ApplicationRoutingStatusResponse."""
        curr = self.get_current_routing_status(application)
        ack = self.get_partner_acknowledgement_status(application)
        form_data = application.form_data or {}
        partner_routing = form_data.get("partner_routing", {})
        
        # Format history items for schema
        raw_history = self.get_routing_history(application)
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

            history_entries.append({
                "from_status": h.get("from_status"),
                "to_status": h.get("to_status") or curr,
                "timestamp": parsed_ts,
                "partner_id": h.get("partner_id"),
                "partner_name": h.get("partner_name"),
                "reason": h.get("reason", ""),
                "actor": h.get("actor", "system"),
                "actor_role": h.get("actor_role", "system"),
                "source": h.get("source", "system")
            })

        updated_ts = partner_routing.get("routing_status_updated_at")
        if isinstance(updated_ts, str):
            try:
                dt_updated = datetime.fromisoformat(updated_ts)
            except Exception:
                dt_updated = application.updated_at or application.created_at
        elif isinstance(updated_ts, datetime):
            dt_updated = updated_ts
        else:
            dt_updated = application.updated_at or application.created_at

        return {
            "application_id": application.id,
            "current_routing_status": curr,
            "partner_acknowledgement_status": ack,
            "assigned_partner_id": partner_routing.get("assigned_partner_id"),
            "assigned_partner_name": partner_routing.get("assigned_partner_name"),
            "assigned_partner_type": partner_routing.get("assigned_partner_type"),
            "partner_reference_code": form_data.get("partner_reference_code"),
            "allowed_next_transitions": self.get_allowed_next_transitions(application),
            "history": history_entries,
            "updated_at": dt_updated
        }

    def record_initial_routing_status(
        self,
        application: Application,
        actor: User,
        partner_id: Optional[UUID] = None,
        partner_name: Optional[str] = None
    ) -> None:
        """Initialize routing status and starting audit record on newly drafted application."""
        initial_status = (
            PartnerRoutingStatus.PARTNER_ASSIGNED.value
            if partner_id or partner_name
            else PartnerRoutingStatus.NOT_ROUTED.value
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        actor_identifier = actor.email or actor.phone or str(actor.id)
        
        form_data = dict(application.form_data or {})
        partner_routing = dict(form_data.get("partner_routing", {}))
        
        partner_routing["routing_status"] = initial_status
        partner_routing["partner_acknowledgement_status"] = PartnerAcknowledgementStatus.NOT_ROUTED.value
        partner_routing["routing_status_updated_at"] = now_iso
        partner_routing["last_routing_reason"] = "Initial application dossier created."
        if partner_id:
            partner_routing["assigned_partner_id"] = str(partner_id)
        if partner_name:
            partner_routing["assigned_partner_name"] = partner_name
            
        form_data["partner_routing"] = partner_routing
        
        history = list(form_data.get("routing_history", []))
        history.append({
            "from_status": None,
            "to_status": initial_status,
            "timestamp": now_iso,
            "partner_id": str(partner_id) if partner_id else None,
            "partner_name": partner_name,
            "reason": "Application draft created and initial channel partner assigned." if partner_name else "Application draft created. Awaiting channel partner assignment.",
            "actor": actor_identifier,
            "actor_role": actor.role,
            "source": "portal"
        })
        form_data["routing_history"] = history
        application.form_data = form_data

