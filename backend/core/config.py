"""
core/config.py

Application configuration loaded from environment variables.

Responsibilities:
- Central source of truth for all runtime configuration.
- Validated at startup via Pydantic BaseSettings; missing required vars fail fast.
- Consumed by infrastructure (DB engine, security) and application code.
- Never imported by the domain layer.

Usage:
    from core.config import settings
    settings.database_url
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    secret_key: str = ""
    debug: bool = False

    # Database
    database_url: str = ""  # postgresql+asyncpg://...
    database_echo: bool = False  # Log SQL — development only


    # JWT
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # CORS
    allowed_origins: list[str] | str = ["http://localhost:5173"]

    # Storage
    storage_backend: str = "local"
    storage_local_root: str = "./storage/uploads"

    # Mail Dispatcher
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_use_tls: bool = True
    mail_username: str | None = None
    mail_password: str | None = None
    mail_default_sender: str = "noreply@clinora.com"
    mail_enabled: bool = False

    # Google OAuth 2.0
    google_client_id: str | None = None
    google_client_secret: str | None = None
    frontend_url: str = "http://localhost:5173"

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def validate_allowed_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed]
            except Exception:
                pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance. Cached after first call."""
    return Settings()


# Module-level convenience reference — use `settings` in most cases.
# Call `get_settings()` when you need the lru_cache reference (e.g. in tests
# that override environment variables and need cache invalidation).
settings = get_settings()
