import type { Block, DocumentData, Page } from "../api/client";

export interface Location {
  pageId: string;
  index: number;
}

export interface Trashed extends Location {
  block: Block;
}

function withPositions(blocks: Block[], pageId: string): Block[] {
  return blocks.map((block, position) => ({ ...block, page_id: pageId, position }));
}

function mapPages(doc: DocumentData, change: (page: Page) => Block[]): DocumentData {
  return { ...doc, pages: doc.pages.map((page) => ({ ...page, blocks: withPositions(change(page), page.id) })) };
}

export function locate(doc: DocumentData, blockId: string): (Location & { block: Block }) | null {
  for (const page of doc.pages) {
    const index = page.blocks.findIndex((b) => b.id === blockId);
    if (index >= 0) return { pageId: page.id, index, block: page.blocks[index] };
  }
  return null;
}

/** Remove the block and insert it at `index` on the target page, matching the server's rule. */
export function moveBlock(doc: DocumentData, blockId: string, target: Location): DocumentData {
  const found = locate(doc, blockId);
  if (!found) return doc;
  return mapPages(doc, (page) => {
    const rest = page.blocks.filter((b) => b.id !== blockId);
    if (page.id !== target.pageId) return rest;
    const index = Math.max(0, Math.min(target.index, rest.length));
    return [...rest.slice(0, index), found.block, ...rest.slice(index)];
  });
}

export function removeBlock(doc: DocumentData, blockId: string): DocumentData {
  return mapPages(doc, (page) => page.blocks.filter((b) => b.id !== blockId));
}

export function insertBlock(doc: DocumentData, block: Block, target: Location): DocumentData {
  return mapPages(doc, (page) =>
    page.id === target.pageId
      ? [...page.blocks.slice(0, target.index), block, ...page.blocks.slice(target.index)]
      : page.blocks,
  );
}

export function replaceBlock(doc: DocumentData, block: Block): DocumentData {
  return mapPages(doc, (page) => page.blocks.map((b) => (b.id === block.id ? { ...b, ...block } : b)));
}

/** Resolve a drop: over a block means "take its place", over a page means "go to the end". */
export function dropTarget(doc: DocumentData, overId: string): Location | null {
  const overBlock = locate(doc, overId);
  if (overBlock) return { pageId: overBlock.pageId, index: overBlock.index };
  const page = doc.pages.find((p) => p.id === overId);
  return page ? { pageId: page.id, index: page.blocks.length } : null;
}
