from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.adobe.provider import Adobe, get_adobe
from api.auth.access import document_for
from api.auth.sessions import optional_user, required_user
from api.core import usage
from api.core.config import Settings, get_settings
from api.core.db import get_session
from api.core.models import Document, User
from api.core.schemas import DocumentOut, DocumentSummary, UsageOut
from api.documents.service import ingest
from api.history.service import undo

router = APIRouter(tags=["documents"])


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    adobe: Adobe = Depends(get_adobe),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    # Read one byte past the limit so oversized files are caught without loading all of them.
    raw = file.file.read(settings.max_upload_bytes + 1)
    doc = ingest(session, adobe, settings, file.filename or "document.pdf", raw, owner=user)
    return DocumentOut.build(doc)


@router.get("/documents")
def list_documents(
    session: Session = Depends(get_session), user: User = Depends(required_user)
) -> list[DocumentSummary]:
    query = (
        select(Document)
        .where(Document.owner_id == user.id)
        .options(selectinload(Document.pages))
        .order_by(Document.created_at.desc())
    )
    return [
        DocumentSummary(id=d.id, name=d.name, created_at=d.created_at, page_count=len(d.pages))
        for d in session.scalars(query)
    ]


@router.get("/documents/{document_id}")
def read_document(
    document_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    return DocumentOut.build(document_for(session, document_id, user))


@router.post("/documents/{document_id}/claim")
def claim_document(
    document_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(required_user),
) -> DocumentOut:
    """Move an anonymous document into the signed-in account so it outlives the 24 hour purge."""
    doc = document_for(session, document_id, user)
    if doc.owner_id is None:
        doc.owner_id = user.id
        session.commit()
    return DocumentOut.build(doc)


@router.post("/documents/{document_id}/undo")
def undo_change(
    document_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    doc = document_for(session, document_id, user)
    undo(session, doc)
    return DocumentOut.build(doc)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> Response:
    session.delete(document_for(session, document_id, user))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/usage")
def read_usage(
    session: Session = Depends(get_session), settings: Settings = Depends(get_settings)
) -> UsageOut:
    return usage.summary(session, settings)
