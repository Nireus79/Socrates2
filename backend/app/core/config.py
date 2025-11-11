"""
Configuration management using Pydantic Settings.
Loads configuration from .env file.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.
    All settings are required unless marked Optional.
    """

    # ===== DATABASE =====
    DATABASE_URL_AUTH: str
    DATABASE_URL_SPECS: str

    # ===== SECURITY =====
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ===== LLM API KEYS =====
    ANTHROPIC_API_KEY: str

    # ===== APPLICATION =====
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development | staging | production
    LOG_LEVEL: str = "INFO"  # DEBUG | INFO | WARNING | ERROR

    # ===== CORS =====
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ===== ACTION LOGGING =====
    ACTION_LOGGING_ENABLED: bool = True  # Enable/disable action logging for workflow monitoring
    ACTION_LOG_LEVEL: str = "INFO"  # INFO | DEBUG | WARNING

    # ===== SENTRY ERROR TRACKING =====
    SENTRY_DSN: Optional[str] = None  # Sentry error tracking DSN (leave blank to disable)
    APP_VERSION: str = "0.1.0"  # App version for error tracking
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 0-1: percentage of transactions to trace (10% default)
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 0-1: percentage of transactions to profile (10% default)

    # ===== STRIPE PAYMENT INTEGRATION =====
    STRIPE_SECRET_KEY: Optional[str] = None  # Stripe API secret key (leave blank to disable payments)
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None  # Stripe publishable key for frontend
    STRIPE_WEBHOOK_SECRET: Optional[str] = None  # Stripe webhook signing secret
    STRIPE_PRICE_PRO_MONTHLY: Optional[str] = None  # Stripe price ID for Pro tier
    STRIPE_PRICE_TEAM_MONTHLY: Optional[str] = None  # Stripe price ID for Team tier

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
