"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Voice Lab"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Authentication
    # IMPORTANT: Set to true ONLY for local development to skip auth
    disable_auth: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/voicelab"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_type: Literal["local", "s3", "gcs"] = "local"
    storage_path: str = "./storage"
    s3_bucket: str = ""
    s3_region: str = "ap-northeast-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Google Cloud
    google_application_credentials: str = ""
    gcp_project_id: str = ""

    # Azure Speech
    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"

    # ElevenLabs
    elevenlabs_api_key: str = ""

    # VoAI
    voai_api_key: str = ""
    voai_api_endpoint: str = ""

    # LLM Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # OAuth Domain Restriction
    # Comma-separated list of allowed email domains for Google OAuth login
    # e.g., "heyuai.com.tw,example.com"
    # Empty string or "*" means allow all domains
    allowed_domains: list[str] = []

    # Google OAuth
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def parse_allowed_domains(cls, v):
        """Parse allowed domains from string or list."""
        if isinstance(v, str):
            if not v or v == "*":
                return []
            return [domain.strip().lower() for domain in v.split(",") if domain.strip()]
        return [d.lower() for d in v] if v else []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
