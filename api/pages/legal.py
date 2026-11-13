from pathlib import Path

from api.blocks.mapping import MappedBlock
from api.core.schemas import LegalDetails, LegalKind

TEMPLATES = Path(__file__).parent / "templates"
NOTE = "Template text. Not legal advice. Review before publishing."


def fill(kind: LegalKind, details: LegalDetails) -> str:
    text = (TEMPLATES / f"{kind}.md").read_text("utf-8")
    day = details.effective_date
    values = {
        "company": details.company,
        "email": details.email,
        "effective_date": f"{day:%B} {day.day}, {day.year}",
        "year": str(details.effective_date.year),
        "jurisdiction": details.jurisdiction,
    }
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def markdown_blocks(text: str) -> list[MappedBlock]:
    """Read the small Markdown subset the templates use: #/## headings, - lists, paragraphs."""
    blocks: list[MappedBlock] = []
    for chunk in (part.strip() for part in text.split("\n\n")):
        if not chunk:
            continue
        if chunk.startswith("#"):
            marks, _, title = chunk.partition(" ")
            blocks.append(MappedBlock("heading", title.strip(), level=len(marks)))
        elif chunk.startswith("- "):
            items = [line.removeprefix("- ").strip() for line in chunk.splitlines()]
            blocks.append(MappedBlock("list", "\n".join(items)))
        else:
            blocks.append(MappedBlock("paragraph", " ".join(chunk.split())))
    return blocks


def legal_blocks(kind: LegalKind, details: LegalDetails) -> list[MappedBlock]:
    blocks = markdown_blocks(fill(kind, details))
    note = MappedBlock("paragraph", NOTE)
    return blocks[:1] + [note] + blocks[1:]
