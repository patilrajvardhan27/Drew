# Redraft

Redraft turns a PDF into editable blocks, lets you drag and rewrite them, add Copyright, Privacy and Terms pages, and exports a clean PDF. Adobe PDF Extract does the reading and Adobe HTML to PDF does the writing.

Independent project. Not affiliated with Adobe.

## How it works

1. **Upload.** The API checks the file is a real PDF (magic bytes, 20 MB, 50 pages), hashes it and looks for a cached Extract result.
2. **Extract.** On a cache miss, Adobe PDF Extract returns headings, paragraphs, lists and tables in reading order. Tables come back as CSV.
3. **Validate tables.** pandas checks each table for a header row, consistent column counts and columns that mix numbers with text. Problems show as flags on the block.
4. **Edit.** Drag blocks within or across pages (mouse or keyboard), click to rewrite, delete and undo, edit table cells.
5. **Add pages.** Insert a Copyright, Privacy Policy, Terms of Service or blank page anywhere. Templates are filled from a short form.
6. **Export.** One Jinja2 template and print stylesheet render the document. The browser preview and the Adobe export use the same HTML, so they match.

## Staying inside the free tier

Adobe's free tier allows 500 document transactions a month and 25 requests a minute.

| Limit | Handling |
| --- | --- |
| Extract costs 1 transaction per 5 pages | Results are cached by SHA-256, so re-uploads cost nothing |
| HTML to PDF costs 1 per 50 pages | Export runs only on click; the preview is rendered locally |
| 25 requests a minute | Every call goes through one client with a queue and backoff on 429 |
| 500 a month | Extract is refused at 450 so there is always room to export |

All Adobe calls live in `api/adobe/client.py`.

## Running locally

Offline mode needs no Adobe account: every upload replays the recorded sample in `tests/fixtures/extract`, and export is turned off.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r api/requirements-dev.txt
cp .env.example .env
uvicorn api.main:app --reload
```

```bash
npm --prefix web install
npm --prefix web run dev
```

Open http://localhost:5173. For real extraction, create free credentials in the Adobe Developer Console, set `REDRAFT_ADOBE_MODE=live` and fill in the client ID and secret in `.env`. They are read on the server only.

To run everything in one container instead:

```bash
docker compose up --build
```

## Checks

```bash
PYTHON=.venv/bin/python ./scripts/verify.sh
```

This runs the 250-line limit, ruff, pytest, the API contract drift check, TypeScript, Vitest, a production build and Playwright with axe on desktop and phone sizes.

## Layout

```
api/
  adobe/      client.py (queue, retry, budget), extract.py, html_to_pdf.py, provider.py
  blocks/     mapping.py (Extract JSON to blocks), routes.py
  documents/  upload, cache and ingest
  pages/      legal templates and routes
  tables/     validate.py (pandas checks)
  export/     render.py, document.html.j2, print.css
  core/       config, db, models, schemas, usage, ordering, cleanup
web/src/
  features/   upload, editor, pages, export
  shared/     ui, hooks (useDocument, useBlocks), api (generated types)
  theme/      tokens.css
contracts/    openapi.json, generated from the API
tests/        pytest suite and recorded Extract fixtures
scripts/      verify.sh, check-file-length.mjs, record_fixture.py
```

## Privacy

Uploaded PDFs are not stored. Extracted text, edits and cached Extract results are deleted after 24 hours by a background job, and document text is never logged.

## License

MIT
