"""Centralized configuration via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: dfireballz/config.py -> parent -> parent = repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    postgres_user: str = Field(default="dfireballz", description="PostgreSQL username")
    postgres_password: str = Field(default="", description="PostgreSQL password")
    postgres_db: str = Field(default="dfireballz", description="PostgreSQL database name")
    database_url: str = Field(
        default="postgresql://dfireballz:changeme@db:5432/dfireballz",
        description="Full database URL",
    )

    # --- Redis ---
    redis_url: str = Field(default="redis://redis:6379/0", description="Redis URL")

    # --- Orchestrator ---
    orchestrator_url: str = Field(
        default="http://orchestrator:8800",
        description="Orchestrator API base URL",
    )

    # --- API Keys (threat intel) ---
    virustotal_api_key: str = Field(default="", description="VirusTotal API key")
    shodan_api_key: str = Field(default="", description="Shodan API key")
    abuseipdb_api_key: str = Field(default="", description="AbuseIPDB API key")
    urlscan_api_key: str = Field(default="", description="URLScan API key")
    vulncheck_api_key: str = Field(default="", description="VulnCheck API key")

    # --- General ---
    max_iterations: int = Field(
        default=10, description="Maximum tool iterations per investigation session"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    results_dir: Path = Field(
        default=_REPO_ROOT / "results", description="Directory for session results"
    )
    reports_dir: Path = Field(
        default=_REPO_ROOT / "reports", description="Directory for organized reports"
    )
    evidence_dir: Path = Field(
        default=_REPO_ROOT / "evidence", description="Directory for evidence files"
    )
    cases_dir: Path = Field(
        default=_REPO_ROOT / "cases", description="Directory for case files"
    )


# Singleton instance
settings = Settings()
