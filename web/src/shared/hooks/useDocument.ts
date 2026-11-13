import { useCallback, useEffect, useState } from "react";
import { api, type DocumentData, type Usage } from "../api/client";

export function useDocument(id: string) {
  const [doc, setDocState] = useState<DocumentData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setDocState(null);
    setError(null);
    api
      .document(id)
      .then((data) => live && setDocState(data))
      .catch((err: Error) => live && setError(err.message));
    return () => {
      live = false;
    };
  }, [id]);

  const setDoc = useCallback((update: (doc: DocumentData) => DocumentData) => {
    setDocState((current) => (current ? update(current) : current));
  }, []);

  return { doc, setDoc, error };
}

export function useUsage() {
  const [usage, setUsage] = useState<Usage | null>(null);
  const refresh = useCallback(() => {
    api.usage().then(setUsage).catch(() => setUsage(null));
  }, []);
  useEffect(refresh, [refresh]);
  return { usage, refresh };
}
