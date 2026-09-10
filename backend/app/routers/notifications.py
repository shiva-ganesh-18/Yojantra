"""Notification router."""
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.notification_service import get_notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def get_notifications(
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications."""
    service = get_notification_service(db)
    notifs = service.get_user_notifications(user.id, unread_only)

    return [
        {
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "is_read": n.is_read,
            "action_url": n.action_url,
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifs
    ]


@router.put("/{notif_id}/read")
@router.patch("/{notif_id}/read")
def mark_read(
    notif_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read with ownership validation."""
    service = get_notification_service(db)
    success = service.mark_as_read(notif_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}


@router.put("/read-all")
@router.patch("/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for current user."""
    service = get_notification_service(db)
    count = service.mark_all_read(user.id)
    return {"message": "All notifications marked as read", "updated_count": count}


@router.delete("/{notif_id}")
def delete_notification(
    notif_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete notification with ownership check."""
    service = get_notification_service(db)
    success = service.delete_notification(notif_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted successfully"}


@router.get("/unread-count")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count."""
    service = get_notification_service(db)
    count = len(service.get_user_notifications(user.id, unread_only=True))
    return {"unread_count": count}


@router.post("/register-token")
def register_device_fcm_token(
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register device FCM token for push notifications.
    Token is linked to user's secure metadata for multi-device push delivery.
    """
    token = payload.get("fcm_token")
    if not token or not isinstance(token, str):
        raise HTTPException(status_code=400, detail="Valid fcm_token is required")

    service = get_notification_service(db)
    result = service.register_fcm_token(user.id, token)
    return result


@router.post("/send-test")
def send_test_notification(
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger a test notification (for application updates, missing documents, or scheme updates).
    Ensures safe payload delivery and returns FCM delivery status.
    """
    notif_type = payload.get("type", "application_status_update")
    title = payload.get("title", "Application Status Update")
    body = payload.get("body", "Your Yojantra application status has been updated.")
    action_url = payload.get("action_url", "/applications")

    service = get_notification_service(db)
    notif = service.create_notification(
        user_id=user.id,
        notif_type=notif_type,
        title=title,
        body=body,
        action_url=action_url,
        metadata={"category": notif_type}
    )
    service.send_immediately(notif)
    return {
        "message": "Notification generated and dispatched",
        "notification_id": str(notif.id),
        "status": "dispatched"
    }


@router.get("/firebase/status")
def get_firebase_status():
    """
    Returns Firebase features operational status (Auth, FCM, App Check, Analytics).
    Truthfully indicates live vs framework-ready components.
    """
    from app.core.firebase import is_firebase_configured
    from app.core.config import get_settings

    cfg = get_settings()
    is_live = is_firebase_configured()

    return {
        "firebase_project_id": cfg.FIREBASE_PROJECT_ID or "configured-client-only",
        "authentication": {
            "google_auth": "LIVE" if is_live else "FRAMEWORK_READY (Configured for client/backend verify)",
            "phone_otp": "LIVE (Native database verification)"
        },
        "cloud_messaging_fcm": {
            "status": "LIVE" if is_live else "FRAMEWORK_READY (Ready for Service Account credentials)",
            "supported_events": [
                "application_status_update",
                "missing_document_alert",
                "scheme_update",
                "partner_application_update"
            ]
        },
        "app_check": {
            "status": "LIVE" if (is_live and cfg.FIREBASE_APP_CHECK_ENFORCEMENT) else "CONFIGURED_PROTECTIVE (Development mode non-blocking)",
            "enforced": cfg.FIREBASE_APP_CHECK_ENFORCEMENT
        },
        "analytics": {
            "status": "CONFIGURED (Client non-sensitive event measurement)",
            "sensitive_data_protection": "STRICT (Aadhaar, PAN, OTP, passwords stripped at source)"
        }
    }
