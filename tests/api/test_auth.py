from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from api.auth.passwords import hash_password, verify_password
from api.core.cleanup import purge_expired
from api.core.db import get_engine
from api.core.models import AuthAttempt, Document, utcnow
from tests.api.conftest import make_pdf

PASSWORD = "correct horse battery"


def register(client, email="ada@example.com", password=PASSWORD):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def test_password_hashes_are_salted_and_verifiable():
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)

    assert first != second
    assert verify_password(PASSWORD, first)
    assert not verify_password("wrong password", first)
    assert not verify_password(PASSWORD, "not-a-hash")


def test_register_signs_in_and_me_works(client):
    response = register(client, email="Ada@Example.com")

    assert response.status_code == 201
    assert "httponly" in response.headers["set-cookie"].lower()
    assert client.get("/api/auth/me").json()["email"] == "ada@example.com"


def test_duplicate_and_short_passwords_are_refused(client):
    register(client)

    assert register(client).status_code == 409
    assert register(client, email="b@example.com", password="short").status_code == 422


def test_login_logout(client):
    register(client)
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401

    bad = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong password!"})
    good = client.post("/api/auth/login", json={"email": "ada@example.com", "password": PASSWORD})

    assert bad.status_code == 401
    assert good.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_lockout_is_stored_in_the_database(client, settings):
    register(client)
    client.post("/api/auth/logout")
    wrong = {"email": "ada@example.com", "password": "wrong password!"}
    for _ in range(5):
        assert client.post("/api/auth/login", json=wrong).status_code == 401

    right = {"email": "ada@example.com", "password": PASSWORD}
    assert client.post("/api/auth/login", json=right).status_code == 429
    with Session(get_engine()) as session:
        assert session.scalar(select(func.count()).select_from(AuthAttempt)) == 5
        session.execute(update(AuthAttempt).values(at=utcnow() - timedelta(minutes=16)))
        session.commit()
    assert client.post("/api/auth/login", json=right).status_code == 200


def test_old_attempts_are_purged(client, settings):
    with Session(get_engine()) as session:
        session.add(AuthAttempt(email="a@example.com", kind="login", at=utcnow() - timedelta(days=2)))
        session.commit()
        purge_expired(session, settings)
        assert session.scalar(select(func.count()).select_from(AuthAttempt)) == 0


def test_signed_in_upload_is_owned_and_private(client, settings):
    register(client)
    doc = client.post("/api/documents", files={"file": ("a.pdf", make_pdf(), "application/pdf")}).json()

    assert doc["owned"] is True
    assert [d["id"] for d in client.get("/api/documents").json()] == [doc["id"]]

    client.post("/api/auth/logout")
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404
    block = doc["pages"][0]["blocks"][0]["id"]
    assert client.patch(f"/api/blocks/{block}", json={"text": "x"}).status_code == 404


def test_claim_keeps_a_document_past_the_purge(client, document, settings):
    register(client)
    claimed = client.post(f"/api/documents/{document['id']}/claim").json()

    with Session(get_engine()) as session:
        purge_expired(session, settings, now=utcnow() + timedelta(days=3))
        assert session.get(Document, document["id"]) is not None
    assert claimed["owned"] is True
    assert any(settings.cache_dir.iterdir())


def test_claim_needs_sign_in(client, document):
    assert client.post(f"/api/documents/{document['id']}/claim").status_code == 401


def test_listing_needs_sign_in(client):
    assert client.get("/api/documents").status_code == 401
