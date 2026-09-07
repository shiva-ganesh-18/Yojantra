import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_root_dir = os.path.dirname(_base_dir)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SchemeMatch AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-super-secret-key-change-in-production"

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
        return self

    # AI
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "schemes"

    # External APIs
    DIGILOCKER_CLIENT_ID: str = ""
    DIGILOCKER_CLIENT_SECRET: str = ""
    UDYAM_API_KEY: str = ""
    AADHAAR_API_KEY: str = ""

    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE: str = ""
    WHATSAPP_API_KEY: str = ""

    # Security
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    OTP_EXPIRE_MINUTES: int = 10
    MAX_OTP_ATTEMPTS: int = 5
    ALLOW_DEV_OTP: bool = False
    DEV_OTP_CODE: str = "123456"

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
