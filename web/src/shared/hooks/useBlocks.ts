import { useCallback, useRef, useState } from "react";
import { api, type Block, type BlockPatch, type DocumentData } from "../api/client";
import { insertBlock, locate, moveBlock, removeBlock, replaceBlock, type Location, type Trashed } from "./blockOps";

type SetDoc = (update: (doc: DocumentData) => DocumentData) => void;

/** Owns every block change: optimistic update first, server second, rollback on failure. */
export function useBlocks(doc: DocumentData | null, setDoc: SetDoc) {
  const [error, setError] = useState<string | null>(null);
  const [trash, setTrash] = useState<Trashed[]>([]);
  const docRef = useRef(doc);
  docRef.current = doc;

  const attempt = useCallback(
    async (optimistic: (doc: DocumentData) => DocumentData, save: () => Promise<(doc: DocumentData) => DocumentData>) => {
      const before = docRef.current;
      if (!before) return false;
      setError(null);
      setDoc(optimistic);
      try {
        setDoc(await save());
        return true;
      } catch (err) {
        setDoc(() => before);
        setError(err instanceof Error ? err.message : "Something went wrong.");
        return false;
      }
    },
    [setDoc],
  );

  const reorder = useCallback(
    (blockId: string, target: Location) =>
      attempt(
        (d) => moveBlock(d, blockId, target),
        async () => {
          const fresh = await api.moveBlock(blockId, target.pageId, target.index);
          return () => fresh;
        },
      ),
    [attempt],
  );

  const edit = useCallback(
    (blockId: string, patch: BlockPatch) => {
      const current = docRef.current && locate(docRef.current, blockId);
      if (!current) return Promise.resolve(false);
      const optimistic = { ...current.block, ...patch } as Block;
      return attempt(
        (d) => replaceBlock(d, optimistic),
        async () => {
          const saved = await api.patchBlock(blockId, patch);
          return (d) => replaceBlock(d, saved);
        },
      );
    },
    [attempt],
  );

  const remove = useCallback(
    async (blockId: string) => {
      const found = docRef.current && locate(docRef.current, blockId);
      if (!found) return;
      const ok = await attempt(
        (d) => removeBlock(d, blockId),
        async () => {
          await api.deleteBlock(blockId);
          return (d) => d;
        },
      );
      if (ok) setTrash((items) => [...items, found]);
    },
    [attempt],
  );

  const undo = useCallback(async () => {
    const last = trash[trash.length - 1];
    if (!last) return;
    const { block, pageId, index } = last;
    const ok = await attempt(
      (d) => insertBlock(d, block, { pageId, index }),
      async () => {
        const created = await api.createBlock(pageId, {
          type: block.type,
          text: block.text,
          level: block.level,
          table_csv: block.table_csv,
          position: index,
        });
        return (d) => insertBlock(removeBlock(d, block.id), created, { pageId, index });
      },
    );
    if (ok) setTrash((items) => items.slice(0, -1));
  }, [attempt, trash]);

  return { reorder, edit, remove, undo, canUndo: trash.length > 0, error, clearError: () => setError(null) };
}
