"""Everything a route needs to change a document: access, the stale-tab check, and history.

The editor sends the revision it last saw in X-Document-Revision. If another tab or device changed
the document since, the write is refused with 409 instead of silently overwriting that work, and
the editor reloads. Every successful change answers with the new revision in the same header.
"""

from dataclasses import dataclass

from fastapi import Depends, Header, Response
from sqlalchemy.orm import Session

from api.auth import access
from api.auth.sessions import optional_user
from api.core.db import get_session
from api.core.errors import AppError
from api.core.models import Block, Document, Page, User
from api.history import service

REVISION_HEADER = "X-Document-Revision"
STALE = "This document changed in another tab or window. The latest version has been loaded."


@dataclass
class Edit:
    session: Session
    user: User | None
    response: Response
    expected: int | None

    def document(self, document_id: str) -> Document:
        return access.document_for(self.session, document_id, self.user)

    def page(self, page_id: str) -> Page:
        return access.page_for(self.session, page_id, self.user)

    def block(self, block_id: str) -> Block:
        return access.block_for(self.session, block_id, self.user)

    def check(self, doc: Document) -> None:
        if self.expected is not None and self.expected != doc.revision:
            raise AppError(409, STALE)

    def record(self, doc: Document, key: str | None = None) -> None:
        self.check(doc)
        service.record(self.session, doc, key)
        self.announce(doc)

    def undo(self, doc: Document) -> None:
        self.check(doc)
        service.undo(self.session, doc)
        self.announce(doc)

    def announce(self, doc: Document) -> None:
        self.response.headers[REVISION_HEADER] = str(doc.revision)


def edit_context(
    response: Response,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
    revision: int | None = Header(default=None, alias=REVISION_HEADER),
) -> Edit:
    return Edit(session=session, user=user, response=response, expected=revision)
