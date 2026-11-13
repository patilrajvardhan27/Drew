from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.core.db import get_engine
from api.core.models import HistoryEntry


def texts(doc, page=0):
    return [b["text"] for b in doc["pages"][page]["blocks"]]


def fetch(client, document):
    return client.get(f"/api/documents/{document['id']}").json()


def undo(client, document):
    return client.post(f"/api/documents/{document['id']}/undo")


def test_new_document_has_nothing_to_undo(client, document):
    assert document["can_undo"] is False
    assert undo(client, document).status_code == 409


def test_undo_reverts_a_move_and_survives_reload(client, document):
    before = texts(document)
    first = document["pages"][0]["blocks"][0]["id"]
    client.post(f"/api/blocks/{first}/move", json={"page_id": document["pages"][1]["id"], "position": 0})

    assert fetch(client, document)["can_undo"] is True
    restored = undo(client, document).json()

    assert texts(restored) == before
    assert restored["pages"][0]["blocks"][0]["id"] == first
    assert texts(fetch(client, document)) == before


def test_undo_restores_deleted_page(client, document):
    client.delete(f"/api/pages/{document['pages'][1]['id']}")

    restored = undo(client, document).json()

    assert [p["id"] for p in restored["pages"]] == [p["id"] for p in document["pages"]]
    assert restored["pages"][1]["source_index"] == 1


def test_typing_into_one_block_makes_one_undo_step(client, document):
    block = document["pages"][0]["blocks"][2]
    for text in ("a", "ab", "abc"):
        client.patch(f"/api/blocks/{block['id']}", json={"text": text})

    restored = undo(client, document).json()

    assert restored["pages"][0]["blocks"][2]["text"] == block["text"]
    assert restored["can_undo"] is False


def test_history_is_capped(client, document):
    block = document["pages"][0]["blocks"][0]["id"]
    page = document["pages"][0]["id"]
    for i in range(55):
        client.post(f"/api/blocks/{block}/move", json={"page_id": page, "position": i % 3})

    with Session(get_engine()) as session:
        count = session.scalar(select(func.count()).select_from(HistoryEntry))
    assert count == 50


def test_split_uses_the_unsaved_draft(client, document):
    block = document["pages"][0]["blocks"][2]
    draft = "First half. Second half."

    doc = client.post(f"/api/blocks/{block['id']}/split", json={"offset": 11, "text": draft}).json()

    assert texts(doc)[2:4] == ["First half.", "Second half."]
    assert doc["pages"][0]["blocks"][3]["type"] == "paragraph"
    assert [b["position"] for b in doc["pages"][0]["blocks"]] == list(range(7))


def test_split_refuses_tables_and_edges(client, document):
    table = document["pages"][1]["blocks"][1]["id"]
    para = document["pages"][0]["blocks"][2]

    assert client.post(f"/api/blocks/{table}/split", json={"offset": 2}).status_code == 422
    end = len(para["text"])
    assert client.post(f"/api/blocks/{para['id']}/split", json={"offset": end}).status_code == 422


def test_merge_joins_into_the_block_above(client, document):
    blocks = document["pages"][0]["blocks"]

    doc = client.post(f"/api/blocks/{blocks[2]['id']}/merge").json()

    assert texts(doc)[1] == f"{blocks[1]['text']} {blocks[2]['text']}"
    assert len(doc["pages"][0]["blocks"]) == len(blocks) - 1


def test_merge_lists_line_by_line(client, document):
    page = document["pages"][0]
    list_block = page["blocks"][4]
    extra = client.post(
        f"/api/pages/{page['id']}/blocks", json={"type": "list", "text": "One more item.", "position": 5}
    ).json()

    doc = client.post(f"/api/blocks/{extra['id']}/merge").json()

    assert doc["pages"][0]["blocks"][4]["text"] == list_block["text"] + "\nOne more item."


def test_merge_refuses_first_block_and_tables(client, document):
    first = document["pages"][0]["blocks"][0]["id"]
    after_table = document["pages"][1]["blocks"][2]["id"]

    assert client.post(f"/api/blocks/{first}/merge").status_code == 422
    assert client.post(f"/api/blocks/{after_table}/merge").status_code == 422


def test_split_then_undo(client, document):
    block = document["pages"][0]["blocks"][2]
    client.post(f"/api/blocks/{block['id']}/split", json={"offset": 5})

    assert texts(undo(client, document).json()) == texts(document)


def test_coalescing_window_expires(client, document, monkeypatch):
    from api.history import service

    block = document["pages"][0]["blocks"][2]["id"]
    client.patch(f"/api/blocks/{block}", json={"text": "one"})
    monkeypatch.setattr(service, "COALESCE", timedelta(seconds=-1))
    client.patch(f"/api/blocks/{block}", json={"text": "two"})

    assert undo(client, document).json()["pages"][0]["blocks"][2]["text"] == "one"
