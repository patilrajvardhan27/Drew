import type { ReactNode } from "react";

function Prose({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="prose">
      <h1>{title}</h1>
      {children}
    </article>
  );
}

export function TermsPage() {
  return (
    <Prose title="Terms of Service">
      <p>Redraft is a personal project offered as is, without warranties of any kind.</p>
      <h2>Your files</h2>
      <p>
        You must have the right to upload and edit the PDFs you send. You keep every right to your content; Redraft
        only processes it to show and export your edits.
      </p>
      <h2>Fair use</h2>
      <p>
        The service runs on a small monthly Adobe allowance. Uploads may be refused once it is spent, and automated or
        bulk use is not allowed.
      </p>
      <h2>Legal page templates</h2>
      <p>The Terms, Privacy and Copyright templates are starting points, not legal advice. Review them before use.</p>
    </Prose>
  );
}

export function PrivacyPage() {
  return (
    <Prose title="Privacy">
      <p>Redraft keeps as little as it can, for as short a time as it can.</p>
      <h2>What happens to an upload</h2>
      <ul>
        <li>The PDF is sent to Adobe PDF Services for extraction and is not stored by Redraft.</li>
        <li>The extracted text and your edits are stored for 24 hours, then deleted automatically.</li>
        <li>Document text is never written to logs and never used to train any model.</li>
      </ul>
      <h2>Adobe</h2>
      <p>
        Adobe processes files under its own terms for PDF Services. Redraft is an independent project and is not
        affiliated with Adobe.
      </p>
      <h2>No accounts, no tracking</h2>
      <p>There are no accounts, analytics or advertising cookies.</p>
    </Prose>
  );
}

export function CopyrightPage() {
  return (
    <Prose title="Copyright">
      <p>Copyright {new Date().getFullYear()} Redraft. The source code is published under the MIT License.</p>
      <p>
        Documents you upload remain the property of their owners. Adobe, Acrobat and PDF Services are trademarks of
        Adobe Inc., used here only to describe the APIs this project calls.
      </p>
      <p>
        If you believe content processed here infringes your rights, open an issue on the project repository and it
        will be removed.
      </p>
    </Prose>
  );
}
