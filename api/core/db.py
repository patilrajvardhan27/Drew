from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session

from api.core.config import get_settings
from api.core.errors import NotFound


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = get_settings().database_url
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            if url.startswith("sqlite:///"):
                Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(url, connect_args=connect_args)
    return _engine


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db() -> None:
    from api.core import models  # noqa: F401  registers the tables

    engine = get_engine()
    Base.metadata.create_all(engine)
    add_missing_columns(engine)


def add_missing_columns(engine: Engine) -> None:
    """create_all skips existing tables, so new nullable or defaulted columns are added here."""
    existing = inspect(engine)
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if not existing.has_table(table.name):
                continue
            present = {column["name"] for column in existing.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                kind = column.type.compile(engine.dialect)
                default = (
                    column.default.arg if column.default is not None and column.default.is_scalar else None
                )
                clause = f" DEFAULT {default!r}" if default is not None else ""
                connection.execute(
                    text(f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {kind}{clause}')
                )


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


def get_or_404[Model: Base](session: Session, model: type[Model], key: str) -> Model:
    row = session.get(model, key)
    if row is None:
        raise NotFound(model.__name__)
    return row
