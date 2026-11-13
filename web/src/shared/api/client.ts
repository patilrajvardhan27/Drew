import type { components } from "./schema";

type Schemas = components["schemas"];
export type Block = Schemas["BlockOut"];
export type Page = Schemas["PageOut"];
export type DocumentData = Schemas["DocumentOut"];
export type Usage = Schemas["UsageOut"];
export type BlockCreate = Schemas["BlockCreate"];
export type BlockPatch = Schemas["BlockPatch"];
export type PageCreate = Schemas["PageCreate"];
export type LegalDetails = Schemas["LegalDetails"];

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

function detail(body: unknown, fallback: string): string {
  const value = (body as { detail?: unknown } | null)?.detail;
  if (typeof value === "string") return value;
  if (Array.isArray(value) && value[0]?.msg) return String(value[0].msg);
  return fallback;
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = init.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init.headers };
  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, detail(body, `Request failed (${response.status})`));
  }
  return response;
}

async function json<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await request(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
  return response.json() as Promise<T>;
}

export const api = {
  upload(file: File): Promise<DocumentData> {
    const form = new FormData();
    form.append("file", file);
    return request("/documents", { method: "POST", body: form }).then((r) => r.json());
  },
  document: (id: string) => json<DocumentData>(`/documents/${id}`),
  usage: () => json<Usage>("/usage"),
  createBlock: (pageId: string, body: BlockCreate) => json<Block>(`/pages/${pageId}/blocks`, "POST", body),
  patchBlock: (id: string, body: BlockPatch) => json<Block>(`/blocks/${id}`, "PATCH", body),
  moveBlock: (id: string, pageId: string, position: number) =>
    json<DocumentData>(`/blocks/${id}/move`, "POST", { page_id: pageId, position }),
  deleteBlock: (id: string) => request(`/blocks/${id}`, { method: "DELETE" }).then(() => undefined),
  addPage: (documentId: string, body: PageCreate) => json<DocumentData>(`/documents/${documentId}/pages`, "POST", body),
  deletePage: (id: string) => json<DocumentData>(`/pages/${id}`, "DELETE"),
  previewUrl: (documentId: string) => `/api/documents/${documentId}/preview`,
  exportPdf: (documentId: string) => request(`/documents/${documentId}/export`, { method: "POST" }).then((r) => r.blob()),
};
