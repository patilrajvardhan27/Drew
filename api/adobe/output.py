import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

STRUCTURED_DATA = "structuredData.json"


@dataclass
class ExtractOutput:
    """The parts of an Extract result Redraft uses: the element JSON and table CSVs."""

    data: dict
    tables: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_zip(cls, raw: bytes) -> "ExtractOutput":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            data = json.loads(archive.read(STRUCTURED_DATA))
            tables = {
                name: archive.read(name).decode("utf-8-sig")
                for name in archive.namelist()
                if name.startswith("tables/") and name.endswith(".csv")
            }
        return cls(data=data, tables=tables)

    @classmethod
    def from_dir(cls, root: Path) -> "ExtractOutput":
        data = json.loads((root / STRUCTURED_DATA).read_text("utf-8"))
        tables = {
            f"tables/{path.name}": path.read_text("utf-8-sig")
            for path in sorted((root / "tables").glob("*.csv"))
        }
        return cls(data=data, tables=tables)

    def to_dir(self, root: Path) -> None:
        (root / "tables").mkdir(parents=True, exist_ok=True)
        (root / STRUCTURED_DATA).write_text(json.dumps(self.data), "utf-8")
        for name, text in self.tables.items():
            (root / "tables" / Path(name).name).write_text(text, "utf-8")
