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
    """Mark notification as read."""
    service = get_notification_service(db)
    success = service.mark_as_read(notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}


@router.get("/unread-count")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count."""
    service = get_notification_service(db)
    count = len(service.get_user_notifications(user.id, unread_only=True))
    return {"unread_count": count}
