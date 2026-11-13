import asyncio
import logging
import shutil
from datetime import UTC, datetime, timedelta

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.db import get_engine
from api.core.models import Document, utcnow

log = logging.getLogger(__name__)


def purge_expired(session: Session, settings: Settings, now: datetime | None = None) -> int:
    """Delete documents and cached Extract results older than the retention window."""
    cutoff = (now or utcnow()) - timedelta(hours=settings.retention_hours)
    expired = session.scalars(select(Document).where(Document.created_at < cutoff)).all()
    for doc in expired:
        session.delete(doc)
    session.commit()

    if settings.cache_dir.exists():
        for entry in settings.cache_dir.iterdir():
            modified = datetime.fromtimestamp(entry.stat().st_mtime, UTC).replace(tzinfo=None)
            if modified < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
    return len(expired)


async def purge_forever(settings: Settings, every_seconds: int = 3600) -> None:
    def run_once() -> int:
        with Session(get_engine()) as session:
            return purge_expired(session, settings)

    while True:
        try:
            removed = await run_in_threadpool(run_once)
            if removed:
                log.info("Purged %d expired documents", removed)
        except Exception:
            log.exception("Purge failed")
        await asyncio.sleep(every_seconds)
