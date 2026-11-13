"""Undo by snapshot: before each change the document's pages are saved, and undo restores the last one.

Documents are capped at 50 extracted pages, so a snapshot is small, and one rule covers every kind
of change (edit, move, split, merge, delete, add page) without writing an inverse for each.
"""

from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.core.errors import AppError
from api.core.models import Block, Document, HistoryEntry, Page, utcnow
from api.core.ordering import by_position

MAX_ENTRIES = 50
COALESCE = timedelta(seconds=60)
BLOCK_FIELDS = ("id", "type", "level", "text", "position", "table_csv", "flags")


def snapshot(doc: Document) -> list[dict]:
    return [
        {
            "id": page.id,
            "kind": page.kind,
            "position": page.position,
            "source_index": page.source_index,
            "blocks": [{f: getattr(b, f) for f in BLOCK_FIELDS} for b in by_position(page.blocks)],
        }
        for page in by_position(doc.pages)
    ]


def _latest(session: Session, doc: Document) -> HistoryEntry | None:
    query = select(HistoryEntry).where(HistoryEntry.document_id == doc.id).order_by(HistoryEntry.id.desc())
    return session.scalars(query.limit(1)).first()


def record(session: Session, doc: Document, key: str | None = None) -> None:
    """Save the current state. Repeated edits to the same block within a minute share one entry."""
    latest = _latest(session, doc)
    if key and latest and latest.key == key and utcnow() - latest.created_at < COALESCE:
        return
    session.add(HistoryEntry(document_id=doc.id, key=key, pages=snapshot(doc)))
    doc.undo_depth = min(doc.undo_depth + 1, MAX_ENTRIES)
    session.flush()
    keep = select(HistoryEntry.id).where(HistoryEntry.document_id == doc.id)
    keep = keep.order_by(HistoryEntry.id.desc()).limit(MAX_ENTRIES)
    session.execute(
        delete(HistoryEntry).where(HistoryEntry.document_id == doc.id, HistoryEntry.id.not_in(keep))
    )


def undo(session: Session, doc: Document) -> None:
    entry = _latest(session, doc)
    if entry is None:
        raise AppError(409, "There is nothing to undo.")
    doc.pages.clear()
    session.flush()
    for saved in entry.pages:
        page = Page(
            id=saved["id"],
            kind=saved["kind"],
            position=saved["position"],
            source_index=saved["source_index"],
        )
        page.blocks = [Block(**{f: block[f] for f in BLOCK_FIELDS}) for block in saved["blocks"]]
        doc.pages.append(page)
    session.delete(entry)
    doc.undo_depth = max(doc.undo_depth - 1, 0)
    session.commit()
