import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { BlockPatch, Page } from "../../shared/api/client";
import { Button, PageSheet } from "../../shared/ui";
import { BlockCard } from "./BlockCard";

const KIND_LABELS: Record<Page["kind"], string> = {
  extracted: "",
  copyright: "Copyright",
  privacy: "Privacy Policy",
  terms: "Terms of Service",
  blank: "Blank page",
};

interface Props {
  page: Page;
  number: number;
  onSave: (id: string, patch: BlockPatch) => void;
  onDeleteBlock: (id: string) => void;
  onDeletePage: (id: string) => void;
}

export function PageColumn({ page, number, onSave, onDeleteBlock, onDeletePage }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: page.id });
  const kind = KIND_LABELS[page.kind];
  const label = `Page ${number}${kind ? ` · ${kind}` : ""}`;

  return (
    <PageSheet
      label={label}
      innerRef={setNodeRef}
      actions={
        <Button variant="quiet" onClick={() => onDeletePage(page.id)}>
          Remove page
        </Button>
      }
    >
      <SortableContext items={page.blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
        <div className={`block-list${isOver ? " is-over" : ""}`}>
          {page.blocks.map((block) => (
            <BlockCard key={block.id} block={block} onSave={onSave} onDelete={onDeleteBlock} />
          ))}
          {page.blocks.length === 0 && <p className="muted empty-page">Drop blocks here.</p>}
        </div>
      </SortableContext>
    </PageSheet>
  );
}
