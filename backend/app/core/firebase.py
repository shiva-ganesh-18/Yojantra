"""Firebase Admin SDK integration module for Yojantra.
Handles verification of Google Firebase ID tokens securely on the server.
"""
import os
import json
from typing import Optional, Dict, Any
from app.core.config import get_settings

settings = get_settings()

_firebase_app = None
_is_configured = False
_init_attempted = False


class FirebaseNotConfiguredError(Exception):
    """Raised when Firebase credentials are not configured on the backend."""
    pass


class InvalidFirebaseTokenError(Exception):
    """Raised when the Firebase ID token is invalid, expired, or malformed."""
    pass


def init_firebase_admin(force: bool = False):
    """Safely initialize Firebase Admin SDK if credentials are present."""
    global _firebase_app, _is_configured, _init_attempted

    if _init_attempted and not force:
        return _firebase_app

    _init_attempted = True

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Check if already initialized in current process
        if firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            _is_configured = True
            return _firebase_app

        cred = None

        # 1. Check direct service account path
        cred_path = (
            getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
            or getattr(settings, "FIREBASE_SERVICE_ACCOUNT_PATH", None)
            or os.getenv("FIREBASE_CREDENTIALS_PATH")
            or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        )
        if cred_path and os.path.isfile(cred_path):
            cred = credentials.Certificate(cred_path)

        # 2. Check individual environment variables
        elif (
            getattr(settings, "FIREBASE_PROJECT_ID", None)
            and getattr(settings, "FIREBASE_CLIENT_EMAIL", None)
            and getattr(settings, "FIREBASE_PRIVATE_KEY", None)
        ):
            project_id = settings.FIREBASE_PROJECT_ID
            client_email = settings.FIREBASE_CLIENT_EMAIL
            private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")

            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token"
            })

        # 3. Check for GOOGLE_APPLICATION_CREDENTIALS standard env var
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.isfile(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
            cred = credentials.ApplicationDefault()

        if cred:
            _firebase_app = firebase_admin.initialize_app(cred)
            _is_configured = True
            print("[FIREBASE] Firebase Admin SDK initialized successfully.")
        else:
            _is_configured = False
            print("[FIREBASE] No Firebase Admin credentials found. Google authentication endpoints will indicate unconfigured.")

    except Exception as e:
        _is_configured = False
        print(f"[FIREBASE] Warning: Failed to initialize Firebase Admin SDK: {e}")

    return _firebase_app


def is_firebase_configured() -> bool:
    """Return True if Firebase Admin SDK is ready to verify tokens."""
    global _is_configured
    if _firebase_app is None:
        init_firebase_admin()
    return _is_configured


def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token sent from the frontend.
    Returns verified user payload: uid, email, email_verified, name, picture.
    Raises FirebaseNotConfiguredError or InvalidFirebaseTokenError.
    """
    if not is_firebase_configured():
        raise FirebaseNotConfiguredError(
            "Firebase Admin SDK is not configured on this server. "
            "Please configure FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and FIREBASE_PRIVATE_KEY."
        )

    if not id_token or not isinstance(id_token, str):
        raise InvalidFirebaseTokenError("Missing or invalid token format.")

    try:
        from firebase_admin import auth

        # clock_skew_seconds=10 accommodates standard minor clock skew (e.g. sub-second or few-second local clock drift) without disabling validation
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=10)
        uid = decoded_token.get("uid")
        if not uid:
            raise InvalidFirebaseTokenError("Token payload missing user identifier (UID).")

        return {
            "uid": uid,
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "name": decoded_token.get("name") or "",
            "picture": decoded_token.get("picture") or "",
            "auth_time": decoded_token.get("auth_time")
        }
    except Exception as e:
        raise InvalidFirebaseTokenError(f"Token verification failed: {str(e)}")


def verify_app_check_token(app_check_token: Optional[str]) -> Dict[str, Any]:
    """
    Verify Firebase App Check token sent in X-Firebase-AppCheck header.
    Returns decoded App Check token claims (e.g. app_id).
    If App Check is not enforced in config, allows requests gracefully.
    """
    if not settings.FIREBASE_APP_CHECK_ENFORCEMENT:
        return {"app_id": "development-unrestricted", "verified": True, "enforced": False}

    if not app_check_token:
        raise InvalidFirebaseTokenError("Missing required X-Firebase-AppCheck header.")

    if not is_firebase_configured():
        # Fallback in local/test environments if debug token is provided
        if settings.FIREBASE_APP_CHECK_DEBUG_TOKEN and app_check_token == settings.FIREBASE_APP_CHECK_DEBUG_TOKEN:
            return {"app_id": "debug-token-verified", "verified": True, "enforced": True}
        raise FirebaseNotConfiguredError("Firebase Admin SDK is required to verify App Check tokens.")

    try:
        from firebase_admin import app_check
        decoded_token = app_check.verify_token(app_check_token)
        return {
            "app_id": decoded_token.get("app_id"),
            "verified": True,
            "enforced": True
        }
    except Exception as e:
        raise InvalidFirebaseTokenError(f"App Check verification failed: {str(e)}")


def sanitize_fcm_data(data: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    Sanitize FCM data payload to ensure no sensitive citizen credentials
    (Aadhaar, PAN, OTP, passwords, full financials) are ever transmitted.
    All values in FCM data payload must be strings.
    """
    if not data:
        return {}

    FORBIDDEN_KEYS = {
        "aadhaar", "aadhaar_number", "pan", "pan_number", "otp", "password", 
        "pin", "secret", "bank_account", "cvv", "full_financial_data"
    }

    sanitized = {}
    for k, v in data.items():
        k_lower = str(k).lower()
        if any(bad in k_lower for bad in FORBIDDEN_KEYS):
            continue
        if v is not None:
            sanitized[str(k)] = str(v)
    return sanitized


def send_fcm_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    action_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a Firebase Cloud Messaging push notification to a device token.
    Ensures safe payload delivery and returns status summary.
    """
    if not fcm_token:
        return {"status": "skipped", "reason": "No FCM token provided"}

    if not is_firebase_configured():
        return {
            "status": "framework_ready",
            "message": "FCM is ready. Live dispatch requires FIREBASE_PROJECT_ID and Service Account credentials.",
            "token_masked": fcm_token[:6] + "..." if len(fcm_token) > 10 else "configured"
        }

    try:
        from firebase_admin import messaging

        clean_data = sanitize_fcm_data(data)
        if action_url:
            clean_data["action_url"] = str(action_url)

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=clean_data,
            token=fcm_token,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon="/pwa-192x192.png",
                    badge="/pwa-192x192.png"
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=action_url or "/"
                )
            )
        )

        response = messaging.send(message)
        return {"status": "delivered", "message_id": response}
    except Exception as e:
        return {"status": "error", "reason": str(e)}
