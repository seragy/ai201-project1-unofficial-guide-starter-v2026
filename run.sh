#!/usr/bin/env bash
# Start The Unofficial Guide as a service — the one documented command.
#   ./run.sh                 → http://127.0.0.1:8000
#   PORT=9000 ./run.sh       → another port
# Builds the vector index first if this checkout doesn't have one yet
# (chroma_db/ is gitignored, so a fresh clone never does).
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "No .venv here. Run the setup in RUNNING.md (Capstone section) first." >&2
  exit 1
fi
if [ ! -f .env ] || ! grep -q '^GEMINI_API_KEY=.' .env; then
  echo "No GEMINI_API_KEY in .env. Copy .env.example to .env and paste your key in." >&2
  exit 1
fi

if ! .venv/bin/python -c "import sys, config; from store import index_exists; sys.exit(0 if index_exists(config.CORPUS) else 1)" 2>/dev/null; then
  echo "No index yet — building it (first time only, ~80 MB embedder download)…"
  .venv/bin/python app.py index
fi

PORT="${PORT:-8000}"
echo "Serving on http://127.0.0.1:${PORT}  ·  request log: logs/requests.jsonl"
exec .venv/bin/gunicorn serve:app \
  --bind "127.0.0.1:${PORT}" --workers 1 --threads 1 --timeout 60
