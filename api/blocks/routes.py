from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from api.core.db import get_or_404, get_session
from api.core.errors import AppError
from api.core.models import Block, Page
from api.core.ordering import renumber
from api.core.schemas import BlockCreate, BlockMove, BlockOut, BlockPatch, DocumentOut
from api.tables.validate import validate_csv

router = APIRouter(tags=["blocks"])


def _check_table(block: Block) -> None:
    if block.type == "table":
        if block.table_csv is None:
            raise AppError(422, "A table block needs table_csv.")
        block.flags = validate_csv(block.table_csv)
    else:
        block.table_csv = None
        block.flags = []


@router.post("/pages/{page_id}/blocks", status_code=status.HTTP_201_CREATED)
def create_block(page_id: str, body: BlockCreate, session: Session = Depends(get_session)) -> BlockOut:
    page = get_or_404(session, Page, page_id)
    block = Block(type=body.type, text=body.text, level=body.level, table_csv=body.table_csv)
    _check_table(block)
    page.blocks.append(block)
    renumber(page.blocks, block, body.position)
    session.commit()
    return BlockOut.model_validate(block)


@router.patch("/blocks/{block_id}")
def update_block(block_id: str, body: BlockPatch, session: Session = Depends(get_session)) -> BlockOut:
    block = get_or_404(session, Block, block_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(block, field, value)
    _check_table(block)
    session.commit()
    return BlockOut.model_validate(block)


@router.post("/blocks/{block_id}/move")
def move_block(block_id: str, body: BlockMove, session: Session = Depends(get_session)) -> DocumentOut:
    block = get_or_404(session, Block, block_id)
    source = block.page
    target = get_or_404(session, Page, body.page_id)
    if target.document_id != source.document_id:
        raise AppError(422, "Blocks can only move within their own document.")
    if target is not source:
        block.page = target
        renumber(source.blocks)
    renumber(target.blocks, block, body.position)
    session.commit()
    return DocumentOut.build(target.document)


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: str, session: Session = Depends(get_session)) -> Response:
    block = get_or_404(session, Block, block_id)
    page = block.page
    page.blocks.remove(block)
    session.delete(block)
    renumber(page.blocks)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
