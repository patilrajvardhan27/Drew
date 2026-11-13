import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { useEffect, useMemo, useState } from "react";
import { api } from "../../shared/api/client";
import { dropTarget, locate } from "../../shared/hooks/blockOps";
import { useBlocks } from "../../shared/hooks/useBlocks";
import { useDocument, useUsage } from "../../shared/hooks/useDocument";
import { SkeletonSheet } from "../../shared/ui";
import { ExportPanel } from "../export/ExportPanel";
import { BlockGhost, type BlockActions } from "./BlockCard";
import { EditorHeader } from "./EditorHeader";
import { PageColumn } from "./PageColumn";
import "./editor.css";

function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));
}

export function EditorView({ id }: { id: string }) {
  const { doc, setDoc, error: loadError } = useDocument(id);
  const { usage, refresh: refreshUsage } = useUsage();
  const blocks = useBlocks(doc, setDoc);
  const [dragging, setDragging] = useState<string | null>(null);
  const [showOriginal, setShowOriginal] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const { undo } = blocks;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z" && !event.shiftKey) {
        if (isTyping(event.target)) return;
        event.preventDefault();
        undo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo]);

  const actions: BlockActions = useMemo(
    () => ({ onSave: blocks.edit, onDelete: blocks.remove, onSplit: blocks.split, onMerge: blocks.merge }),
    [blocks.edit, blocks.remove, blocks.split, blocks.merge],
  );

  if (loadError) return <p className="alert editor-message">{loadError}</p>;
  if (!doc) {
    return (
      <div className="editor-pages">
        <SkeletonSheet lines={6} />
        <SkeletonSheet lines={4} />
      </div>
    );
  }

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    setDragging(null);
    if (!over || active.id === over.id) return;
    const target = dropTarget(doc, String(over.id));
    if (target) blocks.reorder(String(active.id), target);
  };

  const lifted = dragging ? locate(doc, dragging)?.block : null;

  return (
    <div className="editor">
      <EditorHeader
        doc={doc}
        showOriginal={showOriginal}
        onToggleOriginal={() => setShowOriginal((on) => !on)}
        onUndo={undo}
        onKeep={() => blocks.replaceWith(() => api.claim(doc.id))}
        onReplace={(fresh) => setDoc(() => fresh)}
      />

      {blocks.error && (
        <p className="alert" role="alert">
          {blocks.error}
        </p>
      )}

      <div className={`editor-layout${showOriginal ? " is-wide" : ""}`}>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={({ active }) => setDragging(String(active.id))}
          onDragCancel={() => setDragging(null)}
          onDragEnd={onDragEnd}
        >
          <div className="editor-pages">
            {doc.pages.map((page, i) => (
              <PageColumn
                key={page.id}
                page={page}
                number={i + 1}
                showOriginal={showOriginal}
                actions={actions}
                onDeletePage={(pageId) => blocks.replaceWith(() => api.deletePage(pageId))}
              />
            ))}
          </div>
          <DragOverlay>{lifted ? <BlockGhost block={lifted} /> : null}</DragOverlay>
        </DndContext>
        <ExportPanel doc={doc} usage={usage} onExported={refreshUsage} />
      </div>
    </div>
  );
}
