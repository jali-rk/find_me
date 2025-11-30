"""
Application configuration using pydantic-settings.
Loads settings from environment variables with defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Storage
    data_dir: Path = Field(default=Path("./data"), description="Root directory for event data")

    # Face detection and matching
    face_model_name: str = Field(default="buffalo_l", description="InsightFace model name")
    embedding_dim: int = Field(default=512, description="Face embedding dimension")
    face_match_threshold: float = Field(
        default=0.35, ge=0.0, le=1.0, description="Minimum similarity score for matches"
    )

    # Upload limits
    max_upload_mb: int = Field(default=15, gt=0, description="Maximum file size in MB")
    allowed_image_types: str = Field(
        default="jpeg,jpg,png,webp", description="Comma-separated allowed image types"
    )

    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 path prefix")
    cors_origins: list[str] = Field(
        default=["http://localhost:8000", "http://127.0.0.1:8000"],
        description="Allowed CORS origins",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    @property
    def max_upload_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_mb * 1024 * 1024

    @property
    def allowed_types_set(self) -> set[str]:
        """Set of allowed image extensions."""
        return {ext.strip().lower() for ext in self.allowed_image_types.split(",")}

    def get_event_dir(self, event_id: str) -> Path:
        """Get the directory path for a specific event."""
        return self.data_dir / "events" / event_id

    def ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
