import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useState } from "react";
import { api, type Page } from "../../shared/api/client";
import { Button, PageSheet, Skeleton } from "../../shared/ui";
import { BlockCard, type BlockActions } from "./BlockCard";

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
  showOriginal: boolean;
  actions: BlockActions;
  onDeletePage: (id: string) => void;
}

export function PageColumn({ page, number, showOriginal, actions, onDeletePage }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: page.id });
  const kind = KIND_LABELS[page.kind];
  const label = `Page ${number}${kind ? ` · ${kind}` : ""}`;
  const original = showOriginal && page.source_index !== null;

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
      <div className={original ? "page-split" : undefined}>
        {original && <OriginalPage page={page} />}
        <SortableContext items={page.blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
          <div className={`block-list${isOver ? " is-over" : ""}`}>
            {page.blocks.map((block, i) => (
              <BlockCard
                key={block.id}
                block={block}
                canMerge={i > 0 && block.type !== "table" && page.blocks[i - 1].type !== "table"}
                actions={actions}
              />
            ))}
            {page.blocks.length === 0 && <p className="muted empty-page">Drop blocks here.</p>}
          </div>
        </SortableContext>
      </div>
    </PageSheet>
  );
}

function OriginalPage({ page }: { page: Page }) {
  const [state, setState] = useState<"loading" | "ready" | "missing">("loading");
  const pageNumber = (page.source_index ?? 0) + 1;

  if (state === "missing") {
    return <p className="muted original-missing">The original page image is no longer stored.</p>;
  }
  return (
    <figure className="original">
      {state === "loading" && <Skeleton height={420} />}
      <img
        src={api.originalUrl(page.id)}
        alt={`Original page ${pageNumber} of the uploaded PDF`}
        className={state === "ready" ? "" : "visually-hidden"}
        onLoad={() => setState("ready")}
        onError={() => setState("missing")}
      />
      <figcaption className="muted">Original page {pageNumber}</figcaption>
    </figure>
  );
}
