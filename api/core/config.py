from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDRAFT_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/redraft.db"
    storage_dir: Path = Path("./data/files")

    # "fixture" replays tests/fixtures/extract for every upload, so the app runs without a key.
    adobe_mode: Literal["live", "fixture"] = "live"
    adobe_client_id: str = ""
    adobe_client_secret: str = ""
    fixture_dir: Path = Path("tests/fixtures/extract")

    max_upload_mb: int = 20
    max_pages: int = 50
    monthly_limit: int = 500
    extract_cap: int = 450
    jobs_per_minute: int = 25
    retention_hours: int = 24

    cors_origins: list[str] = ["http://localhost:5173"]
    web_dist: Path = Path("web/dist")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cache_dir(self) -> Path:
        return self.storage_dir / "cache"


@lru_cache
def get_settings() -> Settings:
    return Settings()
