#!/usr/bin/env bash
# Runs everything CI runs. Use PYTHON=... to point at a virtualenv.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python}"

node scripts/check-file-length.mjs
"$PYTHON" -m ruff check api tests scripts
"$PYTHON" -m ruff format --check api tests scripts
"$PYTHON" -m pytest -q

"$PYTHON" -m scripts.export_openapi >/dev/null
npm --prefix web run gen:api >/dev/null
git diff --exit-code -- contracts web/src/shared/api/schema.d.ts || {
  echo "The API contract changed. Commit contracts/openapi.json and the regenerated client."
  exit 1
}

node --test express-addon/test/*.test.js
npm --prefix web run typecheck
npm --prefix web test
npm --prefix web run build
(cd web && PYTHON="$PYTHON" npx playwright test --trace off)
