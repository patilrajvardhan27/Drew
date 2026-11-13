import time
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import create_engine, inspect, text

from api.core.db import add_missing_columns
from api.core.errors import AppError
from api.export import links


def test_original_page_is_served_as_png(client, document):
    page = document["pages"][0]

    response = client.get(f"/api/pages/{page['id']}/original")

    assert page["source_index"] == 0
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


def test_added_pages_have_no_original(client, document):
    doc = client.post(f"/api/documents/{document['id']}/pages", json={"kind": "blank", "position": 0}).json()

    assert doc["pages"][0]["source_index"] is None
    assert client.get(f"/api/pages/{doc['pages'][0]['id']}/original").status_code == 404


def test_express_link_exports_without_a_session(client, document, adobe):
    link = client.post(f"/api/documents/{document['id']}/express-link").json()
    url = urlparse(link["url"])

    response = client.get(f"{url.path}?{url.query}")

    assert url.path == f"/api/express/{document['id']}"
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(adobe.export_html) == 1


def test_express_link_rejects_tampering(client, document):
    link = urlparse(client.post(f"/api/documents/{document['id']}/express-link").json()["url"])
    query = parse_qs(link.query)

    forged = f"{link.path}?expires={int(query['expires'][0]) + 3600}&signature={query['signature'][0]}"

    assert client.get(forged).status_code == 403


def test_express_link_expires(settings):
    expires, signature = links.sign(settings, "doc", now=time.time() - 3600)

    with pytest.raises(AppError) as error:
        links.verify(settings, "doc", expires, signature)
    assert error.value.status == 410


def test_express_route_answers_any_origin_and_exposes_the_title(client, document):
    link = urlparse(client.post(f"/api/documents/{document['id']}/express-link").json()["url"])

    response = client.get(f"{link.path}?{link.query}", headers={"Origin": "https://anything.example"})

    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-expose-headers"] == "Content-Disposition"


def test_express_preflight_may_reach_a_local_server(client, document):
    response = client.options(
        f"/api/express/{document['id']}",
        headers={
            "Origin": "https://localhost:5241",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-private-network"] == "true"


def test_other_routes_keep_the_strict_cors_policy(client, document):
    response = client.get(f"/api/documents/{document['id']}", headers={"Origin": "https://anything.example"})

    assert "access-control-allow-origin" not in response.headers


def test_old_databases_gain_new_columns(tmp_path):
    from api.core import models  # noqa: F401
    from api.core.db import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE pages (id VARCHAR(32) PRIMARY KEY, document_id VARCHAR(32))"))
    Base.metadata.create_all(engine)

    add_missing_columns(engine)

    columns = {c["name"] for c in inspect(engine).get_columns("pages")}
    assert {"kind", "position", "source_index"} <= columns
