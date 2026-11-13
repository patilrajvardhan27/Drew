from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.auth.access import document_for, page_for
from api.auth.sessions import optional_user
from api.core.config import Settings, get_settings
from api.core.db import get_session
from api.core.errors import AppError, NotFound
from api.core.models import Block, Page, User
from api.core.ordering import renumber
from api.core.schemas import DocumentOut, PageCreate
from api.documents.images import page_image_path
from api.history.service import record
from api.pages.legal import legal_blocks

router = APIRouter(tags=["pages"])


@router.post("/documents/{document_id}/pages", status_code=status.HTTP_201_CREATED)
def add_page(
    document_id: str,
    body: PageCreate,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    doc = document_for(session, document_id, user)
    page = Page(kind=body.kind)
    if body.kind != "blank":
        if body.details is None:
            raise AppError(422, "Legal pages need company, email, effective date and jurisdiction.")
        page.blocks = [
            Block(type=b.type, text=b.text, level=b.level, position=i, flags=[])
            for i, b in enumerate(legal_blocks(body.kind, body.details))
        ]
    record(session, doc)
    doc.pages.append(page)
    renumber(doc.pages, page, body.position)
    session.commit()
    return DocumentOut.build(doc)


@router.delete("/pages/{page_id}")
def delete_page(
    page_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    page = page_for(session, page_id, user)
    doc = page.document
    record(session, doc)
    doc.pages.remove(page)
    renumber(doc.pages)
    session.commit()
    return DocumentOut.build(doc)


@router.get("/pages/{page_id}/original", response_class=FileResponse)
def original_page(
    page_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    """The uploaded page as a PNG, for the side-by-side view."""
    page = page_for(session, page_id, user)
    if page.source_index is None:
        raise NotFound("Original page")
    path = page_image_path(settings, page.document.sha256, page.source_index)
    if not path.is_file():
        raise NotFound("Original page")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, max-age=3600"})
