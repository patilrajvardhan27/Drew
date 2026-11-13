import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from api.adobe.provider import Adobe, get_adobe
from api.auth.access import document_for
from api.auth.sessions import optional_user
from api.core.config import Settings, get_settings
from api.core.db import get_or_404, get_session
from api.core.models import Document, User
from api.core.schemas import ExpressLink
from api.export import links
from api.export.render import render_html

router = APIRouter(tags=["export"])
PDF_RESPONSE = {200: {"content": {"application/pdf": {}}}}


def _pdf_name(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", name.rsplit(".", 1)[0]).strip("-") or "document"
    return f"{stem}-redraft.pdf"


def _export(session: Session, adobe: Adobe, doc: Document) -> Response:
    pdf, cost = adobe.html_to_pdf(session, render_html(doc), len(doc.pages))
    doc.transactions_used += cost
    session.commit()
    headers = {"Content-Disposition": f'attachment; filename="{_pdf_name(doc.name)}"'}
    return Response(pdf, media_type="application/pdf", headers=headers)


@router.get("/documents/{document_id}/preview", response_class=HTMLResponse)
def preview(
    document_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> HTMLResponse:
    return HTMLResponse(render_html(document_for(session, document_id, user)))


@router.post("/documents/{document_id}/export", response_class=Response, responses=PDF_RESPONSE)
def export_pdf(
    document_id: str,
    session: Session = Depends(get_session),
    adobe: Adobe = Depends(get_adobe),
    user: User | None = Depends(optional_user),
) -> Response:
    return _export(session, adobe, document_for(session, document_id, user))


@router.post("/documents/{document_id}/express-link")
def create_express_link(
    document_id: str,
    request: Request,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
    settings: Settings = Depends(get_settings),
) -> ExpressLink:
    doc = document_for(session, document_id, user)
    expires, signature = links.sign(settings, doc.id)
    url = request.url_for("express_export", document_id=doc.id).include_query_params(
        expires=expires, signature=signature
    )
    return ExpressLink(url=str(url), expires_at=datetime.fromtimestamp(expires, UTC))


@router.get("/express/{document_id}", response_class=Response, responses=PDF_RESPONSE, name="express_export")
def express_export(
    document_id: str,
    expires: int,
    signature: str,
    session: Session = Depends(get_session),
    adobe: Adobe = Depends(get_adobe),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Called by the Express add-on: the signature stands in for the owner's session."""
    links.verify(settings, document_id, expires, signature)
    return _export(session, adobe, get_or_404(session, Document, document_id))
