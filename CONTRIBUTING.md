# Contributing

## Ground rules

- **One source of truth for the API.** The Pydantic schemas in `api/core/schemas.py` define the contract. After changing them, run `python -m scripts.export_openapi` and `npm --prefix web run gen:api`, and commit both outputs. CI fails if they drift. Never edit `schema.d.ts` by hand.
- **250 lines per file.** `scripts/check-file-length.mjs` enforces it. Split by responsibility at about 200.
- **No repeated logic.** Adobe calls go through `api/adobe/client.py`. Position bookkeeping goes through `api/core/ordering.py`. Block changes in the UI go through `useBlocks`. Reuse `shared/ui` before adding a component. Anything used twice moves to `core/` or `shared/` in the same change.
- **Tests ship with the code.** pytest with recorded Extract fixtures (no Adobe key in CI), Vitest for hooks, Playwright with axe for every page.
- **Security.** Credentials come from environment variables only. Uploads are checked by magic bytes and size. Nothing older than 24 hours is kept. Document text never goes into logs.
- **Budget.** Extract is refused at 450 transactions a month. Extract results are cached by file hash.
- **Design.** Follow `docs/design.md`. Skeleton loaders on every async view, no icon libraries, no hover animations.
- **Legal templates** always carry "Template text. Not legal advice."
- **Access.** Load documents, pages and blocks through `api/auth/access.py` so ownership is checked in one place.
- **Undo.** Any route that changes a document calls `history.record` first.

## Refreshing the Extract fixture

```bash
REDRAFT_ADOBE_CLIENT_ID=... REDRAFT_ADOBE_CLIENT_SECRET=... \
  python -m scripts.record_fixture web/public/sample.pdf tests/fixtures/extract
```

This spends one transaction. Regenerate the sample PDF with `python scripts/make_sample_pdf.py`.

## Before opening a pull request

Run `./scripts/verify.sh`. Keep commits small and focused.
