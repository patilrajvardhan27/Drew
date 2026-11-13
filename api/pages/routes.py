from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.core.db import get_or_404, get_session
from api.core.errors import AppError
from api.core.models import Block, Document, Page
from api.core.ordering import renumber
from api.core.schemas import DocumentOut, PageCreate
from api.pages.legal import legal_blocks

router = APIRouter(tags=["pages"])


@router.post("/documents/{document_id}/pages", status_code=status.HTTP_201_CREATED)
def add_page(document_id: str, body: PageCreate, session: Session = Depends(get_session)) -> DocumentOut:
    doc = get_or_404(session, Document, document_id)
    page = Page(kind=body.kind)
    if body.kind != "blank":
        if body.details is None:
            raise AppError(422, "Legal pages need company, email, effective date and jurisdiction.")
        page.blocks = [
            Block(type=b.type, text=b.text, level=b.level, position=i, flags=[])
            for i, b in enumerate(legal_blocks(body.kind, body.details))
        ]
    doc.pages.append(page)
    renumber(doc.pages, page, body.position)
    session.commit()
    return DocumentOut.build(doc)


@router.delete("/pages/{page_id}")
def delete_page(page_id: str, session: Session = Depends(get_session)) -> DocumentOut:
    page = get_or_404(session, Page, page_id)
    doc = page.document
    doc.pages.remove(page)
    renumber(doc.pages)
    session.commit()
    return DocumentOut.build(doc)
