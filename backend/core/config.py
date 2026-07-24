"""
Application configuration loaded from environment variables via pydantic-settings.
Secrets are NEVER hardcoded — they must come from .env or OS env vars.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM Provider Configuration ───────────────────────────
    # Options: "ollama" (or "local"), "bedrock", "anthropic"
    llm_provider: str = "ollama"

    # ── Local / Self-Hosted LLM (Ollama, vLLM, LM Studio) ────
    # No API key required for local Ollama or private vLLM on AWS EC2
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "qwen2.5:0.5b"


    # ── AWS Bedrock (Uses AWS IAM Roles — No third-party API key) ──
    aws_region: str = "us-east-1"
    aws_bedrock_model_id: str = "meta.llama3-8b-instruct-v1:0"

    # ── Anthropic & Cloud API Keys (Optional for Cloud Deployments) ──
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""


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

