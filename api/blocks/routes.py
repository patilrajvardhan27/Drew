from fastapi import APIRouter, Depends, status

from api.core.errors import AppError
from api.core.models import Block
from api.core.ordering import by_position, renumber
from api.core.schemas import BlockCreate, BlockMove, BlockOut, BlockPatch, BlockSplit, DocumentOut
from api.history.context import Edit, edit_context
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
def create_block(page_id: str, body: BlockCreate, edit: Edit = Depends(edit_context)) -> BlockOut:
    page = edit.page(page_id)
    block = Block(type=body.type, text=body.text, level=body.level, table_csv=body.table_csv)
    _check_table(block)
    edit.record(page.document)
    page.blocks.append(block)
    renumber(page.blocks, block, body.position)
    edit.session.commit()
    return BlockOut.model_validate(block)


@router.patch("/blocks/{block_id}")
def update_block(block_id: str, body: BlockPatch, edit: Edit = Depends(edit_context)) -> BlockOut:
    block = edit.block(block_id)
    edit.record(block.page.document, key=f"edit:{block.id}")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(block, field, value)
    _check_table(block)
    edit.session.commit()
    return BlockOut.model_validate(block)


@router.post("/blocks/{block_id}/move")
def move_block(block_id: str, body: BlockMove, edit: Edit = Depends(edit_context)) -> DocumentOut:
    block = edit.block(block_id)
    source = block.page
    target = edit.page(body.page_id)
    if target.document_id != source.document_id:
        raise AppError(422, "Blocks can only move within their own document.")
    edit.record(source.document)
    if target is not source:
        block.page = target
        renumber(source.blocks)
    renumber(target.blocks, block, body.position)
    edit.session.commit()
    return DocumentOut.build(target.document)


@router.post("/blocks/{block_id}/split")
def split_block(block_id: str, body: BlockSplit, edit: Edit = Depends(edit_context)) -> DocumentOut:
    block = edit.block(block_id)
    text = block.text if body.text is None else body.text
    if block.type == "table":
        raise AppError(422, "Tables cannot be split.")
    if body.offset >= len(text):
        raise AppError(422, "Place the cursor inside the text to split it.")
    edit.record(block.page.document)
    block.text = text[: body.offset].rstrip()
    tail = Block(type=block.type, level=block.level, text=text[body.offset :].lstrip(), flags=[])
    block.page.blocks.append(tail)
    renumber(block.page.blocks, tail, block.position + 1)
    edit.session.commit()
    return DocumentOut.build(block.page.document)


@router.post("/blocks/{block_id}/merge")
def merge_block(block_id: str, edit: Edit = Depends(edit_context)) -> DocumentOut:
    """Join this block onto the end of the block above it on the same page."""
    block = edit.block(block_id)
    page = block.page
    siblings = by_position(page.blocks)
    index = siblings.index(block)
    if index == 0:
        raise AppError(422, "The first block on a page has nothing above it to merge into.")
    above = siblings[index - 1]
    if "table" in (above.type, block.type):
        raise AppError(422, "Tables cannot be merged.")
    edit.record(page.document)
    above.text = f"{above.text}{JOINERS[above.type]}{block.text}".strip()
    page.blocks.remove(block)
    edit.session.delete(block)
    renumber(page.blocks)
    edit.session.commit()
    return DocumentOut.build(page.document)


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: str, edit: Edit = Depends(edit_context)) -> None:
    block = edit.block(block_id)
    page = block.page
    edit.record(page.document)
    page.blocks.remove(block)
    edit.session.delete(block)
    renumber(page.blocks)
    edit.session.commit()
