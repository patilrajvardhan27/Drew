import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Block, BlockPatch } from "../../shared/api/client";
import { Button, Tag } from "../../shared/ui";
import { BlockText } from "./BlockText";
import { TableGrid } from "./TableGrid";

const LABELS: Record<Block["type"], string> = {
  heading: "Heading",
  paragraph: "Paragraph",
  list: "List",
  table: "Table",
};

export interface BlockActions {
  onSave: (id: string, patch: BlockPatch) => void;
  onDelete: (id: string) => void;
  onSplit: (id: string, offset: number, text: string) => void;
  onMerge: (id: string) => void;
}

export function BlockCard({ block, canMerge, actions }: { block: Block; canMerge: boolean; actions: BlockActions }) {
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });
  const label = LABELS[block.type] + (block.type === "heading" ? ` ${block.level}` : "");

  return (
    <article
      ref={setNodeRef}
      className={`block-card${isDragging ? " is-placeholder" : ""}`}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      aria-label={label}
    >
      <div className="block-bar">
        <button
          type="button"
          ref={setActivatorNodeRef}
          className="drag-handle"
          {...attributes}
          {...listeners}
          aria-label={`Move ${label.toLowerCase()} block`}
        >
          Drag
        </button>
        <Tag>{label}</Tag>
        <span className="block-tools">
          {canMerge && (
            <Button variant="quiet" onClick={() => actions.onMerge(block.id)}>
              Merge up
            </Button>
          )}
          <Button variant="quiet" onClick={() => actions.onDelete(block.id)}>
            Delete
          </Button>
        </span>
      </div>
      {block.type === "table" ? (
        <TableGrid block={block} onSave={(patch) => actions.onSave(block.id, patch)} />
      ) : (
        <BlockText
          block={block}
          onSave={(patch) => actions.onSave(block.id, patch)}
          onSplit={(offset, text) => actions.onSplit(block.id, offset, text)}
        />
      )}
    </article>
  );
}

/** The lifted copy shown under the pointer while dragging. */
export function BlockGhost({ block }: { block: Block }) {
  return (
    <article className="block-card is-lifted">
      <div className="block-bar">
        <span className="drag-handle">Drag</span>
        <Tag>{LABELS[block.type]}</Tag>
      </div>
      <p className="block-text block-ghost-text">{block.type === "table" ? "Table" : block.text}</p>
    </article>
  );
}
