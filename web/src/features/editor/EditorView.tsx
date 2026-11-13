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
import { useState } from "react";
import { api } from "../../shared/api/client";
import { dropTarget, locate } from "../../shared/hooks/blockOps";
import { useBlocks } from "../../shared/hooks/useBlocks";
import { useDocument, useUsage } from "../../shared/hooks/useDocument";
import { Button, SkeletonSheet } from "../../shared/ui";
import { ExportPanel } from "../export/ExportPanel";
import { AddPageMenu } from "../pages/AddPageMenu";
import { BlockGhost } from "./BlockCard";
import { PageColumn } from "./PageColumn";
import "./editor.css";

export function EditorView({ id }: { id: string }) {
  const { doc, setDoc, error: loadError } = useDocument(id);
  const { usage, refresh: refreshUsage } = useUsage();
  const blocks = useBlocks(doc, setDoc);
  const [dragging, setDragging] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
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

  const deletePage = (pageId: string) => {
    setPageError(null);
    api
      .deletePage(pageId)
      .then((fresh) => setDoc(() => fresh))
      .catch((err: Error) => setPageError(err.message));
  };

  const lifted = dragging ? locate(doc, dragging)?.block : null;
  const message = blocks.error ?? pageError;

  return (
    <div className="editor">
      <header className="editor-head">
        <div>
          <h1 className="editor-title">{doc.name}</h1>
          <p className="muted">
            {doc.pages.length} pages · {doc.transactions_used} Adobe transactions used by this document
          </p>
        </div>
        <div className="editor-actions">
          <Button variant="outline" onClick={blocks.undo} disabled={!blocks.canUndo}>
            Undo delete
          </Button>
          <AddPageMenu doc={doc} onAdded={(fresh) => setDoc(() => fresh)} />
        </div>
      </header>

      {message && (
        <p className="alert" role="alert">
          {message}
        </p>
      )}

      <div className="editor-layout">
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
                onSave={blocks.edit}
                onDeleteBlock={blocks.remove}
                onDeletePage={deletePage}
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
