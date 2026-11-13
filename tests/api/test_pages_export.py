DETAILS = {
    "company": "Acme & Sons",
    "email": "legal@example.com",
    "effective_date": "2026-03-01",
    "jurisdiction": "Ontario",
}


def add_page(client, document, **body):
    return client.post(f"/api/documents/{document['id']}/pages", json=body)


def test_terms_page_is_filled_and_marked(client, document):
    doc = add_page(client, document, kind="terms", position=2, details=DETAILS).json()

    page = doc["pages"][2]
    texts = [b["text"] for b in page["blocks"]]
    assert page["kind"] == "terms"
    assert texts[0] == "Terms of Service"
    assert texts[1] == "Template text. Not legal advice. Review before publishing."
    assert "Effective March 1, 2026." in texts
    assert not any("{{" in t for t in texts)


def test_copyright_page_inserted_first(client, document):
    doc = add_page(client, document, kind="copyright", position=0, details=DETAILS).json()

    assert [p["kind"] for p in doc["pages"]] == ["copyright", "extracted", "extracted"]
    assert [p["position"] for p in doc["pages"]] == [0, 1, 2]
    assert doc["pages"][0]["blocks"][2]["text"].startswith("Copyright 2026 Acme & Sons.")


def test_blank_page_needs_no_details(client, document):
    doc = add_page(client, document, kind="blank", position=1).json()

    assert doc["pages"][1]["kind"] == "blank"
    assert doc["pages"][1]["blocks"] == []


def test_legal_page_requires_details(client, document):
    assert add_page(client, document, kind="privacy", position=0).status_code == 422


def test_delete_page(client, document):
    doc = client.delete(f"/api/pages/{document['pages'][0]['id']}").json()

    assert len(doc["pages"]) == 1
    assert doc["pages"][0]["position"] == 0


def test_preview_escapes_user_text(client, document):
    add_page(client, document, kind="terms", position=2, details=DETAILS)

    html = client.get(f"/api/documents/{document['id']}/preview").text

    assert "Acme &amp; Sons" in html
    assert html.count('<section class="sheet">') == 3
    assert "<th>Region </th>" in html


def test_export_counts_a_transaction(client, document, adobe):
    response = client.post(f"/api/documents/{document['id']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert 'filename="report-redraft.pdf"' in response.headers["content-disposition"]
    assert "Northwind Field Report" in adobe.export_html[0]
    assert client.get(f"/api/documents/{document['id']}").json()["transactions_used"] == 2
