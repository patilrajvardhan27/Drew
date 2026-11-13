from functools import lru_cache
from typing import Protocol

from sqlalchemy.orm import Session

from api.adobe.client import AdobeClient
from api.adobe.extract import extract_cost, extract_job
from api.adobe.html_to_pdf import html_to_pdf_cost, html_to_pdf_job
from api.adobe.output import ExtractOutput
from api.core.config import Settings, get_settings
from api.core.errors import AppError


class Adobe(Protocol):
    """What the routes need from Adobe; each call returns its result and the transactions spent."""

    def extract(self, session: Session, pdf: bytes, pages: int) -> tuple[ExtractOutput, int]: ...

    def html_to_pdf(self, session: Session, html: str, pages: int) -> tuple[bytes, int]: ...


class LiveAdobe:
    def __init__(self, settings: Settings):
        self.client = AdobeClient(settings)

    def extract(self, session: Session, pdf: bytes, pages: int) -> tuple[ExtractOutput, int]:
        cost = extract_cost(pages)
        return self.client.run(session, "extract", cost, extract_job(pdf)), cost

    def html_to_pdf(self, session: Session, html: str, pages: int) -> tuple[bytes, int]:
        cost = html_to_pdf_cost(pages)
        return self.client.run(session, "export", cost, html_to_pdf_job(html)), cost


class FixtureAdobe:
    """Offline stand-in: every upload yields the recorded sample, and export is unavailable."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def extract(self, session: Session, pdf: bytes, pages: int) -> tuple[ExtractOutput, int]:
        return ExtractOutput.from_dir(self.settings.fixture_dir), 0

    def html_to_pdf(self, session: Session, html: str, pages: int) -> tuple[bytes, int]:
        raise AppError(503, "PDF export needs Adobe credentials. Use the preview in offline mode.")


@lru_cache
def get_adobe() -> Adobe:
    settings = get_settings()
    return LiveAdobe(settings) if settings.adobe_mode == "live" else FixtureAdobe(settings)
