#!/usr/bin/env bash
# Helper to (optionally) refresh research data, start the FastAPI backend,
# and boot the Next.js frontend so the entire stack runs from one command.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAIN_APP_DIR="$REPO_ROOT/main-app"

usage() {
  cat <<'EOF'
Usage: scripts/run_everything.sh [options]

Options:
  --facts "<text>"         Provide inline case facts for python main.py
  --facts-file <path>      Read case facts from file for python main.py
  --port <number>          Port for the FastAPI backend (default 8000)
  --skip-pipeline          Skip running python main.py before starting servers
  -h, --help               Show this message

Environment variables:
  GOOGLE_API_KEY / GEMINI_API_KEY   Required if python main.py needs Gemini access
  LEGAL_ANALYSIS_RESULTS_FILE       Override path to legal_analysis_results.json
  CASES_DATA_DIR                    Override path to cached case documents
  RESEARCH_API_CORS                 Allowed origins for the FastAPI server
  NEXT_PUBLIC_RESEARCH_API_URL      Frontend override (auto-set based on --port)
EOF
}

FACTS_ARGS=()
RUN_PIPELINE=1
PORT="${PORT:-8000}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --facts)
      [[ $# -lt 2 ]] && { echo "Missing value for --facts"; exit 1; }
      FACTS_ARGS=(--facts "$2")
      shift 2
      ;;
    --facts-file)
      [[ $# -lt 2 ]] && { echo "Missing value for --facts-file"; exit 1; }
      FACTS_ARGS=(--facts-file "$2")
      shift 2
      ;;
    --port)
      [[ $# -lt 2 ]] && { echo "Missing value for --port"; exit 1; }
      PORT="$2"
      shift 2
      ;;
    --skip-pipeline)
      RUN_PIPELINE=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

export NEXT_PUBLIC_RESEARCH_API_URL="${NEXT_PUBLIC_RESEARCH_API_URL:-http://localhost:${PORT}}"

command -v uvicorn >/dev/null 2>&1 || {
  echo "uvicorn not found. Install python dependencies first (pip install -r requirements.txt)." >&2
  exit 1
}

command -v npm >/dev/null 2>&1 || {
  echo "npm not found. Install Node.js 18+." >&2
  exit 1
}

if [[ $RUN_PIPELINE -eq 1 ]]; then
  if [[ ${#FACTS_ARGS[@]} -eq 0 ]]; then
    echo "[run-everything] No facts supplied; skipping python main.py (use --facts or --facts-file to refresh data)."
  else
    echo "[run-everything] Running python main.py to refresh legal analysis data..."
    (cd "$REPO_ROOT" && python main.py "${FACTS_ARGS[@]}")
    echo "[run-everything] Legal analysis workflow complete."
  fi
else
  echo "[run-everything] Skipping python main.py as requested."
fi

cleanup() {
  echo
  echo "[run-everything] Shutting down services..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[run-everything] Starting FastAPI backend on port ${PORT}..."
(cd "$REPO_ROOT" && uvicorn research_api.main:app --host 0.0.0.0 --port "$PORT") &
BACKEND_PID=$!

echo "[run-everything] Starting Next.js frontend (npm run dev)..."
(cd "$MAIN_APP_DIR" && npm run dev) &
FRONTEND_PID=$!

echo
echo "[run-everything] Both servers are running."
echo "  FastAPI:    http://localhost:${PORT}"
echo "  Next.js UI: http://localhost:3000"
echo
echo "Press Ctrl+C to stop everything."

wait -n "$BACKEND_PID" "$FRONTEND_PID"
