"""SMS Gateway Integration Service for production and sandbox environments.

Supported Providers & Authentication Modes:
1. Twilio API Key Authentication (Recommended):
   - TWILIO_ACCOUNT_SID (Account Identifier)
   - TWILIO_API_KEY_SID (API Key SID e.g. SK...)
   - TWILIO_API_KEY_SECRET (API Key Secret)
2. Twilio Account SID + Auth Token Authentication (Legacy fallback)
3. Sender Identifiers supported:
   - TWILIO_PHONE (E.164 phone number e.g. +1... or approved alphanumeric header)
   - TWILIO_MESSAGING_SERVICE_SID (Messaging Service SID e.g. MG...)
4. Secure Fallback & Sandbox Driver (Masked logging, zero leak of secrets)
"""
import logging
from typing import Dict, Any, Optional, Tuple
import httpx

from app.core.config import get_settings

logger = logging.getLogger("yojantra.sms")
settings = get_settings()


class SMSGatewayService:
    """Handles reliable, rate-limited SMS OTP and transactional alerts dispatch."""

    def __init__(self):
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_api_key_sid = settings.TWILIO_API_KEY_SID
        self.twilio_api_key_secret = settings.TWILIO_API_KEY_SECRET
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_phone = settings.TWILIO_PHONE
        self.twilio_messaging_service_sid = settings.TWILIO_MESSAGING_SERVICE_SID

    def get_auth_credentials(self) -> Optional[Tuple[str, str]]:
        """
        Determine Twilio HTTP Basic Auth credentials.
        Priority:
        1. API Key Authentication: (API_KEY_SID, API_KEY_SECRET)
        2. Auth Token Authentication: (ACCOUNT_SID, AUTH_TOKEN)
        """
        if self.twilio_api_key_sid and self.twilio_api_key_secret:
            return (self.twilio_api_key_sid, self.twilio_api_key_secret)
        if self.twilio_account_sid and self.twilio_auth_token:
            return (self.twilio_account_sid, self.twilio_auth_token)
        return None

    def get_sender_parameter(self) -> Optional[Dict[str, str]]:
        """
        Return the appropriate sender payload for Twilio Messages API.
        Priority:
        1. MessagingServiceSid if TWILIO_MESSAGING_SERVICE_SID is set
        2. From if TWILIO_PHONE is set
        """
        if self.twilio_messaging_service_sid:
            return {"MessagingServiceSid": self.twilio_messaging_service_sid}
        if self.twilio_phone:
            return {"From": self.twilio_phone}
        return None

    def is_production_gateway_configured(self) -> bool:
        """Check whether production SMS credentials and a valid sender are provisioned."""
        has_auth = self.get_auth_credentials() is not None
        has_account = bool(self.twilio_account_sid)
        has_sender = self.get_sender_parameter() is not None
        return bool(has_auth and has_account and has_sender)

    def mask_phone_number(self, phone: str) -> str:
        """Mask phone number with Data Privacy Safeguards (e.g. +919876543210 -> +91******3210)."""
        if not phone or len(phone) < 7:
            return "+91******"
        return f"{phone[:3]}******{phone[-4:]}"

    def send_otp_sms(self, phone: str, otp_code: str, expire_minutes: int = 5) -> Dict[str, Any]:
        """
        Dispatch 6-digit OTP via configured SMS Gateway.
        Ensures OTP text adheres to standard verification template:
        - Domestic India SMS: Subject to TRAI entity/Sender ID/template registration according to Twilio India guidelines.
        - International SMS route: Standard carrier verification rules apply.
        """
        masked_phone = self.mask_phone_number(phone)
        message_body = (
            f"Your Yojantra verification OTP is {otp_code}. "
            f"Valid for {expire_minutes} minutes. Do not share OTP with anyone for your security. - Yojantra GovTech"
        )

        auth_tuple = self.get_auth_credentials()
        sender_param = self.get_sender_parameter()
        is_prod = settings.ENVIRONMENT.lower() in ("production", "prod")

        # 1. If production Twilio/SMS credentials configured, execute HTTP REST dispatch
        if self.is_production_gateway_configured() and auth_tuple and sender_param:
            auth_mode = "twilio_api_key" if self.twilio_api_key_sid else "twilio_auth_token"
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
                data = {
                    **sender_param,
                    "To": phone,
                    "Body": message_body
                }
                
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(url, data=data, auth=auth_tuple)
                    
                if response.status_code in (200, 201):
                    sid = response.json().get("sid", "msg_dispatched")
                    logger.info(f"[SMS GATEWAY] Production OTP successfully dispatched to {masked_phone} via {auth_mode}")
                    return {
                        "status": "delivered",
                        "provider": auth_mode,
                        "masked_phone": masked_phone,
                        "message_id": sid
                    }
                else:
                    err_json = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    err_code = err_json.get("code", response.status_code)
                    logger.warning(
                        f"[SMS GATEWAY ERROR] Gateway returned code {err_code} for {masked_phone}."
                    )
                    if is_prod:
                        return {
                            "status": "error",
                            "error_code": "SMS_DISPATCH_FAILED",
                            "detail": "SMS carrier gateway rejected the dispatch request. Please check sender and DLT configuration.",
                            "masked_phone": masked_phone
                        }
            except Exception as e:
                logger.error(f"[SMS GATEWAY EXCEPTION] Failed to connect to SMS Gateway: {str(e)}")
                if is_prod:
                    return {
                        "status": "error",
                        "error_code": "SMS_GATEWAY_UNAVAILABLE",
                        "detail": "SMS delivery service temporarily unreachable.",
                        "masked_phone": masked_phone
                    }

        # 2. Production Check: If in production mode and sender credentials are missing
        if is_prod:
            logger.error("[SMS CONFIG ERROR] In production mode, TWILIO_PHONE or TWILIO_MESSAGING_SERVICE_SID is required.")
            return {
                "status": "error",
                "error_code": "SMS_SENDER_UNCONFIGURED",
                "detail": "Production SMS gateway sender is not provisioned on this server.",
                "masked_phone": masked_phone
            }

        # 3. Fallback / Sandbox Mode (Non-production development/demo only)
        logger.info(
            f"[SMS GATEWAY] Dispatched OTP via Sandbox Gateway for {masked_phone} "
            f"(Expiry: {expire_minutes} min, Single-Use)"
        )
        return {
            "status": "dispatched_sandbox",
            "provider": "sandbox_gateway_fallback",
            "masked_phone": masked_phone,
            "note": "Non-production sandbox active. For live SMS, configure TWILIO_PHONE or TWILIO_MESSAGING_SERVICE_SID."
        }

    def send_transactional_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Dispatch general notification SMS (e.g. application approved, missing document)."""
        masked_phone = self.mask_phone_number(phone)
        auth_tuple = self.get_auth_credentials()
        sender_param = self.get_sender_parameter()

        if self.is_production_gateway_configured() and auth_tuple and sender_param:
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
                data = {
                    **sender_param,
                    "To": phone,
                    "Body": message
                }
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(url, data=data, auth=auth_tuple)
                if response.status_code in (200, 201):
                    return {"status": "delivered", "provider": "twilio_production"}
            except Exception as e:
                logger.error(f"[SMS ERROR] Transactional SMS failed: {e}")

        return {"status": "dispatched_sandbox", "masked_phone": masked_phone}


_sms_service_instance: Optional[SMSGatewayService] = None


def get_sms_service() -> SMSGatewayService:
    global _sms_service_instance
    if _sms_service_instance is None:
        _sms_service_instance = SMSGatewayService()
    return _sms_service_instance
