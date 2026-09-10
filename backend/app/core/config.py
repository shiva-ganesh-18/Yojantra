import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_root_dir = os.path.dirname(_base_dir)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Yojantra"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,https://schemematch-ai-complete.vercel.app"

    # Firebase Admin
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    FIREBASE_APP_CHECK_ENFORCEMENT: bool = False
    FIREBASE_APP_CHECK_DEBUG_TOKEN: str = ""

    # Database
    DATABASE_URL: str = "postgresql://schemematch:schemematch@db:5432/schemematch"
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "schemematch"
    REDIS_URL: str = "redis://redis:6379/0"

    @model_validator(mode="after")
    def validate_production_secrets(self):
        is_prod = self.ENVIRONMENT.lower() in ("production", "prod") or (
            not self.DEBUG and self.ENVIRONMENT.lower() != "development"
        )
        if is_prod:
            insecure_keys = [
                "",
                "your-super-secret-key-change-in-production",
                "change-this-to-32-random-characters-long-key",
                "change-this-to-a-secure-random-32-character-secret",
                "your-super-secret-32-character-key",
                "super-secret-schemematch-dev-key-32chars",
                "secret",
            ]
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_keys or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, "
                    "SECRET_KEY must be provided via environment variables and be at least 32 characters long."
                )
            if "schemematch:schemematch" in self.DATABASE_URL:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, "
                    "default database credentials 'schemematch:schemematch' are not permitted."
                )
            if self.NEO4J_PASSWORD == "schemematch":
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, "
                    "default NEO4J_PASSWORD 'schemematch' is not permitted."
                )
            if self.DEBUG:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: DEBUG mode cannot be enabled in production mode."
                )
            if self.ALLOW_DEV_OTP:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: ALLOW_DEV_OTP cannot be enabled in production mode."
                )
            # Production Google Sign-In must be backed by verified App Check
            # whenever Firebase Admin credentials are configured. Unconfigured
            # deployments keep graceful degradation (endpoints report unconfigured).
            cred_path = self.FIREBASE_CREDENTIALS_PATH or self.FIREBASE_SERVICE_ACCOUNT_PATH
            firebase_configured = bool(
                (self.FIREBASE_PROJECT_ID and self.FIREBASE_CLIENT_EMAIL and self.FIREBASE_PRIVATE_KEY)
                or (cred_path and os.path.isfile(cred_path))
            )
            if firebase_configured and not self.FIREBASE_APP_CHECK_ENFORCEMENT:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production mode with Firebase "
                    "Admin credentials configured, FIREBASE_APP_CHECK_ENFORCEMENT must be True."
                )
        else:
            if not self.SECRET_KEY:
                self.SECRET_KEY = "dev-local-development-secret-key-for-testing-only-32chars"
        return self

    # AI
    AI_PROVIDER: str = "auto"  # "auto", "gemini", "openai"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"  # Configurable OpenAI chat model; key is never logged or exposed
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "schemes"

    # External APIs & Official Government Integrations
    # 1. DigiLocker (MeitY)
    DIGILOCKER_CLIENT_ID: str = ""
    DIGILOCKER_CLIENT_SECRET: str = ""
    DIGILOCKER_REDIRECT_URI: str = "http://localhost:8001/api/integrations/digilocker/callback"
    DIGILOCKER_API_BASE_URL: str = "https://api.digitallocker.gov.in/public/oauth2/1"

    # 2. UIDAI / Aadhaar (Licensed AUA/KUA Gateway)
    AADHAAR_API_KEY: str = ""
    UIDAI_API_URL: str = ""
    UIDAI_LICENSE_KEY: str = ""
    UIDAI_AUA_CODE: str = ""
    UIDAI_SUB_AUA_CODE: str = ""
    UIDAI_CERT_PATH: str = ""

    # 3. Income Tax Department PAN Verification
    PAN_API_KEY: str = ""
    PAN_GATEWAY_URL: str = ""
    PAN_SERVICE_PROVIDER: str = "income_tax_dept"  # "income_tax_dept", "nsdl", "utiitsl"

    # 4. Ministry of MSME UDYAM Portal
    UDYAM_API_KEY: str = ""
    UDYAM_GATEWAY_URL: str = ""
    UDYAM_CLIENT_ID: str = ""

    # 5. National Scheme Gazette & Open DBT Sync
    GOV_SYNC_API_KEY: str = ""
    GOV_SYNC_ENDPOINT_URL: str = ""

    # 6. Core Banking System (CBS) & Channel Partner Live Gateway
    BANKING_GATEWAY_URL: str = ""
    BANKING_GATEWAY_API_KEY: str = ""
    BANKING_GATEWAY_AUTH_TYPE: str = "bearer"  # "bearer", "api_key", "mtls", "oauth2"
    BANKING_GATEWAY_TIMEOUT_SECONDS: float = 4.0
    BANKING_GATEWAY_CERT_PATH: str = ""
    BANKING_GATEWAY_KEY_PATH: str = ""
    BANKING_GATEWAY_CA_PATH: str = ""
    # Aliases for CBS naming convention
    CBS_GATEWAY_URL: str = ""
    CBS_API_KEY: str = ""
    CBS_AUTH_TYPE: str = "bearer"

    # 7. PFMS / DBT Integration & Inbound Webhooks
    PFMS_GATEWAY_URL: str = ""
    PFMS_API_KEY: str = ""
    PFMS_AUTH_TYPE: str = "bearer"  # "bearer", "api_key", "mtls"
    PFMS_TIMEOUT_SECONDS: float = 4.0
    PFMS_WEBHOOK_SECRET: str = ""
    BANKING_WEBHOOK_SECRET: str = ""
    INTEGRATIONS_WEBHOOK_MAX_AGE_SECONDS: int = 300

    # Twilio SMS / WhatsApp
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_API_KEY_SID: str = ""
    TWILIO_API_KEY_SECRET: str = ""
    TWILIO_PHONE: str = ""
    TWILIO_MESSAGING_SERVICE_SID: str = ""
    WHATSAPP_API_KEY: str = ""

    # Security
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    OTP_EXPIRE_MINUTES: int = 5  # 5 minutes expiration
    OTP_RESEND_COOLDOWN_SECONDS: int = 30  # 30-second resend cooldown
    MAX_OTP_ATTEMPTS: int = 5
    ALLOW_DEV_OTP: bool = False
    DEV_OTP_CODE: str = ""  # Empty by default; only allowed in non-production if explicitly configured

    # Features
    ENABLE_VOICE: bool = True
    ENABLE_WHATSAPP: bool = True
    ENABLE_IVR: bool = False
    OFFLINE_SYNC_INTERVAL_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(_root_dir, ".env"),
            os.path.join(_base_dir, ".env"),
            ".env"
        ),
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
