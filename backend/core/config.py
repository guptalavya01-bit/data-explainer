"""
Application configuration loaded from environment variables via pydantic-settings.
Secrets are NEVER hardcoded — they must come from .env or OS env vars.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Anthropic ────────────────────────────────────────────
    anthropic_api_key: str = ""

    # ── IBM Cloud Object Storage (optional) ──────────────────
    cos_endpoint: str = ""
    cos_api_key_id: str = ""
    cos_instance_crn: str = ""
    cos_bucket_name: str = ""

    # ── App ──────────────────────────────────────────────────
    max_file_size_mb: int = 10
    allowed_origins: str = "http://localhost:5173,http://localhost:8000"
    port: int = 8000

    # ── Helpers ──────────────────────────────────────────────
    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
