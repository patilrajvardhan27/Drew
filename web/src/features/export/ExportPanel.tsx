import { useEffect, useState } from "react";
import { api, type DocumentData, type Usage } from "../../shared/api/client";
import { downloadFile } from "../../shared/csv";
import { Button, Skeleton } from "../../shared/ui";
import { ExpressCard } from "./ExpressCard";
import "./export.css";

const PREVIEW_DELAY_MS = 700;

function fingerprint(doc: DocumentData): string {
  let hash = 0;
  for (const char of JSON.stringify(doc.pages)) hash = (hash * 31 + char.charCodeAt(0)) | 0;
  return String(hash >>> 0);
}

/** Preview uses the same HTML and print CSS as the export, so what you see is what Adobe renders. */
export function ExportPanel({ doc, usage, onExported }: { doc: DocumentData; usage: Usage | null; onExported: () => void }) {
  const [version, setVersion] = useState(() => fingerprint(doc));
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const next = fingerprint(doc);
    const timer = window.setTimeout(() => {
      if (next !== version) {
        setLoaded(false);
        setVersion(next);
      }
    }, PREVIEW_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [doc, version]);

  const exportPdf = async () => {
    setBusy(true);
    setError(null);
    try {
      const pdf = await api.exportPdf(doc.id);
      downloadFile(doc.name.replace(/\.pdf$/i, "") + "-redraft.pdf", pdf, "application/pdf");
      onExported();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="export-panel" aria-label="Preview and export">
      <div className="export-frame">
        {!loaded && <Skeleton height={360} />}
        <iframe
          title="Print preview"
          src={`${api.previewUrl(doc.id)}?v=${version}`}
          onLoad={() => setLoaded(true)}
          className={loaded ? "" : "visually-hidden"}
        />
      </div>
      <Button onClick={exportPdf} disabled={busy}>
        {busy ? "Exporting" : "Export PDF"}
      </Button>
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
      <UsageNote usage={usage} />
      <ExpressCard documentId={doc.id} />
    </aside>
  );
}

function UsageNote({ usage }: { usage: Usage | null }) {
  if (!usage) return <Skeleton width="70%" />;
  if (usage.mode === "fixture") {
    return <p className="muted">Offline mode: uploads replay a recorded sample and export is turned off.</p>;
  }
  return (
    <p className="muted">
      Export costs 1 Adobe transaction. {usage.remaining} of {usage.limit} left this month.
    </p>
  );
}
