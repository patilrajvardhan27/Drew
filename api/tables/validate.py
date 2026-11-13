import csv
import io
import re

import pandas as pd

NUMBER_NOISE = re.compile(r"[,\s$€£%()]")
MIXED_THRESHOLD = 0.5


def parse_rows(text: str) -> list[list[str]]:
    return [row for row in csv.reader(io.StringIO(text.lstrip("﻿"))) if any(c.strip() for c in row)]


def validate_csv(text: str) -> list[str]:
    """Return human-readable problems with an extracted table; empty means it looks sound."""
    rows = parse_rows(text)
    if not rows:
        return ["Table is empty"]

    flags: list[str] = []
    widths = {len(row) for row in rows}
    if len(widths) > 1:
        flags.append(f"Rows have different column counts ({min(widths)} to {max(widths)})")

    header = rows[0]
    if any(not cell.strip() for cell in header):
        flags.append("Header row has empty cells")
    if header and all(_numeric(pd.Series(header)).notna()):
        flags.append("First row looks like data, not a header")

    width = max(widths)
    names = [cell.strip() or f"Column {i + 1}" for i, cell in enumerate(header + [""] * width)][:width]
    body = pd.DataFrame([row + [""] * (width - len(row)) for row in rows[1:]], columns=range(width))
    for index, name in enumerate(names):
        values = body[index].astype(str).str.strip()
        values = values[values != ""]
        if values.empty:
            continue
        ratio = _numeric(values).notna().mean()
        if MIXED_THRESHOLD <= ratio < 1:
            flags.append(f"Column '{name}' mixes numbers and text")
    return flags


def _numeric(values: pd.Series) -> pd.Series:
    cleaned = values.astype(str).str.replace(NUMBER_NOISE, "", regex=True)
    return pd.to_numeric(cleaned.where(cleaned != ""), errors="coerce")
