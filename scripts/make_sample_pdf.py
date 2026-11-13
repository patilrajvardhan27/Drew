"""Writes web/public/sample.pdf: a two-page report with headings, a list and a table.

Built from raw PDF operators so it needs no extra packages. Run from the repo root.
"""

from pathlib import Path

PAGES = [
    [
        (72, 700, 26, "Northwind Field Report"),
        (72, 660, 16, "Summary"),
        (72, 636, 11, "Field teams visited 42 sites this quarter and closed 18 open requests."),
        (72, 620, 11, "Response times improved in every region except the coast."),
        (72, 584, 16, "Highlights"),
        (84, 560, 11, "- New intake form cut paperwork by a third."),
        (84, 544, 11, "- Two regional depots now share one parts inventory."),
        (84, 528, 11, "- Safety audits passed with no critical findings."),
        (72, 492, 11, "The full regional breakdown follows on the next page."),
    ],
    [
        (72, 700, 16, "Regional figures"),
        (72, 670, 11, "Region        Q1 visits    Q2 visits    Notes"),
        (72, 652, 11, "North         12           15           Stable"),
        (72, 634, 11, "Coast         9            n/a          Storm closures"),
        (72, 616, 11, "Valley        14           17           New depot"),
        (72, 580, 11, "Figures are counted at the close of each quarter."),
    ],
]


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build() -> bytes:
    objects: list[bytes] = []
    page_ids = [3 + 2 * i for i in range(len(PAGES))]
    font_id = 3 + 2 * len(PAGES)

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(PAGES)} >>".encode())
    for index, lines in enumerate(PAGES):
        stream = "".join(
            f"BT /F1 {size} Tf {x} {y} Td ({escape(text)}) Tj ET\n" for x, y, size, text in lines
        ).encode()
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {page_ids[index] + 1} 0 R >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


if __name__ == "__main__":
    target = Path("web/public/sample.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(build())
    print(f"Wrote {target}")
