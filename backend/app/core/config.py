"""
Configuration management using Pydantic Settings.
Loads configuration from .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


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

    # ===== ACTION LOGGING =====
    ACTION_LOGGING_ENABLED: bool = True  # Enable/disable action logging for workflow monitoring
    ACTION_LOG_LEVEL: str = "INFO"  # INFO | DEBUG | WARNING

    class Config:
        env_file = ".env"
        case_sensitive = True

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
