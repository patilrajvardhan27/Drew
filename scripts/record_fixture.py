"""Runs one real Extract call and saves the result as a test fixture.

Usage: REDRAFT_ADOBE_CLIENT_ID=... REDRAFT_ADOBE_CLIENT_SECRET=... \
       python -m scripts.record_fixture web/public/sample.pdf tests/fixtures/extract

Costs Extract transactions, so run it only when the fixture needs refreshing.
"""

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from api.adobe.provider import LiveAdobe
from api.core.config import get_settings
from api.core.db import get_engine, init_db
from api.documents.service import count_pages


def main(source: str, target: str) -> None:
    settings = get_settings()
    raw = Path(source).read_bytes()
    init_db()
    with Session(get_engine()) as session:
        output, cost = LiveAdobe(settings).extract(session, raw, count_pages(raw, settings))
    output.to_dir(Path(target))
    print(f"Saved {len(output.data.get('elements', []))} elements to {target} ({cost} transactions)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
