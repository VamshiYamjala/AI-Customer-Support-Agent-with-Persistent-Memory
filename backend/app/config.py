"""
backend/app/config.py
Configuration module using pydantic-settings.
Loads environment variables from .env, validates required secrets, and masks credentials in string representation.
"""

from typing import Any, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _mask_value(v: Optional[str]) -> str:
    if not v:
        return "<EMPTY>"
    if len(v) <= 8:
        return "********"
    return f"********{v[-4:]}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Hindsight Configuration
    HINDSIGHT_BASE_URL: str = Field(
        default="https://api.hindsight.vectorize.io",
        description="Base URL for Hindsight Cloud API",
    )
    HINDSIGHT_API_KEY: str = Field(
        ...,
        description="API Key for Hindsight Cloud",
    )
    HINDSIGHT_BANK_PREFIX: str = Field(
        default="cs-",
        description="Prefix for customer-specific memory banks",
    )
    HINDSIGHT_SHARED_KB_BANK: str = Field(
        default="support-kb",
        description="Shared company knowledge base bank ID",
    )

    # LLM (Groq) Configuration
    GROQ_API_KEY: str = Field(
        ...,
        description="API Key for Groq Cloud LLM",
    )
    GROQ_MODEL: str = Field(
        default="openai/gpt-oss-20b",
        description="Model name to use on Groq",
    )

    # Application Security & Database
    SESSION_SECRET: str = Field(
        ...,
        description="Secret key for signing customer session tokens",
    )
    DATABASE_URL: str = Field(
        default="sqlite:///./data/app.db",
        description="SQLite database path",
    )
    APP_ENV: str = Field(
        default="development",
        description="Application environment (development / production)",
    )
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:8000",
        description="Comma-separated allowed CORS origins",
    )

    @field_validator("HINDSIGHT_BASE_URL", mode="before")
    @classmethod
    def sanitize_base_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().strip("'\"").rstrip("/")
        return v

    @field_validator("HINDSIGHT_API_KEY", "GROQ_API_KEY", "SESSION_SECRET", mode="before")
    @classmethod
    def sanitize_credentials(cls, v: Any) -> Any:
        if isinstance(v, str):
            cleaned = v.strip().strip("'\"").strip()
            if cleaned.startswith("Bearer "):
                cleaned = cleaned[7:].strip()
            return cleaned
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def __repr__(self) -> str:
        return (
            f"Settings("
            f"APP_ENV='{self.APP_ENV}', "
            f"HINDSIGHT_BASE_URL='{self.HINDSIGHT_BASE_URL}', "
            f"HINDSIGHT_API_KEY='{_mask_value(self.HINDSIGHT_API_KEY)}', "
            f"HINDSIGHT_BANK_PREFIX='{self.HINDSIGHT_BANK_PREFIX}', "
            f"HINDSIGHT_SHARED_KB_BANK='{self.HINDSIGHT_SHARED_KB_BANK}', "
            f"GROQ_API_KEY='{_mask_value(self.GROQ_API_KEY)}', "
            f"GROQ_MODEL='{self.GROQ_MODEL}', "
            f"SESSION_SECRET='{_mask_value(self.SESSION_SECRET)}', "
            f"DATABASE_URL='{self.DATABASE_URL}'"
            f")"
        )

    def __str__(self) -> str:
        return self.__repr__()


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Returns the cached Settings singleton or initializes it.
    Fails fast with readable error if required variables are missing.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
