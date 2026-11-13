"""Every route loads documents, pages and blocks through here, so ownership is checked in one place.

Anonymous documents are reachable by anyone holding their unguessable link. Once a document
belongs to an account, only that account can see or change it.
"""

from sqlalchemy.orm import Session

from api.core.db import get_or_404
from api.core.errors import NotFound
from api.core.models import Block, Document, Page, User


def check(doc: Document, user: User | None) -> Document:
    if doc.owner_id is not None and (user is None or user.id != doc.owner_id):
        raise NotFound("Document")
    return doc


def document_for(session: Session, document_id: str, user: User | None) -> Document:
    return check(get_or_404(session, Document, document_id), user)


def page_for(session: Session, page_id: str, user: User | None) -> Page:
    page = get_or_404(session, Page, page_id)
    check(page.document, user)
    return page


def block_for(session: Session, block_id: str, user: User | None) -> Block:
    block = get_or_404(session, Block, block_id)
    check(block.page.document, user)
    return block
