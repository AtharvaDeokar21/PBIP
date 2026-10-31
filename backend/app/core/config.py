import secrets
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PBIP API"
    app_env: str = "development"
    # Ignore generic DEBUG variables exported by developer tooling.
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    api_v1_prefix: str = "/api/v1"

    # Credentials are never hard-coded: set DATABASE_URL and JWT_SECRET_KEY in .env.
    database_url: str = "postgresql+asyncpg://localhost:5432/postgres"

    # Without JWT_SECRET_KEY a random per-process secret is used, so tokens are
    # only valid for that process; every deployment must set the variable.
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Customer banking limits (INR)
    max_single_transfer_amount: float = 500_000
    daily_transfer_limit: float = 1_000_000
    max_page_size: int = 100

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
