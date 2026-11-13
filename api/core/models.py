from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.db import Base


def new_id() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    transactions_used: Mapped[int] = mapped_column(default=0)
    pages: Mapped[list["Page"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16), default="extracted")
    position: Mapped[int] = mapped_column(default=0)
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


class UsageMonth(Base):
    __tablename__ = "usage_months"

    month: Mapped[str] = mapped_column(String(7), primary_key=True)
    transactions: Mapped[int] = mapped_column(default=0)
