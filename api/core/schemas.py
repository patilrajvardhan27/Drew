from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.core.models import Document
from api.core.ordering import by_position

BlockType = Literal["heading", "paragraph", "list", "table"]
PageKind = Literal["extracted", "copyright", "privacy", "terms", "blank"]
LegalKind = Literal["copyright", "privacy", "terms"]


class BlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    page_id: str
    type: BlockType
    level: int
    text: str
    position: int
    table_csv: str | None
    flags: list[str]


class PageOut(BaseModel):
    id: str
    kind: PageKind
    position: int
    source_index: int | None
    blocks: list[BlockOut]


class DocumentOut(BaseModel):
    id: str
    name: str
    sha256: str
    created_at: datetime
    transactions_used: int
    owned: bool
    can_undo: bool
    revision: int
    pages: list[PageOut]

    @classmethod
    def build(cls, doc: Document) -> "DocumentOut":
        pages = [
            PageOut(
                id=page.id,
                kind=page.kind,
                position=page.position,
                source_index=page.source_index,
                blocks=[BlockOut.model_validate(b) for b in by_position(page.blocks)],
            )
            for page in by_position(doc.pages)
        ]
        return cls(
            id=doc.id,
            name=doc.name,
            sha256=doc.sha256,
            created_at=doc.created_at,
            transactions_used=doc.transactions_used,
            owned=doc.owner_id is not None,
            can_undo=doc.undo_depth > 0,
            revision=doc.revision,
            pages=pages,
        )


class BlockCreate(BaseModel):
    type: BlockType
    text: str = ""
    level: int = Field(default=0, ge=0, le=6)
    table_csv: str | None = None
    position: int = Field(default=0, ge=0)


class BlockPatch(BaseModel):
    text: str | None = None
    level: int | None = Field(default=None, ge=0, le=6)
    table_csv: str | None = None


class BlockSplit(BaseModel):
    offset: int = Field(gt=0)
    # The editor sends its unsaved draft so a split never races the debounced save.
    text: str | None = None


class BlockMove(BaseModel):
    page_id: str
    position: int = Field(ge=0)


class LegalDetails(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    email: EmailStr
    effective_date: date
    jurisdiction: str = Field(min_length=1, max_length=120)


class PageCreate(BaseModel):
    kind: Literal["copyright", "privacy", "terms", "blank"]
    position: int = Field(ge=0)
    details: LegalDetails | None = None


class UsageOut(BaseModel):
    month: str
    used: int
    limit: int
    extract_cap: int
    remaining: int
    mode: Literal["live", "fixture"]


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=200)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str


class DocumentSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    page_count: int


class ExpressLink(BaseModel):
    url: str
    expires_at: datetime
