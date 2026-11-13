import logging
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
log = logging.getLogger(__name__)


class Settings(BaseSettings):
    # .env is read from the repo root, whichever directory the server is started from.
    model_config = SettingsConfigDict(env_prefix="REDRAFT_", env_file=ROOT / ".env", extra="ignore")

    database_url: str = "sqlite:///./data/redraft.db"
    storage_dir: Path = Path("./data/files")

    # "fixture" replays tests/fixtures/extract for every upload, so the app runs without a key.
    adobe_mode: Literal["live", "fixture"] = "live"
    # Adobe's own variable names work too, so credentials copied from their samples need no renaming.
    adobe_client_id: str = Field(
        default="", validation_alias=AliasChoices("REDRAFT_ADOBE_CLIENT_ID", "PDF_SERVICES_CLIENT_ID")
    )
    adobe_client_secret: str = Field(
        default="",
        validation_alias=AliasChoices("REDRAFT_ADOBE_CLIENT_SECRET", "PDF_SERVICES_CLIENT_SECRET"),
    )
    fixture_dir: Path = ROOT / "tests/fixtures/extract"

    max_upload_mb: int = 20
    max_pages: int = 50
    monthly_limit: int = 500
    extract_cap: int = 450
    jobs_per_minute: int = 25
    retention_hours: int = 24

    # Signs short-lived Express links. Without one, links stop working when the server restarts.
    secret_key: str = ""
    secure_cookies: bool = False
    session_days: int = 30

    # Where reset emails link to; defaults to the address the request came in on.
    public_url: str = ""
    # "log" writes emails to the server log for local work; use "smtp" anywhere real.
    mail_backend: Literal["log", "smtp"] = "log"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Redraft <no-reply@localhost>"

    cors_origins: list[str] = ["http://localhost:5173"]
    web_dist: Path = ROOT / "web/dist"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cache_dir(self) -> Path:
        return self.storage_dir / "cache"

    def signing_key(self) -> bytes:
        return self.secret_key.encode()


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.secret_key:
        settings.secret_key = secrets.token_hex(32)
        log.warning("REDRAFT_SECRET_KEY is not set; Express links will reset on restart.")
    if settings.adobe_mode == "live" and not (settings.adobe_client_id and settings.adobe_client_secret):
        log.warning("Adobe mode is live but credentials are missing; uploads will fail with 503.")
    return settings
