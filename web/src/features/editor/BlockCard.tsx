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

interface Props {
  block: Block;
  onSave: (id: string, patch: BlockPatch) => void;
  onDelete: (id: string) => void;
}

export function BlockCard({ block, onSave, onDelete }: Props) {
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
        <Button variant="quiet" className="block-delete" onClick={() => onDelete(block.id)}>
          Delete
        </Button>
      </div>
      <BlockBody block={block} onSave={(patch) => onSave(block.id, patch)} />
    </article>
  );
}

export function BlockBody({ block, onSave }: { block: Block; onSave: (patch: BlockPatch) => void }) {
  return block.type === "table" ? <TableGrid block={block} onSave={onSave} /> : <BlockText block={block} onSave={onSave} />;
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
