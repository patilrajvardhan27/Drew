import re

from fastapi import APIRouter, Depends, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from api.adobe.provider import Adobe, get_adobe
from api.core.db import get_or_404, get_session
from api.core.models import Document
from api.export.render import render_html

router = APIRouter(tags=["export"])


def _pdf_name(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", name.rsplit(".", 1)[0]).strip("-") or "document"
    return f"{stem}-redraft.pdf"


@router.get("/documents/{document_id}/preview", response_class=HTMLResponse)
def preview(document_id: str, session: Session = Depends(get_session)) -> HTMLResponse:
    return HTMLResponse(render_html(get_or_404(session, Document, document_id)))


@router.post(
    "/documents/{document_id}/export",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def export_pdf(
    document_id: str,
    session: Session = Depends(get_session),
    adobe: Adobe = Depends(get_adobe),
) -> Response:
    doc = get_or_404(session, Document, document_id)
    pdf, cost = adobe.html_to_pdf(session, render_html(doc), len(doc.pages))
    doc.transactions_used += cost
    session.commit()
    headers = {"Content-Disposition": f'attachment; filename="{_pdf_name(doc.name)}"'}
    return Response(pdf, media_type="application/pdf", headers=headers)
