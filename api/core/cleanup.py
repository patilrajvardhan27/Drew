import asyncio
import logging
import shutil
from datetime import UTC, datetime, timedelta

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.db import get_engine
from api.core.models import AuthAttempt, AuthSession, Document, PasswordReset, utcnow

log = logging.getLogger(__name__)


def purge_expired(session: Session, settings: Settings, now: datetime | None = None) -> int:
    """Delete anonymous documents and cached Extract results older than the retention window."""
    cutoff = (now or utcnow()) - timedelta(hours=settings.retention_hours)
    _purge_auth_rows(session, now or utcnow())
    anonymous = select(Document).where(Document.owner_id.is_(None), Document.created_at < cutoff)
    expired = session.scalars(anonymous).all()
    for doc in expired:
        session.delete(doc)
    session.commit()

    # Cached results behind a document someone kept are still needed for its original page images.
    kept = set(session.scalars(select(Document.sha256).where(Document.owner_id.is_not(None))))
    if settings.cache_dir.exists():
        for entry in settings.cache_dir.iterdir():
            if entry.name in kept:
                continue
            modified = datetime.fromtimestamp(entry.stat().st_mtime, UTC).replace(tzinfo=None)
            if modified < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
    return len(expired)


def _purge_auth_rows(session: Session, now: datetime) -> None:
    session.execute(delete(AuthAttempt).where(AuthAttempt.at < now - timedelta(days=1)))
    session.execute(delete(PasswordReset).where(PasswordReset.expires_at < now))
    session.execute(delete(AuthSession).where(AuthSession.expires_at < now))


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
