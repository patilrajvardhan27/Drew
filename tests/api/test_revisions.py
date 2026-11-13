HEADER = "X-Document-Revision"


def first_block(document):
    return document["pages"][0]["blocks"][0]["id"]


def test_new_document_starts_at_revision_zero(document):
    assert document["revision"] == 0


def test_every_change_answers_with_the_new_revision(client, document):
    block = first_block(document)

    edited = client.patch(f"/api/blocks/{block}", json={"text": "a"}, headers={HEADER: "0"})
    deleted = client.delete(f"/api/blocks/{block}", headers={HEADER: "1"})

    assert edited.headers[HEADER] == "1"
    assert deleted.status_code == 204
    assert deleted.headers[HEADER] == "2"
    assert client.get(f"/api/documents/{document['id']}").json()["revision"] == 2


def test_coalesced_typing_still_moves_the_revision(client, document):
    block = first_block(document)
    for revision, text in enumerate(["a", "ab", "abc"]):
        response = client.patch(f"/api/blocks/{block}", json={"text": text}, headers={HEADER: str(revision)})
        assert response.status_code == 200

    assert client.get(f"/api/documents/{document['id']}").json()["revision"] == 3


def test_a_stale_tab_cannot_overwrite_newer_work(client, document):
    block = first_block(document)
    client.patch(f"/api/blocks/{block}", json={"text": "from tab B"}, headers={HEADER: "0"})

    stale = client.patch(f"/api/blocks/{block}", json={"text": "from tab A"}, headers={HEADER: "0"})

    assert stale.status_code == 409
    assert "changed in another tab" in stale.json()["detail"]
    assert (
        client.get(f"/api/documents/{document['id']}").json()["pages"][0]["blocks"][0]["text"] == "from tab B"
    )


def test_a_stale_tab_cannot_undo_someone_elses_change(client, document):
    block = first_block(document)
    client.patch(f"/api/blocks/{block}", json={"text": "tab A edit"}, headers={HEADER: "0"})
    client.delete(f"/api/blocks/{block}", headers={HEADER: "1"})

    response = client.post(f"/api/documents/{document['id']}/undo", headers={HEADER: "1"})

    assert response.status_code == 409


def test_undo_moves_the_revision_forward(client, document):
    client.delete(f"/api/blocks/{first_block(document)}", headers={HEADER: "0"})

    response = client.post(f"/api/documents/{document['id']}/undo", headers={HEADER: "1"})

    assert response.json()["revision"] == 2
    assert response.headers[HEADER] == "2"


def test_requests_without_the_header_are_not_checked(client, document):
    block = first_block(document)
    client.patch(f"/api/blocks/{block}", json={"text": "one"})

    assert client.patch(f"/api/blocks/{block}", json={"text": "two"}).status_code == 200


def test_refused_writes_change_nothing(client, document):
    page = document["pages"][0]["id"]

    response = client.post(
        f"/api/documents/{document['id']}/pages", json={"kind": "blank", "position": 0}, headers={HEADER: "7"}
    )

    assert response.status_code == 409
    doc = client.get(f"/api/documents/{document['id']}").json()
    assert (doc["revision"], doc["can_undo"], doc["pages"][0]["id"]) == (0, False, page)
