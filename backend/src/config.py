"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
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
    cors_origins_str: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="cors_origins",
    )

    # OAuth Domain Restriction
    # Comma-separated list of allowed email domains for Google OAuth login
    # e.g., "heyuai.com.tw,example.com"
    # Empty string or "*" means allow all domains
    allowed_domains_str: str = Field(default="", alias="allowed_domains")

    # Google OAuth
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    # ==========================================================================
    # V2V Performance Feature Toggles
    # ==========================================================================
    # These toggles allow A/B testing of performance optimizations
    # Set via environment variables: V2V_LIGHTWEIGHT_MODE=true, etc.

    # Lightweight mode: skip sync audio storage for lower latency
    # Trade-off: Audio not saved in real-time, need batch upload after session
    v2v_lightweight_mode: bool = True

    # WebSocket compression: reduce bandwidth but add CPU overhead
    # Trade-off: Lower bandwidth vs higher CPU usage
    v2v_ws_compression: bool = False

    # Batch audio upload: buffer audio and upload after session ends
    # Trade-off: No real-time audio backup vs lower latency
    v2v_batch_audio_upload: bool = True

    # Skip latency tracking: disable detailed metrics collection
    # Trade-off: No latency metrics vs lower overhead
    v2v_skip_latency_tracking: bool = False

    # Gemini model configuration
    # Options: gemini-2.5-flash-native-audio-preview-12-2025 (Chinese), gemini-2.0-flash-exp (English only)
    gemini_live_model: str = "gemini-2.5-flash-native-audio-preview-12-2025"

    # Google AI API Key (for Gemini)
    google_ai_api_key: str = ""

    # Gemini TTS configuration
    # Model options: gemini-2.5-pro-preview-tts (high quality), gemini-2.5-flash-preview-tts (low latency)
    gemini_tts_model: str = "gemini-2.5-pro-preview-tts"
    gemini_tts_default_voice: str = "Kore"

    # ==========================================================================
    # Mureka AI Music Generation (Feature 012)
    # ==========================================================================
    mureka_api_key: str = ""
    mureka_api_base_url: str = "https://api.mureka.ai"

    # Music Generation Quota Configuration
    music_daily_limit_per_user: int = 10
    music_monthly_limit_per_user: int = 100
    music_max_concurrent_jobs: int = 3

    @property
    def allowed_domains(self) -> list[str]:
        """Parse allowed domains from comma-separated string."""
        v = self.allowed_domains_str
        if not v or v == "*":
            return []
        return [domain.strip().lower() for domain in v.split(",") if domain.strip()]

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
