import { useRef, useState, type DragEvent } from "react";
import { api } from "../../shared/api/client";
import { navigate } from "../../shared/hooks/useRoute";
import { Button, SkeletonSheet } from "../../shared/ui";
import "./upload.css";

const MAX_MB = 20;

export function UploadView() {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hovering, setHovering] = useState(false);

  const send = async (file: File | undefined) => {
    if (!file) return;
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`PDFs are limited to ${MAX_MB} MB.`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const doc = await api.upload(file);
      navigate(`/d/${doc.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setBusy(false);
    }
  };

  const trySample = async () => {
    const blob = await fetch("/sample.pdf").then((r) => r.blob());
    send(new File([blob], "northwind-field-report.pdf", { type: "application/pdf" }));
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setHovering(false);
    send(event.dataTransfer.files[0]);
  };

  return (
    <div className="upload">
      <section className="hero">
        <h1>Rewrite a PDF without retyping it.</h1>
        <p className="hero-lede">
          Redraft reads your PDF into headings, paragraphs, lists and tables. Drag them into a new order, edit the
          words, add Terms, Privacy or Copyright pages, and export a clean PDF.
        </p>
      </section>

      {busy ? (
        <div aria-live="polite">
          <p className="muted">Reading your PDF. Larger files take up to a minute.</p>
          <SkeletonSheet lines={6} />
        </div>
      ) : (
        <div
          className={`dropzone${hovering ? " is-hovering" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setHovering(true);
          }}
          onDragLeave={() => setHovering(false)}
          onDrop={onDrop}
        >
          <p className="dropzone-title">Drop a PDF here</p>
          <p className="muted">Up to {MAX_MB} MB and 50 pages. Files are deleted after 24 hours.</p>
          <div className="dropzone-actions">
            <Button onClick={() => input.current?.click()}>Choose a PDF</Button>
            <Button variant="outline" onClick={trySample}>
              Try the sample report
            </Button>
          </div>
          <label className="visually-hidden" htmlFor="pdf-input">
            PDF file
          </label>
          <input
            id="pdf-input"
            ref={input}
            type="file"
            accept="application/pdf,.pdf"
            className="visually-hidden"
            onChange={(e) => send(e.target.files?.[0])}
          />
        </div>
      )}
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}

      <ol className="steps">
        <li>
          <h2>Extract</h2>
          <p className="muted">Adobe PDF Extract finds the structure in reading order, tables included.</p>
        </li>
        <li>
          <h2>Edit</h2>
          <p className="muted">Drag blocks between pages, rewrite text, fix flagged tables.</p>
        </li>
        <li>
          <h2>Export</h2>
          <p className="muted">Adobe HTML to PDF writes the result with the layout from the preview.</p>
        </li>
      </ol>
    </div>
  );
}
