import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from api.adobe.output import ExtractOutput
from api.adobe.provider import get_adobe
from api.core.config import get_settings
from api.core.db import reset_engine

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class FakeAdobe:
    """Replays the recorded Extract result and counts calls, so tests need no key."""

    def __init__(self):
        self.extract_calls = 0
        self.export_html: list[str] = []

    def extract(self, session, pdf, pages):
        self.extract_calls += 1
        return ExtractOutput.from_dir(FIXTURES / "extract"), 1

    def html_to_pdf(self, session, html, pages):
        self.export_html.append(html)
        return b"%PDF-1.7 fake", 1


def make_pdf(pages: int = 2, salt: str = "") -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": f"test {salt}"})
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("REDRAFT_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("REDRAFT_STORAGE_DIR", str(tmp_path / "files"))
    monkeypatch.setenv("REDRAFT_ADOBE_MODE", "fixture")
    monkeypatch.setenv("REDRAFT_FIXTURE_DIR", str(FIXTURES / "extract"))
    monkeypatch.setenv("REDRAFT_WEB_DIST", str(tmp_path / "no-dist"))
    get_settings.cache_clear()
    reset_engine()
    yield get_settings()
    reset_engine()
    get_settings.cache_clear()


@pytest.fixture
def adobe():
    return FakeAdobe()


@pytest.fixture
def client(settings, adobe):
    from api.main import create_app

    app = create_app()
    app.dependency_overrides[get_adobe] = lambda: adobe
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def document(client):
    response = client.post("/api/documents", files={"file": ("report.pdf", make_pdf(), "application/pdf")})
    assert response.status_code == 201, response.text
    return response.json()
