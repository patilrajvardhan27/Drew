# Redraft for Adobe Express

A panel add-on that imports a Redraft export into the open Express document as editable pages.

## How it works

1. In Redraft, open a document and choose **Create Express link**. The link is signed and valid for 15 minutes.
2. Paste it into this panel and choose **Import PDF**.
3. The panel downloads the export from Redraft (one HTML to PDF transaction) and calls `addOnUISdk.app.document.importPdf`.

The panel accepts only Redraft export links, so it never fetches arbitrary URLs. No login cookie is involved: add-ons run in a third-party iframe, so access is carried by the link's signature.

## Running it in Express

1. Turn on add-on development in Express: open [Adobe Express](https://new.express.adobe.com), go to **Settings**, then **Add-on development**, and switch it on. Accept the developer terms if asked.
2. Install and start the dev server:

   ```bash
   cd express-addon
   npm install
   npm run start
   ```

   It serves the panel at https://localhost:5241 with a local certificate. The first run asks to trust that certificate.
3. In Express, open a document, choose **Add-ons**, then **Your add-ons**, enable **Add-on testing**, and connect to `https://localhost:5241`.
4. Start Redraft as usual. If Redraft runs on another machine or behind HTTPS, links must use `https`.

The export route accepts calls from any origin, because the link's signature is its only credential and it never reads cookies; nothing needs configuring for Adobe's add-on hosts. It also exposes the download name, which becomes the imported document's title. Set `REDRAFT_SECRET_KEY` so links keep working after a restart.

## Tests

```bash
npm test
```

The link checks run with Node's built-in test runner; nothing needs installing.

## Publishing

`npm run package` builds a zip for the Express add-on marketplace. Before submitting, add icons and a listing, and point it at a public HTTPS deployment of Redraft.
