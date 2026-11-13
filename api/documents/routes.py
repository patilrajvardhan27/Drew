from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from api.adobe.provider import Adobe, get_adobe
from api.core import usage
from api.core.config import Settings, get_settings
from api.core.db import get_or_404, get_session
from api.core.models import Document
from api.core.schemas import DocumentOut, UsageOut
from api.documents.service import ingest

router = APIRouter(tags=["documents"])


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    adobe: Adobe = Depends(get_adobe),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    # Read one byte past the limit so oversized files are caught without loading all of them.
    raw = file.file.read(settings.max_upload_bytes + 1)
    doc = ingest(session, adobe, settings, file.filename or "document.pdf", raw)
    return DocumentOut.build(doc)


@router.get("/documents/{document_id}")
def read_document(document_id: str, session: Session = Depends(get_session)) -> DocumentOut:
    return DocumentOut.build(get_or_404(session, Document, document_id))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, session: Session = Depends(get_session)) -> Response:
    session.delete(get_or_404(session, Document, document_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/usage")
def read_usage(
    session: Session = Depends(get_session), settings: Settings = Depends(get_settings)
) -> UsageOut:
    return usage.summary(session, settings)
