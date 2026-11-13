import { useState } from "react";
import { api, type ExpressLink } from "../../shared/api/client";
import { Button } from "../../shared/ui";

/** Creates a 15 minute link the Redraft add-on inside Adobe Express can import from. */
export function ExpressCard({ documentId }: { documentId: string }) {
  const [link, setLink] = useState<ExpressLink | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = async () => {
    setError(null);
    setCopied(false);
    try {
      setLink(await api.expressLink(documentId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the link.");
    }
  };

  const copy = async () => {
    if (!link) return;
    await navigator.clipboard.writeText(link.url);
    setCopied(true);
  };

  const expires = link ? new Date(link.expires_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "";

  return (
    <section className="express-card" aria-label="Send to Adobe Express">
      <h2 className="express-title">Send to Adobe Express</h2>
      {link ? (
        <>
          <label className="visually-hidden" htmlFor="express-link">
            Express link
          </label>
          <input id="express-link" className="input" readOnly value={link.url} onFocus={(e) => e.target.select()} />
          <div className="express-actions">
            <Button variant="outline" onClick={copy}>
              {copied ? "Copied" : "Copy link"}
            </Button>
            <Button variant="quiet" onClick={create}>
              New link
            </Button>
          </div>
          <p className="muted">
            Paste it into the Redraft add-on in Express before {expires}. Importing spends one export transaction.
          </p>
        </>
      ) : (
        <Button variant="outline" onClick={create}>
          Create Express link
        </Button>
      )}
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
