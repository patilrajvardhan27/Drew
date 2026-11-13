# Redraft

Redraft turns a PDF into editable blocks, lets you drag and rewrite them, add Copyright, Privacy and Terms pages, and exports a clean PDF. Adobe PDF Extract does the reading and Adobe HTML to PDF does the writing. A companion Adobe Express add-on brings the result into Express as editable pages.

Independent project. Not affiliated with Adobe.

## How it works

1. **Upload.** The API checks the file is a real PDF (magic bytes, 20 MB, 50 pages), hashes it and looks for a cached Extract result. Each page is also rendered to a PNG locally for the side-by-side view.
2. **Extract.** On a cache miss, Adobe PDF Extract returns headings, paragraphs, lists and tables in reading order. Tables come back as CSV.
3. **Validate tables.** pandas checks each table for a header row, consistent column counts and columns that mix numbers with text. Problems show as flags on the block.
4. **Edit.** Drag blocks within or across pages (mouse or keyboard), click to rewrite, split a block at the cursor, merge a block into the one above, edit table cells. Every change can be undone with Ctrl+Z or Cmd+Z, even after a reload.
5. **Compare.** Show original puts each uploaded page next to its blocks.
6. **Add pages.** Insert a Copyright, Privacy Policy, Terms of Service or blank page anywhere. Templates are filled from a short form.
7. **Export.** One Jinja2 template and print stylesheet render the document. The browser preview and the Adobe export use the same HTML, so they match.
8. **Keep or send.** Sign in to keep documents past 24 hours, or create a 15 minute link that the Express add-on imports.

## Adobe credentials

Redraft runs without Adobe in offline mode, where every upload replays a recorded sample and export is off. For real PDFs you need free PDF Services credentials. They live only in a `.env` file on your machine, which git ignores.

1. Sign in at the [Adobe Developer Console](https://developer.adobe.com/console) with any Adobe ID.
2. Choose **Create new project**, then **Add API**, pick **PDF Services API**, and select **OAuth Server-to-Server** when asked for a credential type.
3. Open the project's **OAuth Server-to-Server** credential and copy the **Client ID**, then **Retrieve client secret** and copy that too.
4. In the repo root, copy the template and fill it in:

   ```bash
   cp .env.example .env
   ```

   ```
   REDRAFT_ADOBE_MODE=live
   REDRAFT_ADOBE_CLIENT_ID=your-client-id
   REDRAFT_ADOBE_CLIENT_SECRET=your-client-secret
   REDRAFT_SECRET_KEY=any-long-random-string
   ```

   Adobe's own variable names, `PDF_SERVICES_CLIENT_ID` and `PDF_SERVICES_CLIENT_SECRET`, also work, so you can export them in your shell profile instead of using `.env`.
5. Check them without spending a transaction:

   ```bash
   python -m scripts.check_adobe
   ```

The server reads `.env` from the repo root wherever it is started from. The credentials are never sent to the browser. If they leak, rotate the secret in the console. The free tier allows 500 transactions a month.

## Staying inside the free tier

| Limit | Handling |
| --- | --- |
| Extract costs 1 transaction per 5 pages | Results are cached by SHA-256, so re-uploads cost nothing |
| HTML to PDF costs 1 per 50 pages | Export runs only on click; the preview is rendered locally |
| Original page images | Rendered locally with PDFium, so they cost nothing |
| 25 requests a minute | Every call goes through one client with a queue and backoff on 429 |
| 500 a month | Extract is refused at 450 so there is always room to export |

All Adobe calls live in `api/adobe/client.py`.

## Running locally

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

Open http://localhost:5173. To run everything in one container instead:

```bash
docker compose up --build
```

## Accounts

Anyone can use Redraft without an account; those documents are deleted 24 hours after upload and are reachable by anyone holding the link. Signed-in uploads, and documents claimed with **Keep it in my account**, stay until deleted and are visible only to their owner.

- Passwords are hashed with scrypt and sessions are HttpOnly cookies. Set `REDRAFT_SECURE_COOKIES=true` when serving over HTTPS.
- Five failed sign-ins lock an email for 15 minutes. Attempts are stored in the database, so the lock holds across restarts and several server processes.
- **Forgot your password?** emails a one-hour, single-use link. Choosing a new password signs out every other device. The answer is the same whether or not the email has an account.

Email is sent according to `REDRAFT_MAIL_BACKEND`: `log` prints it in the server output, `file` writes it to `data/files/mail/`, and `smtp` sends it through the server in `REDRAFT_SMTP_*`. Use `smtp` anywhere real, and set `REDRAFT_PUBLIC_URL` so links point at the public address.

## Editing from two tabs

Every document carries a revision number that each change moves forward. The editor sends the revision it last saw, and the server refuses a change from a tab that has fallen behind. That tab then loads the newer version and says why, so one tab can never silently overwrite or undo work done in another.

## Adobe Express add-on

`express-addon/` is a small panel for Adobe Express. In Redraft, choose **Create Express link**, paste the link into the panel, and the export is imported with `importPdf` as editable pages. Setup is in [express-addon/README.md](express-addon/README.md).

## Checks

```bash
PYTHON=.venv/bin/python ./scripts/verify.sh
```

This runs the 250-line limit, ruff, pytest, the API contract drift check, the add-on tests, TypeScript, Vitest, a production build and Playwright with axe on desktop and phone sizes.

## Layout

```
api/
  adobe/      client.py (queue, retry, budget), extract.py, html_to_pdf.py, provider.py
  auth/       passwords, sessions, access checks, routes
  blocks/     mapping.py (Extract JSON to blocks), routes.py (edit, move, split, merge)
  documents/  upload, cache, page images, claim
  history/    snapshot undo
  pages/      legal templates, original page images
  tables/     validate.py (pandas checks)
  export/     render.py, document.html.j2, print.css, signed Express links
  core/       config, db, models, schemas, usage, ordering, cleanup
web/src/
  features/   upload, editor, pages, export, account
  shared/     ui, hooks (useDocument, useBlocks, useAuth), api (generated types)
  theme/      tokens.css
express-addon/  Adobe Express panel
contracts/      openapi.json, generated from the API
tests/          pytest suite and recorded Extract fixtures
scripts/        verify.sh, check-file-length.mjs, check_adobe.py, record_fixture.py
```

## Privacy

Uploaded PDFs are not stored. Extracted text, edits, page images and cached Extract results of anonymous documents are deleted after 24 hours by a background job. Document text is never logged.

## License

MIT
