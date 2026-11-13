import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { Block, BlockPatch } from "../../shared/api/client";

const SAVE_DELAY_MS = 800;

interface Props {
  block: Block;
  onSave: (patch: BlockPatch) => void;
  onSplit: (offset: number, text: string) => void;
}

/** Shows a block's text; click to edit. Paragraphs save while typing, headings on Enter. */
export function BlockText({ block, onSave, onSplit }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(block.text);
  const timer = useRef<number>();
  const field = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!editing) setDraft(block.text);
  }, [block.text, editing]);

  useEffect(() => {
    if (editing) field.current?.focus();
    return () => window.clearTimeout(timer.current);
  }, [editing]);

  const save = (text: string) => {
    window.clearTimeout(timer.current);
    if (text !== block.text) onSave({ text });
  };

  const change = (text: string) => {
    setDraft(text);
    window.clearTimeout(timer.current);
    if (block.type !== "heading") timer.current = window.setTimeout(() => save(text), SAVE_DELAY_MS);
  };

  const finish = () => {
    save(draft);
    setEditing(false);
  };

  const split = () => {
    const offset = field.current?.selectionStart ?? 0;
    if (offset <= 0 || offset >= draft.length) return;
    window.clearTimeout(timer.current);
    onSplit(offset, draft);
    setEditing(false);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && event.altKey) {
      event.preventDefault();
      split();
    } else if (event.key === "Escape") {
      window.clearTimeout(timer.current);
      setDraft(block.text);
      setEditing(false);
    } else if (event.key === "Enter" && block.type === "heading") {
      event.preventDefault();
      finish();
    }
  };

  if (editing) {
    return (
      <div className="block-editing">
        <textarea
          ref={field}
          className={`input block-input block-${block.type}`}
          aria-label={`Edit ${block.type}`}
          value={draft}
          rows={Math.max(2, draft.split("\n").length)}
          onChange={(e) => change(e.target.value)}
          onBlur={finish}
          onKeyDown={onKeyDown}
        />
        {/* mousedown is cancelled so the textarea keeps focus and its cursor position */}
        <button type="button" className="split-button" onMouseDown={(e) => e.preventDefault()} onClick={split}>
          Split at cursor
        </button>
        <span className="muted split-hint">Alt+Enter splits, Escape cancels</span>
      </div>
    );
  }

  return (
    <button type="button" className={`block-text block-${block.type}`} onClick={() => setEditing(true)}>
      {block.type === "list" ? (
        <ul>
          {block.text.split("\n").filter(Boolean).map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      ) : (
        block.text || <span className="muted">Empty block. Click to write.</span>
      )}
    </button>
  );
}
