from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SYSTEMLENS_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default=Path("data"))
    db_path: Path = Field(default=Path("data") / "systemlens.db")
    sample_interval: float = 2.0
    retention_hours: int = 72

    api_host: str = "127.0.0.1"
    api_port: int = 8080
    log_level: str = "INFO"

    auth_enabled: bool = False
    admin_token: str | None = None
    viewer_token: str | None = None
    allow_lan_ui: bool = True

    ssl_cert_path: Path | None = None
    ssl_key_path: Path | None = None


def load_config() -> AppConfig:
    return AppConfig()
