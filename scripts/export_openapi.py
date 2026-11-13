"""Writes contracts/openapi.json from the FastAPI app; the web client types are generated from it."""

import json
from pathlib import Path

from api.main import create_app

if __name__ == "__main__":
    target = Path("contracts/openapi.json")
    target.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", "utf-8")
    print(f"Wrote {target}")
