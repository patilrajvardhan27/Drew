from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from api.core.models import Document
from api.core.ordering import by_position
from api.tables.validate import parse_rows

HERE = Path(__file__).parent
env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html", "j2"]))


def page_view(page) -> list[dict]:
    view = []
    for block in by_position(page.blocks):
        item = {"type": block.type, "level": min(max(block.level, 1), 3), "text": block.text}
        if block.type == "list":
            item["items"] = [line for line in block.text.splitlines() if line.strip()]
        if block.type == "table":
            rows = parse_rows(block.table_csv or "")
            item["header"], item["rows"] = (rows[0], rows[1:]) if rows else ([], [])
        view.append(item)
    return view


def render_html(doc: Document) -> str:
    """One self-contained HTML file; the browser preview and the Adobe export both use it."""
    css = (HERE / "print.css").read_text("utf-8")
    pages = [page_view(page) for page in by_position(doc.pages)]
    return env.get_template("document.html.j2").render(title=doc.name, css=css, pages=pages)
