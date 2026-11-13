def block_ids(doc, page_index):
    return [b["id"] for b in doc["pages"][page_index]["blocks"]]


def positions(doc, page_index):
    return [b["position"] for b in doc["pages"][page_index]["blocks"]]


def test_edit_text(client, document):
    block = document["pages"][0]["blocks"][2]

    response = client.patch(f"/api/blocks/{block['id']}", json={"text": "Rewritten."})

    assert response.json()["text"] == "Rewritten."


def test_editing_a_table_revalidates_it(client, document):
    table = document["pages"][1]["blocks"][1]
    fixed = "Region,Q1,Q2\nNorth,12,15\nCoast,9,0\n"

    response = client.patch(f"/api/blocks/{table['id']}", json={"table_csv": fixed})

    assert response.json()["flags"] == []


def test_reorder_within_a_page(client, document):
    before = block_ids(document, 0)

    doc = client.post(
        f"/api/blocks/{before[0]}/move", json={"page_id": document["pages"][0]["id"], "position": 2}
    ).json()

    assert block_ids(doc, 0) == [before[1], before[2], before[0], *before[3:]]
    assert positions(doc, 0) == list(range(len(before)))


def test_move_across_pages(client, document):
    moving = document["pages"][0]["blocks"][0]["id"]
    target = document["pages"][1]["id"]

    doc = client.post(f"/api/blocks/{moving}/move", json={"page_id": target, "position": 0}).json()

    assert block_ids(doc, 1)[0] == moving
    assert moving not in block_ids(doc, 0)
    assert positions(doc, 0) == list(range(len(block_ids(doc, 0))))


def test_move_out_of_range_lands_at_the_end(client, document):
    first = document["pages"][0]["blocks"][0]["id"]

    doc = client.post(
        f"/api/blocks/{first}/move", json={"page_id": document["pages"][0]["id"], "position": 99}
    ).json()

    assert block_ids(doc, 0)[-1] == first


def test_delete_then_restore_like_undo(client, document):
    page = document["pages"][0]
    removed = page["blocks"][1]

    assert client.delete(f"/api/blocks/{removed['id']}").status_code == 204
    restored = client.post(
        f"/api/pages/{page['id']}/blocks",
        json={"type": removed["type"], "text": removed["text"], "level": removed["level"], "position": 1},
    )

    doc = client.get(f"/api/documents/{document['id']}").json()
    assert restored.status_code == 201
    assert doc["pages"][0]["blocks"][1]["text"] == removed["text"]
    assert positions(doc, 0) == list(range(len(page["blocks"])))


def test_table_block_needs_csv(client, document):
    page_id = document["pages"][0]["id"]

    response = client.post(f"/api/pages/{page_id}/blocks", json={"type": "table"})

    assert response.status_code == 422


def test_unknown_block(client):
    assert client.patch("/api/blocks/missing", json={"text": "x"}).status_code == 404
