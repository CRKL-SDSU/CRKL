#!/usr/bin/env bash
# Start CRKL-Space for local development (no Docker):
#   - Homebrew MySQL (mysql@8.0) on 127.0.0.1:3306
#   - FastAPI backend on 127.0.0.1:8000, restarting when Python files change
#   - Next.js dev server on http://localhost:3000, updating on save
#
# Usage: scripts/dev.sh        Stop with Ctrl+C (stops the backend and frontend;
#                              MySQL keeps running as a Homebrew service).
#
# Needs: Homebrew mysql@8.0 with crkl_db loaded (specs/db/README.md),
# backend/conf/local.yaml, Python packages from backend/requirements.txt,
# and CRKL_DB_USER_PASSWORD (exported, or from a direnv .envrc).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MYSQL_SERVICE="mysql@8.0"
BACKEND_PORT=8000
FRONTEND_PORT=3000

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

port_in_use() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

wait_for() {  # wait_for <description> <seconds> <pid or -> <command...>
  local what="$1" seconds="$2" pid="$3"; shift 3
  for _ in $(seq "$seconds"); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    if [[ "$pid" != "-" ]] && ! kill -0 "$pid" 2>/dev/null; then
      fail "$what exited during startup; see its output above."
    fi
    sleep 1
  done
  fail "$what did not become ready within ${seconds}s"
}

# --- Configuration -----------------------------------------------------------

if [[ -z "${CRKL_DB_USER_PASSWORD:-}" ]] && command -v direnv >/dev/null; then
  eval "$(cd "$ROOT" && direnv export bash 2>/dev/null)" || true
fi
[[ -n "${CRKL_DB_USER_PASSWORD:-}" ]] ||
  fail "CRKL_DB_USER_PASSWORD is not set. Export it, or add it to an .envrc and run 'direnv allow'."

CONFIG="${CRKL_CONFIG_PATH:-$ROOT/backend/conf/local.yaml}"
[[ -f "$CONFIG" ]] ||
  fail "Backend config not found: $CONFIG (see the README's backend configuration section)."

if [[ ! -f "$ROOT/frontend/.env.local" ]]; then
  info "Creating frontend/.env.local"
  printf 'CRKL_BACKEND_URL=http://127.0.0.1:%s\n' "$BACKEND_PORT" > "$ROOT/frontend/.env.local"
fi

# --- Ports -------------------------------------------------------------------

if port_in_use "$FRONTEND_PORT"; then
  if docker compose -f "$ROOT/docker-compose.yml" ps --status running --services 2>/dev/null | grep -qx frontend; then
    fail "Port $FRONTEND_PORT is used by the Docker frontend. Stop it with: docker compose stop frontend"
  fi
  fail "Port $FRONTEND_PORT is already in use."
fi
port_in_use "$BACKEND_PORT" && fail "Port $BACKEND_PORT is already in use."

# --- MySQL -------------------------------------------------------------------

if ! brew services list 2>/dev/null | grep -Eq "^${MYSQL_SERVICE}[[:space:]]+started"; then
  info "Starting $MYSQL_SERVICE"
  brew services start "$MYSQL_SERVICE" >/dev/null
fi
wait_for "MySQL" 30 - nc -z 127.0.0.1 3306

# --- Dependencies ------------------------------------------------------------

python3 -c 'import fastapi, uvicorn, pymysql, yaml' 2>/dev/null ||
  fail "Missing Python packages. Run: python3 -m pip install -r backend/requirements.txt"

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  info "Installing frontend dependencies"
  (cd "$ROOT/frontend" && npm install)
fi

# --- Servers -----------------------------------------------------------------

BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  trap - INT TERM EXIT
  info "Stopping servers"
  # Stop the whole process group: the subshells, uvicorn (and its reloader),
  # npm/next, and the log-prefixing sed processes.
  kill -- -$$ 2>/dev/null || kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  exit "${1:-0}"
}
trap 'cleanup 130' INT TERM
trap 'cleanup $?' EXIT

info "Starting backend on http://127.0.0.1:$BACKEND_PORT"
(
  cd "$ROOT/backend/code"
  CRKL_CONFIG_PATH="$CONFIG" PYTHONUNBUFFERED=1 \
    python3 -m uvicorn main:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload 2>&1 |
    sed -l 's/^/[backend]  /'
) &
BACKEND_PID=$!

wait_for "Backend" 30 "$BACKEND_PID" \
  sh -c "curl -sf http://127.0.0.1:$BACKEND_PORT/api/v1/health | grep -q 'connected :)'"
info "Backend connected to MySQL"

info "Starting frontend on http://localhost:$FRONTEND_PORT"
(
  cd "$ROOT/frontend"
  npm run dev -- --port "$FRONTEND_PORT" 2>&1 | sed -l 's/^/[frontend] /'
) &
FRONTEND_PID=$!

wait_for "Frontend" 60 "$FRONTEND_PID" curl -sf -o /dev/null "http://localhost:$FRONTEND_PORT/explore"
info "Ready: http://localhost:$FRONTEND_PORT/explore  (Ctrl+C to stop)"

# Keep running until a server stops; then stop the other one too.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done
fail "A server stopped unexpectedly; see its output above."
