from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.db import Base


def new_id() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column()
    user: Mapped[User] = relationship()


class AuthAttempt(Base):
    """Failed sign-ins and reset requests, counted per email to slow down guessing."""

    __tablename__ = "auth_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    at: Mapped[datetime] = mapped_column(default=utcnow, index=True)


class PasswordReset(Base):
    __tablename__ = "password_resets"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column()
    user: Mapped[User] = relationship()


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    transactions_used: Mapped[int] = mapped_column(default=0)
    # Owned documents survive the 24 hour purge; anonymous ones do not.
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    undo_depth: Mapped[int] = mapped_column(default=0)
    # Bumped on every change so a stale tab cannot overwrite newer work.
    revision: Mapped[int] = mapped_column(default=0)
    pages: Mapped[list["Page"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    history: Mapped[list["HistoryEntry"]] = relationship(cascade="all, delete-orphan", lazy="noload")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16), default="extracted")
    position: Mapped[int] = mapped_column(default=0)
    # Index of the page in the uploaded PDF, used to show the original next to the blocks.
    source_index: Mapped[int | None] = mapped_column(default=None)
    document: Mapped[Document] = relationship(back_populates="pages")
    blocks: Mapped[list["Block"]] = relationship(back_populates="page", cascade="all, delete")


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    page_id: Mapped[str] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(16))
    level: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(default=0)
    table_csv: Mapped[str | None] = mapped_column(Text, default=None)
    flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    page: Mapped[Page] = relationship(back_populates="blocks")


class HistoryEntry(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    key: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    pages: Mapped[list[dict]] = mapped_column(JSON)


class UsageMonth(Base):
    __tablename__ = "usage_months"

    month: Mapped[str] = mapped_column(String(7), primary_key=True)
    transactions: Mapped[int] = mapped_column(default=0)
