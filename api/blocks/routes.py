from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from api.auth.access import block_for, page_for
from api.auth.sessions import optional_user
from api.core.db import get_session
from api.core.errors import AppError
from api.core.models import Block, User
from api.core.ordering import by_position, renumber
from api.core.schemas import BlockCreate, BlockMove, BlockOut, BlockPatch, BlockSplit, DocumentOut
from api.history.service import record
from api.tables.validate import validate_csv

router = APIRouter(tags=["blocks"])
JOINERS = {"list": "\n", "heading": " ", "paragraph": " "}


def _check_table(block: Block) -> None:
    if block.type == "table":
        if block.table_csv is None:
            raise AppError(422, "A table block needs table_csv.")
        block.flags = validate_csv(block.table_csv)
    else:
        block.table_csv = None
        block.flags = []


@router.post("/pages/{page_id}/blocks", status_code=status.HTTP_201_CREATED)
def create_block(
    page_id: str,
    body: BlockCreate,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> BlockOut:
    page = page_for(session, page_id, user)
    record(session, page.document)
    block = Block(type=body.type, text=body.text, level=body.level, table_csv=body.table_csv)
    _check_table(block)
    page.blocks.append(block)
    renumber(page.blocks, block, body.position)
    session.commit()
    return BlockOut.model_validate(block)


@router.patch("/blocks/{block_id}")
def update_block(
    block_id: str,
    body: BlockPatch,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> BlockOut:
    block = block_for(session, block_id, user)
    record(session, block.page.document, key=f"edit:{block.id}")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(block, field, value)
    _check_table(block)
    session.commit()
    return BlockOut.model_validate(block)


@router.post("/blocks/{block_id}/move")
def move_block(
    block_id: str,
    body: BlockMove,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    block = block_for(session, block_id, user)
    source = block.page
    target = page_for(session, body.page_id, user)
    if target.document_id != source.document_id:
        raise AppError(422, "Blocks can only move within their own document.")
    record(session, source.document)
    if target is not source:
        block.page = target
        renumber(source.blocks)
    renumber(target.blocks, block, body.position)
    session.commit()
    return DocumentOut.build(target.document)


@router.post("/blocks/{block_id}/split")
def split_block(
    block_id: str,
    body: BlockSplit,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    block = block_for(session, block_id, user)
    text = block.text if body.text is None else body.text
    if block.type == "table":
        raise AppError(422, "Tables cannot be split.")
    if body.offset >= len(text):
        raise AppError(422, "Place the cursor inside the text to split it.")
    record(session, block.page.document)
    block.text = text[: body.offset].rstrip()
    tail = Block(type=block.type, level=block.level, text=text[body.offset :].lstrip(), flags=[])
    block.page.blocks.append(tail)
    renumber(block.page.blocks, tail, block.position + 1)
    session.commit()
    return DocumentOut.build(block.page.document)


@router.post("/blocks/{block_id}/merge")
def merge_block(
    block_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> DocumentOut:
    """Join this block onto the end of the block above it on the same page."""
    block = block_for(session, block_id, user)
    page = block.page
    siblings = by_position(page.blocks)
    index = siblings.index(block)
    if index == 0:
        raise AppError(422, "The first block on a page has nothing above it to merge into.")
    above = siblings[index - 1]
    if "table" in (above.type, block.type):
        raise AppError(422, "Tables cannot be merged.")
    record(session, page.document)
    above.text = f"{above.text}{JOINERS[above.type]}{block.text}".strip()
    page.blocks.remove(block)
    session.delete(block)
    renumber(page.blocks)
    session.commit()
    return DocumentOut.build(page.document)


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(
    block_id: str,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> Response:
    block = block_for(session, block_id, user)
    page = block.page
    record(session, page.document)
    page.blocks.remove(block)
    session.delete(block)
    renumber(page.blocks)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
