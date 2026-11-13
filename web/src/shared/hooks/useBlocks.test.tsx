import { act, renderHook } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api, type Block, type DocumentData } from "../api/client";
import { dropTarget, moveBlock } from "./blockOps";
import { useBlocks } from "./useBlocks";

function block(id: string, pageId: string, position: number): Block {
  return { id, page_id: pageId, type: "paragraph", level: 0, text: id, position, table_csv: null, flags: [] };
}

const doc: DocumentData = {
  id: "d",
  name: "a.pdf",
  sha256: "x",
  created_at: "2026-01-01T00:00:00",
  transactions_used: 1,
  owned: false,
  can_undo: false,
  pages: [
    { id: "p1", kind: "extracted", position: 0, source_index: 0, blocks: [block("a", "p1", 0), block("b", "p1", 1), block("c", "p1", 2)] },
    { id: "p2", kind: "extracted", position: 1, source_index: 1, blocks: [block("d", "p2", 0)] },
  ],
};

const ids = (d: DocumentData, page: number) => d.pages[page].blocks.map((b) => b.id);

function setup() {
  return renderHook(() => {
    const [state, setState] = useState<DocumentData | null>(doc);
    const blocks = useBlocks(state, (update) => setState((d) => (d ? update(d) : d)));
    return { state: state!, blocks };
  });
}

afterEach(() => vi.restoreAllMocks());

describe("blockOps", () => {
  it("moves within a page like the server does", () => {
    expect(ids(moveBlock(doc, "a", { pageId: "p1", index: 2 }), 0)).toEqual(["b", "c", "a"]);
  });

  it("moves across pages and renumbers both", () => {
    const moved = moveBlock(doc, "a", { pageId: "p2", index: 0 });

    expect(ids(moved, 1)).toEqual(["a", "d"]);
    expect(moved.pages[0].blocks.map((b) => b.position)).toEqual([0, 1]);
    expect(moved.pages[1].blocks[0].page_id).toBe("p2");
  });

  it("drops on an empty page area at the end", () => {
    expect(dropTarget(doc, "p2")).toEqual({ pageId: "p2", index: 1 });
    expect(dropTarget(doc, "b")).toEqual({ pageId: "p1", index: 1 });
  });
});

describe("useBlocks", () => {
  it("rolls back a failed reorder and reports the error", async () => {
    vi.spyOn(api, "moveBlock").mockRejectedValue(new Error("Network down"));
    const { result } = setup();

    await act(() => result.current.blocks.reorder("a", { pageId: "p1", index: 2 }));

    expect(ids(result.current.state, 0)).toEqual(["a", "b", "c"]);
    expect(result.current.blocks.error).toBe("Network down");
  });

  it("marks a delete as undoable, then undoes through the server", async () => {
    vi.spyOn(api, "deleteBlock").mockResolvedValue(undefined);
    vi.spyOn(api, "undo").mockResolvedValue(doc);
    const { result } = setup();

    await act(() => result.current.blocks.remove("b"));
    expect(ids(result.current.state, 0)).toEqual(["a", "c"]);
    expect(result.current.state.can_undo).toBe(true);

    await act(() => result.current.blocks.undo());
    expect(api.undo).toHaveBeenCalledWith("d");
    expect(ids(result.current.state, 0)).toEqual(["a", "b", "c"]);
    expect(result.current.state.can_undo).toBe(false);
  });

  it("splits with the unsaved draft and takes the server's document", async () => {
    const after = { ...doc, can_undo: true, pages: [{ ...doc.pages[0], blocks: [block("a", "p1", 0), block("a2", "p1", 1)] }] };
    vi.spyOn(api, "splitBlock").mockResolvedValue(after);
    const { result } = setup();

    await act(() => result.current.blocks.split("a", 3, "abc def"));

    expect(api.splitBlock).toHaveBeenCalledWith("a", 3, "abc def");
    expect(ids(result.current.state, 0)).toEqual(["a", "a2"]);
  });

  it("keeps server flags after an edit", async () => {
    vi.spyOn(api, "patchBlock").mockResolvedValue({ ...block("a", "p1", 0), text: "new", flags: ["checked"] });
    const { result } = setup();

    await act(() => result.current.blocks.edit("a", { text: "new" }));

    expect(result.current.state.pages[0].blocks[0]).toMatchObject({ text: "new", flags: ["checked"] });
  });
});
