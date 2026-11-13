#!/usr/bin/env node
// Fails when a tracked source file passes the line limit. Generated files and lockfiles are skipped.
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";

const LIMIT = 250;
const SOURCE = /\.(py|ts|tsx|js|mjs|css|html|j2|md|sh|yml|yaml|toml)$/;
const SKIP = [/^contracts\//, /schema\.d\.ts$/, /package-lock\.json$/, /^tests\/fixtures\//];

const files = execSync("git ls-files --cached --others --exclude-standard", { encoding: "utf8" })
  .split("\n")
  .filter((file) => SOURCE.test(file) && !SKIP.some((rule) => rule.test(file)));

const over = files
  .map((file) => ({ file, lines: readFileSync(file, "utf8").split("\n").length - 1 }))
  .filter(({ lines }) => lines > LIMIT);

for (const { file, lines } of over) console.error(`${file}: ${lines} lines (limit ${LIMIT})`);
if (over.length) process.exit(1);
console.log(`Checked ${files.length} files; all within ${LIMIT} lines.`);
