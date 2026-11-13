from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.errors import AppError
from api.core.models import UsageMonth, utcnow
from api.core.schemas import UsageOut

Operation = Literal["extract", "export"]


def month_key(now: datetime | None = None) -> str:
    return (now or utcnow()).strftime("%Y-%m")


def used_this_month(session: Session) -> int:
    row = session.get(UsageMonth, month_key())
    return row.transactions if row else 0


def ensure_budget(session: Session, settings: Settings, cost: int, operation: Operation) -> None:
    # Extract stops early so there is always room left to export what was already edited.
    limit = settings.extract_cap if operation == "extract" else settings.monthly_limit
    used = used_this_month(session)
    if used + cost > limit:
        raise AppError(
            429,
            f"This month's Adobe budget is spent ({used} of {limit} transactions). It resets on the 1st.",
        )


def record(session: Session, cost: int) -> None:
    key = month_key()
    row = session.get(UsageMonth, key) or UsageMonth(month=key, transactions=0)
    row.transactions += cost
    session.add(row)
    session.commit()


def summary(session: Session, settings: Settings) -> UsageOut:
    used = used_this_month(session)
    return UsageOut(
        month=month_key(),
        used=used,
        limit=settings.monthly_limit,
        extract_cap=settings.extract_cap,
        remaining=max(0, settings.monthly_limit - used),
        mode=settings.adobe_mode,
    )
