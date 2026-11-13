import assert from "node:assert/strict";
import { test } from "node:test";
import { errorMessage, parseLink, titleFrom } from "../src/link.js";

const id = "a".repeat(32);
const signature = "b".repeat(64);
const future = Math.floor(Date.now() / 1000) + 600;
const link = (base, expires = future) => `${base}/api/express/${id}?expires=${expires}&signature=${signature}`;

test("accepts https and local links", () => {
  assert.equal(parseLink(`  ${link("https://redraft.example.com")} `), link("https://redraft.example.com"));
  assert.equal(parseLink(link("http://localhost:8000")), link("http://localhost:8000"));
});

test("rejects plain http on the open web", () => {
  assert.throws(() => parseLink(link("http://redraft.example.com")), /https/);
});

test("rejects anything that is not an export link", () => {
  assert.throws(() => parseLink("not a url"), /full link/);
  assert.throws(() => parseLink(`https://redraft.example.com/api/documents/${id}`), /Redraft Express link/);
  assert.throws(() => parseLink(`https://evil.example.com/api/express/${id}?expires=1&signature=x`), /Redraft Express/);
});

test("rejects expired links before fetching", () => {
  assert.throws(() => parseLink(link("https://redraft.example.com", 1000)), /expired/);
});

test("reads the title from the download name", () => {
  assert.equal(titleFrom('attachment; filename="report-redraft.pdf"'), "report-redraft");
  assert.equal(titleFrom(null), "Redraft document");
});

test("uses the API's error detail when there is one", async () => {
  assert.equal(await errorMessage(new Response(JSON.stringify({ detail: "Expired" }), { status: 410 })), "Expired");
  assert.equal(await errorMessage(new Response("oops", { status: 502 })), "Redraft answered 502.");
});
