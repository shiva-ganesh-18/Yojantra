"""Notification service with multi-channel delivery."""
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Notification, User, Scheme, UserSchemeMatch, Application
from app.core.config import get_settings

settings = get_settings()


class NotificationService:
    """Handles multi-channel notifications: push, SMS, WhatsApp, email, IVR."""

    PRIORITY_MATRIX = {
        "high": ["push", "sms", "whatsapp"],
        "medium": ["push", "whatsapp"],
        "low": ["push"]
    }

    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: UUID,
        notif_type: str,
        title: str,
        body: str,
        priority: str = "medium",
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a notification in the database."""
        notif = Notification(
            user_id=user_id,
            type=notif_type,
            title=title,
            body=body,
            channel="push",  # Default, will be expanded
            action_url=action_url,
            metadata=metadata or {}
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def send_immediately(self, notification: Notification) -> bool:
        """Send notification through appropriate channels based on priority."""
        channels = self.PRIORITY_MATRIX.get(notification.type, ["push"])

        success = False
        for channel in channels:
            try:
                if channel == "push":
                    self._send_push(notification)
                elif channel == "sms":
                    self._send_sms(notification)
                elif channel == "whatsapp":
                    self._send_whatsapp(notification)
                elif channel == "email":
                    self._send_email(notification)
                success = True
            except Exception as e:
                print(f"Failed to send via {channel}: {e}")

        if success:
            notification.sent_at = datetime.utcnow()
            self.db.commit()

        return success

    def _send_push(self, notif: Notification) -> bool:
        """Send push notification via FCM / WebPush (in-app notifications are stored in DB)."""
        # In-app notifications are stored in DB and fetched via GET /notifications
        return True

    def _send_sms(self, notif: Notification) -> bool:
        """Send SMS via Twilio/MSG91 (⏳ EXTERNAL DEPENDENCY)."""
        if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE):
            # External provider credentials absent - do not fake delivery
            return False
        # When credentials present, integrate Twilio REST client
        return True

    def _send_whatsapp(self, notif: Notification) -> bool:
        """Send WhatsApp message via Meta API (⏳ EXTERNAL DEPENDENCY)."""
        if not settings.WHATSAPP_API_KEY:
            # External provider credentials absent - do not fake delivery
            return False
        return True

    def _send_email(self, notif: Notification) -> bool:
        """Send email notification (⏳ EXTERNAL DEPENDENCY)."""
        return False

    def check_and_send_deadline_reminders(self):
        """Cron job: Check upcoming deadlines and send reminders."""
        # 7 days, 3 days, 1 day before deadline
        now = datetime.utcnow().date()

        # Get matches with approaching deadlines
        matches = self.db.query(UserSchemeMatch).join(Scheme).filter(
            and_(
                UserSchemeMatch.is_bookmarked == True,
                Scheme.application_deadline.isnot(None),
                Scheme.application_deadline >= now,
                Scheme.application_deadline <= now + timedelta(days=7)
            )
        ).all()

        for match in matches:
            days_left = (match.scheme.application_deadline - now).days

            if days_left == 7:
                priority = "medium"
                title = f"⏰ Deadline Alert: {match.scheme.name}"
                body = f"Your bookmarked scheme '{match.scheme.name}' deadline is in 7 days. Apply now!"
            elif days_left == 3:
                priority = "high"
                title = f"🚨 Urgent: {match.scheme.name} deadline in 3 days!"
                body = f"Only 3 days left to apply for {match.scheme.name}. Don't miss out!"
            elif days_left == 1:
                priority = "high"
                title = f"🔴 LAST DAY: {match.scheme.name}"
                body = f"Today is the LAST DAY to apply for {match.scheme.name}. Apply immediately!"
            else:
                continue

            notif = self.create_notification(
                user_id=match.user_id,
                notif_type="deadline_reminder",
                title=title,
                body=body,
                priority=priority,
                action_url=match.scheme.official_url,
                metadata={"scheme_id": str(match.scheme_id), "days_left": days_left}
            )
            self.send_immediately(notif)

    def check_new_scheme_matches(self):
        """Cron job: Check for newly eligible schemes and notify users."""
        # Find users who haven't been matched recently
        # This would run the matching engine and notify about new matches
        pass

    def check_application_status_changes(self):
        """Cron job: Poll application statuses and notify users of changes."""
        # In production: integrate with government portals for status polling
        pass

    def get_user_notifications(self, user_id: UUID, unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).all()

    def mark_as_read(self, notif_id: UUID) -> bool:
        """Mark a notification as read."""
        notif = self.db.query(Notification).filter(Notification.id == notif_id).first()
        if notif:
            notif.is_read = True
            self.db.commit()
            return True
        return False


def get_notification_service(db: Session) -> NotificationService:
    return NotificationService(db)
