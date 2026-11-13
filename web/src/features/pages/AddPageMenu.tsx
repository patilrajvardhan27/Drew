import { useState, type FormEvent } from "react";
import { api, type DocumentData, type PageCreate } from "../../shared/api/client";
import { Button, Field } from "../../shared/ui";
import "./pages.css";

const KINDS: { value: PageCreate["kind"]; label: string }[] = [
  { value: "terms", label: "Terms of Service" },
  { value: "privacy", label: "Privacy Policy" },
  { value: "copyright", label: "Copyright" },
  { value: "blank", label: "Blank page" },
];

const today = () => new Date().toISOString().slice(0, 10);

export function AddPageMenu({ doc, onAdded }: { doc: DocumentData; onAdded: (doc: DocumentData) => void }) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<PageCreate["kind"]>("terms");
  const [position, setPosition] = useState(doc.pages.length);
  const [details, setDetails] = useState({ company: "", email: "", effective_date: today(), jurisdiction: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (key: keyof typeof details) => (e: { target: { value: string } }) =>
    setDetails((d) => ({ ...d, [key]: e.target.value }));

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body: PageCreate = { kind, position, details: kind === "blank" ? null : details };
      onAdded(await api.addPage(doc.id, body));
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add the page.");
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <Button
        onClick={() => {
          setPosition(doc.pages.length);
          setOpen(true);
        }}
      >
        Add page
      </Button>
    );
  }

  return (
    <form className="add-page" onSubmit={submit} aria-label="Add a page">
      <Field label="Page">
        <select className="input" value={kind} onChange={(e) => setKind(e.target.value as PageCreate["kind"])}>
          {KINDS.map((k) => (
            <option key={k.value} value={k.value}>
              {k.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Insert">
        <select className="input" value={position} onChange={(e) => setPosition(Number(e.target.value))}>
          {doc.pages.map((_, i) => (
            <option key={i} value={i}>
              Before page {i + 1}
            </option>
          ))}
          <option value={doc.pages.length}>At the end</option>
        </select>
      </Field>
      {kind !== "blank" && (
        <>
          <Field label="Company name">
            <input className="input" required value={details.company} onChange={update("company")} />
          </Field>
          <Field label="Contact email">
            <input className="input" type="email" required value={details.email} onChange={update("email")} />
          </Field>
          <Field label="Effective date">
            <input className="input" type="date" required value={details.effective_date} onChange={update("effective_date")} />
          </Field>
          <Field label="Jurisdiction">
            <input className="input" required value={details.jurisdiction} onChange={update("jurisdiction")} />
          </Field>
          <p className="muted add-page-note">Template text. Not legal advice. Review before publishing.</p>
        </>
      )}
      {error && <p className="alert">{error}</p>}
      <div className="add-page-actions">
        <Button variant="outline" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? "Adding" : "Insert page"}
        </Button>
      </div>
    </form>
  );
}
