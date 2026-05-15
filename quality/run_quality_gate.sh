#!/usr/bin/env bash
set -euo pipefail

echo "[FabMind] Quality Gate"

echo "Check required files"
test -f README.md
test -f AGENTS.md
test -f contracts/openapi.yaml
test -f infra/docker-compose.yml
test -f .github/workflows/ci.yml

echo "Check backend tests if available"
if [ -d apps/api ]; then
  (cd apps/api && uv run pytest)
fi

echo "Check frontend typecheck if available"
if [ -d apps/web ]; then
  (cd apps/web && npm run typecheck)
fi

echo "Quality gate completed"
