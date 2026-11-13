"""Renders each uploaded page to a PNG locally, so the side-by-side view costs no Adobe transactions."""

from pathlib import Path

import pypdfium2 as pdfium

from api.core.config import Settings

# 612pt wide letter pages render about 900px wide: sharp next to the blocks, small on disk.
SCALE = 1.5


def page_image_path(settings: Settings, sha: str, index: int) -> Path:
    return settings.cache_dir / sha / "pages" / f"{index}.png"


def render_pages(raw: bytes, target: Path) -> None:
    if target.is_dir():
        return
    target.mkdir(parents=True)
    pdf = pdfium.PdfDocument(raw)
    try:
        for index in range(len(pdf)):
            image = pdf[index].render(scale=SCALE).to_pil()
            image.save(target / f"{index}.png", optimize=True)
    finally:
        pdf.close()
