from datetime import timedelta

from sqlalchemy.orm import Session

from api.core.cleanup import purge_expired
from api.core.db import get_engine
from api.core.models import Document, utcnow
from api.core.usage import month_key
from tests.api.conftest import make_pdf


def upload(client, raw, name="report.pdf"):
    return client.post("/api/documents", files={"file": (name, raw, "application/pdf")})


def test_upload_returns_pages_and_blocks(document):
    assert document["name"] == "report.pdf"
    assert len(document["pages"]) == 2
    table = document["pages"][1]["blocks"][1]
    assert table["type"] == "table"
    assert table["flags"] == ["Column 'Q2 visits' mixes numbers and text"]


def test_reupload_hits_the_cache(client, adobe):
    raw = make_pdf()
    first = upload(client, raw).json()
    second = upload(client, raw).json()

    assert adobe.extract_calls == 1
    assert first["transactions_used"] == 1
    assert second["transactions_used"] == 0
    assert first["id"] != second["id"]


def test_non_pdf_is_rejected(client):
    response = upload(client, b"GIF89a not a pdf", "image.pdf")

    assert response.status_code == 415
    assert response.json()["detail"] == "Only PDF files are accepted."


def test_unreadable_pdf_is_rejected(client):
    assert upload(client, b"%PDF-1.4 garbage").status_code == 422


def test_page_limit(client, settings):
    response = upload(client, make_pdf(pages=settings.max_pages + 1))

    assert response.status_code == 413


def test_size_limit(client, settings, monkeypatch):
    monkeypatch.setattr(type(settings), "max_upload_bytes", property(lambda _: 100))

    assert upload(client, make_pdf()).status_code == 413


def test_usage_reports_mode_and_budget(client):
    usage = client.get("/api/usage").json()

    assert usage == {
        "month": month_key(),
        "used": 0,
        "limit": 500,
        "extract_cap": 450,
        "remaining": 500,
        "mode": "fixture",
    }


def test_read_and_delete(client, document):
    url = f"/api/documents/{document['id']}"

    assert client.get(url).json()["id"] == document["id"]
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_purge_removes_expired_documents(client, document, settings):
    with Session(get_engine()) as session:
        removed = purge_expired(session, settings, now=utcnow() + timedelta(hours=25))

        assert removed == 1
        assert session.get(Document, document["id"]) is None
    assert not any(settings.cache_dir.iterdir())
