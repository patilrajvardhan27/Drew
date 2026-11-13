"""Per-email attempt limits kept in the database, so they hold across restarts and server processes."""

from datetime import timedelta
from typing import Literal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from api.core.errors import AppError
from api.core.models import AuthAttempt, utcnow

Kind = Literal["login", "reset"]
WINDOW = timedelta(minutes=15)
LIMITS: dict[str, int] = {"login": 5, "reset": 3}


def check(session: Session, email: str, kind: Kind) -> None:
    since = utcnow() - WINDOW
    recent = session.scalar(
        select(func.count())
        .select_from(AuthAttempt)
        .where(AuthAttempt.email == email, AuthAttempt.kind == kind, AuthAttempt.at > since)
    )
    if recent >= LIMITS[kind]:
        raise AppError(429, "Too many attempts. Try again in 15 minutes.")


def note(session: Session, email: str, kind: Kind) -> None:
    session.add(AuthAttempt(email=email, kind=kind))
    session.commit()


def clear(session: Session, email: str, kind: Kind) -> None:
    session.execute(delete(AuthAttempt).where(AuthAttempt.email == email, AuthAttempt.kind == kind))
    session.commit()
