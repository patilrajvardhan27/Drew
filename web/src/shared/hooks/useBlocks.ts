import { useCallback, useRef, useState } from "react";
import { api, type Block, type BlockPatch, type DocumentData } from "../api/client";
import { locate, moveBlock, removeBlock, replaceBlock, type Location } from "./blockOps";

type SetDoc = (update: (doc: DocumentData) => DocumentData) => void;
type Update = (doc: DocumentData) => DocumentData;

// Block-level answers do not carry the document, but every change lands in the server's history.
const undoable: Update = (doc) => ({ ...doc, can_undo: true });

/** Owns every document change: optimistic update first, server second, rollback on failure. */
export function useBlocks(doc: DocumentData | null, setDoc: SetDoc) {
  const [error, setError] = useState<string | null>(null);
  const docRef = useRef(doc);
  docRef.current = doc;

  const attempt = useCallback(
    async (optimistic: Update, save: () => Promise<Update>) => {
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

  /** For calls that answer with the whole document: no optimistic step, just replace. */
  const replaceWith = useCallback(
    (call: () => Promise<DocumentData>) =>
      attempt(
        (d) => d,
        async () => {
          const fresh = await call();
          return () => fresh;
        },
      ),
    [attempt],
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
          return (d) => undoable(replaceBlock(d, saved));
        },
      );
    },
    [attempt],
  );

  const remove = useCallback(
    (blockId: string) =>
      attempt(
        (d) => removeBlock(d, blockId),
        async () => {
          await api.deleteBlock(blockId);
          return undoable;
        },
      ),
    [attempt],
  );

  const split = useCallback(
    (blockId: string, offset: number, text: string) => replaceWith(() => api.splitBlock(blockId, offset, text)),
    [replaceWith],
  );
  const merge = useCallback((blockId: string) => replaceWith(() => api.mergeBlock(blockId)), [replaceWith]);
  const undo = useCallback(() => {
    const id = docRef.current?.id;
    return id ? replaceWith(() => api.undo(id)) : Promise.resolve(false);
  }, [replaceWith]);

  return { reorder, edit, remove, split, merge, undo, replaceWith, error };
}
