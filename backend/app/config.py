"""Application configuration via environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """App-wide settings loaded from environment variables."""

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leadgen"
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- LLM ---
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # --- Data Collection API Keys ---
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    github_token: Optional[str] = None
    crunchbase_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    clearbit_api_key: Optional[str] = None
    apollo_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None

    # --- Social Media ---
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None

    # --- Email ---
    resend_api_key: Optional[str] = None

    # --- Security ---
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- App ---
    log_level: str = "INFO"
    cors_origins: str = "*"
    environment: str = "development"

    # --- Rate Limiting ---
    rate_limit_enabled: bool = True
    rate_limit_default_per_minute: int = 60

    # --- Proxy ---
    proxy_list: Optional[str] = None  # Comma-separated proxy URLs
    proxy_rotation_enabled: bool = True

    # --- Collection Defaults ---
    max_leads_per_source: int = 100
    request_timeout_seconds: int = 30

    @property
    def cors_origin_list(self) -> List[str]:
        origins = self.cors_origins
        if origins == "*":
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


settings = Settings()