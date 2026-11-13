"""Turns Adobe Extract's element list into pages of editable blocks.

Extract paths look like //Document/H1, //Document/P[3]/Sub[2], //Document/L[2]/LI[4]/LBody
or //Document/Table[1]. Cell text inside a table also arrives as separate elements; those
are skipped because the table's CSV rendition already carries it.
"""

import re
from dataclasses import dataclass, field

from api.adobe.output import ExtractOutput

HEADING = re.compile(r"/(Title|H(\d))(?:\[\d+\])?$")
LIST_BODY = re.compile(r"^(.*/L(?:\[\d+\])?)/LI(?:\[\d+\])?/LBody")
LIST_LABEL = re.compile(r"/Lbl(?:\[\d+\])?$")
TABLE = re.compile(r"/Table(?:\[\d+\])?$")
INSIDE_TABLE = re.compile(r"/Table(?:\[\d+\])?/")
FRAGMENT = re.compile(r"/(?:Sub|Span|StyleSpan)(?:\[\d+\])?$")


@dataclass
class MappedBlock:
    type: str
    text: str = ""
    level: int = 0
    table_csv: str | None = None
    key: str = field(default="", repr=False)


def map_extract(output: ExtractOutput) -> list[list[MappedBlock]]:
    elements = output.data.get("elements", [])
    page_count = max((el.get("Page", 0) for el in elements), default=-1) + 1
    pages: list[list[MappedBlock]] = [[] for _ in range(page_count)]

    for element in elements:
        path = element.get("Path", "")
        blocks = pages[element.get("Page", 0)]
        if INSIDE_TABLE.search(path) or LIST_LABEL.search(path):
            continue
        if TABLE.search(path):
            csv = _table_csv(element, output.tables)
            if csv is not None:
                blocks.append(MappedBlock("table", table_csv=csv, key=path))
            continue
        text = (element.get("Text") or "").strip()
        if text:
            _append_text(blocks, path, text)
    return pages


def _table_csv(element: dict, tables: dict[str, str]) -> str | None:
    return next((tables[p] for p in element.get("filePaths", []) if p in tables), None)


def _append_text(blocks: list[MappedBlock], path: str, text: str) -> None:
    previous = blocks[-1] if blocks else None

    list_match = LIST_BODY.search(path)
    if list_match:
        key = list_match.group(1)
        if previous and previous.type == "list" and previous.key == key:
            previous.text += "\n" + text
        else:
            blocks.append(MappedBlock("list", text, key=key))
        return

    heading = HEADING.search(path)
    if heading:
        level = 1 if heading.group(1) == "Title" else int(heading.group(2))
        blocks.append(MappedBlock("heading", text, level=min(level, 6), key=path))
        return

    key = FRAGMENT.sub("", path)
    if previous and previous.type == "paragraph" and previous.key == key:
        previous.text += " " + text
    else:
        blocks.append(MappedBlock("paragraph", text, key=key))
