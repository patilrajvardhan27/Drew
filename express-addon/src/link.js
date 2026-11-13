// Accepts only Redraft's signed export links, so the panel never fetches arbitrary URLs.
const PATH = /^\/api\/express\/[a-f0-9]{32}$/;

export function parseLink(raw) {
  let url;
  try {
    url = new URL(String(raw).trim());
  } catch {
    throw new Error("Paste the full link from Redraft's Send to Adobe Express box.");
  }
  const local = url.hostname === "localhost" || url.hostname === "127.0.0.1";
  if (url.protocol !== "https:" && !(local && url.protocol === "http:")) {
    throw new Error("Redraft links must use https.");
  }
  const { expires, signature } = Object.fromEntries(url.searchParams);
  if (!PATH.test(url.pathname) || !/^\d+$/.test(expires ?? "") || !/^[a-f0-9]{64}$/.test(signature ?? "")) {
    throw new Error("That does not look like a Redraft Express link.");
  }
  if (Number(expires) * 1000 < Date.now()) {
    throw new Error("This link has expired. Create a new one in Redraft.");
  }
  return url.toString();
}

export function titleFrom(disposition) {
  const match = /filename="([^"]+)"/.exec(disposition ?? "");
  return match ? match[1].replace(/\.pdf$/i, "") : "Redraft document";
}

export async function errorMessage(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // Not JSON; fall through to the status line.
  }
  return `Redraft answered ${response.status}.`;
}
