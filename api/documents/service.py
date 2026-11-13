import hashlib
import io
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy.orm import Session

from api.adobe.output import ExtractOutput
from api.adobe.provider import Adobe
from api.blocks.mapping import map_extract
from api.core.config import Settings
from api.core.errors import AppError
from api.core.models import Block, Document, Page, User
from api.documents.images import render_pages
from api.tables.validate import validate_csv

PDF_MAGIC = b"%PDF-"


def count_pages(raw: bytes, settings: Settings) -> int:
    if not raw.startswith(PDF_MAGIC):
        raise AppError(415, "Only PDF files are accepted.")
    if len(raw) > settings.max_upload_bytes:
        raise AppError(413, f"PDFs are limited to {settings.max_upload_mb} MB.")
    try:
        pages = len(PdfReader(io.BytesIO(raw)).pages)
    except (PdfReadError, ValueError) as exc:
        raise AppError(422, "This PDF could not be read. It may be damaged or encrypted.") from exc
    if pages > settings.max_pages:
        raise AppError(413, f"PDFs are limited to {settings.max_pages} pages for now.")
    return pages


def ingest(
    session: Session, adobe: Adobe, settings: Settings, name: str, raw: bytes, owner: User | None = None
) -> Document:
    pages = count_pages(raw, settings)
    sha = hashlib.sha256(raw).hexdigest()
    cache = settings.cache_dir / sha

    cost = 0
    if (cache / "structuredData.json").exists():
        output = ExtractOutput.from_dir(cache)
        cache.touch()
    else:
        output, cost = adobe.extract(session, raw, pages)
        output.to_dir(cache)
    render_pages(raw, cache / "pages")

    doc = build_document(Path(name).name or "document.pdf", sha, output, cost)
    doc.owner_id = owner.id if owner else None
    session.add(doc)
    session.commit()
    return doc


def build_document(name: str, sha: str, output: ExtractOutput, cost: int) -> Document:
    doc = Document(name=name[:255], sha256=sha, transactions_used=cost)
    for page_index, mapped in enumerate(map_extract(output)):
        page = Page(kind="extracted", position=page_index, source_index=page_index)
        page.blocks = [
            Block(
                type=block.type,
                level=block.level,
                text=block.text,
                table_csv=block.table_csv,
                flags=validate_csv(block.table_csv) if block.table_csv is not None else [],
                position=position,
            )
            for position, block in enumerate(mapped)
        ]
        doc.pages.append(page)
    return doc
