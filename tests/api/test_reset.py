import re
from datetime import timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from api.core.db import get_engine
from api.core.models import PasswordReset, utcnow

OLD = "correct horse battery"
NEW = "a brand new passphrase"
EMAIL = "ada@example.com"


def setup_account(client):
    client.post("/api/auth/register", json={"email": EMAIL, "password": OLD})
    client.post("/api/auth/logout")


def ask(client, email=EMAIL):
    return client.post("/api/auth/password-reset", json={"email": email})


def token_from(mailer) -> str:
    return re.search(r"reset\?token=(\S+)", mailer.sent[-1][2]).group(1)


def confirm(client, token, password=NEW):
    return client.post("/api/auth/password-reset/confirm", json={"token": token, "password": password})


def test_reset_flow_changes_the_password_and_signs_in(client, mailer):
    setup_account(client)

    assert ask(client).status_code == 202
    to, subject, body = mailer.sent[0]
    assert (to, subject) == (EMAIL, "Reset your Redraft password")
    assert "http://testserver/reset?token=" in body

    response = confirm(client, token_from(mailer))

    assert response.status_code == 200
    assert client.get("/api/auth/me").json()["email"] == EMAIL
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": OLD}).status_code == 401
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": NEW}).status_code == 200


def test_unknown_email_gets_the_same_answer_and_no_mail(client, mailer):
    setup_account(client)

    known, unknown = ask(client).json(), ask(client, "nobody@example.com").json()

    assert known == unknown
    assert [m[0] for m in mailer.sent] == [EMAIL]


def test_link_works_once(client, mailer):
    setup_account(client)
    ask(client)
    token = token_from(mailer)

    assert confirm(client, token).status_code == 200
    assert confirm(client, token, "another long passphrase").status_code == 400


def test_expired_link_is_refused(client, mailer):
    setup_account(client)
    ask(client)
    with Session(get_engine()) as session:
        session.execute(update(PasswordReset).values(expires_at=utcnow() - timedelta(minutes=1)))
        session.commit()

    assert confirm(client, token_from(mailer)).status_code == 400


def test_reset_signs_out_other_devices(client, mailer):
    client.post("/api/auth/register", json={"email": EMAIL, "password": OLD})
    other_device = dict(client.cookies)
    ask(client)
    confirm(client, token_from(mailer))

    client.cookies.clear()
    client.cookies.update(other_device)
    assert client.get("/api/auth/me").status_code == 401


def test_reset_requests_are_rate_limited(client, mailer):
    setup_account(client)
    for _ in range(3):
        assert ask(client).status_code == 202

    assert ask(client).status_code == 429
    assert len(mailer.sent) == 3


def test_public_url_is_used_for_links(client, mailer, settings):
    settings.public_url = "https://redraft.example.com/"
    setup_account(client)
    ask(client)

    assert "https://redraft.example.com/reset?token=" in mailer.sent[0][2]


def test_file_mailer_writes_readable_messages(tmp_path):
    from api.auth.mailer import FileMailer

    FileMailer(tmp_path / "mail").send(EMAIL, "Hello", "Body text")

    (message,) = (tmp_path / "mail").iterdir()
    assert message.read_text() == f"To: {EMAIL}\nSubject: Hello\n\nBody text\n"
