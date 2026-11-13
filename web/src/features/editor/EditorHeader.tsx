import type { DocumentData } from "../../shared/api/client";
import { useAuth } from "../../shared/hooks/useAuth";
import { linkTo } from "../../shared/hooks/useRoute";
import { Button } from "../../shared/ui";
import { AddPageMenu } from "../pages/AddPageMenu";

interface Props {
  doc: DocumentData;
  showOriginal: boolean;
  onToggleOriginal: () => void;
  onUndo: () => void;
  onKeep: () => void;
  onReplace: (doc: DocumentData) => void;
}

export function EditorHeader({ doc, showOriginal, onToggleOriginal, onUndo, onKeep, onReplace }: Props) {
  const { user } = useAuth();

  return (
    <header className="editor-head">
      <div>
        <h1 className="editor-title">{doc.name}</h1>
        <p className="muted">
          {doc.pages.length} pages · {doc.transactions_used} Adobe transactions used by this document
        </p>
        <KeepNote doc={doc} signedIn={user !== null} onKeep={onKeep} />
      </div>
      <div className="editor-actions">
        <Button variant="outline" aria-pressed={showOriginal} onClick={onToggleOriginal}>
          {showOriginal ? "Hide original" : "Show original"}
        </Button>
        <Button variant="outline" onClick={onUndo} disabled={!doc.can_undo} title="Ctrl+Z or Cmd+Z">
          Undo
        </Button>
        <AddPageMenu doc={doc} onAdded={onReplace} />
      </div>
    </header>
  );
}

function KeepNote({ doc, signedIn, onKeep }: { doc: DocumentData; signedIn: boolean; onKeep: () => void }) {
  if (doc.owned) return <p className="muted keep-note">Saved to your account.</p>;
  if (signedIn) {
    return (
      <p className="muted keep-note">
        Deleted 24 hours after upload.{" "}
        <Button variant="quiet" className="inline-action" onClick={onKeep}>
          Keep it in my account
        </Button>
      </p>
    );
  }
  return (
    <p className="muted keep-note">
      Deleted 24 hours after upload. <a {...linkTo(`/account?next=/d/${doc.id}`)}>Sign in to keep it</a>.
    </p>
  );
}
