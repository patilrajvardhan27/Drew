import { afterEach, describe, expect, it, vi } from "vitest";
import { api, type DocumentData } from "./client";

function reply(body: unknown, headers: Record<string, string> = {}, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
}

afterEach(() => vi.unstubAllGlobals());

describe("revision guard", () => {
  it("sends the last revision it saw on writes, not on reads, and follows the server's answer", async () => {
    const calls: Request[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit) => {
        calls.push(new Request(`http://x${url}`, init));
        if (url.endsWith("/documents/d")) return reply({ id: "d", revision: 3, pages: [] } as unknown as DocumentData);
        return reply({}, { "X-Document-Revision": "4" });
      }),
    );

    await api.document("d");
    await api.patchBlock("b", { text: "one" });
    await api.patchBlock("b", { text: "two" });

    expect(calls[0].headers.get("X-Document-Revision")).toBeNull();
    expect(calls[1].headers.get("X-Document-Revision")).toBe("3");
    expect(calls[2].headers.get("X-Document-Revision")).toBe("4");
  });
});
