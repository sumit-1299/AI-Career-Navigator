#!/usr/bin/env bash
# ==============================================================================
# AI Career Navigator — Backend Production Startup Script
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"

echo "==> [Backend Startup] Preparing production backend server..."

if [[ ! -d "$BACKEND_DIR" ]]; then
    echo "ERROR: Backend directory not found at $BACKEND_DIR" >&2
    exit 1
fi

# Load environment configuration if available
if [[ -f "$REPO_ROOT/.env" ]]; then
    echo "==> [Backend Startup] Loading environment variables from $REPO_ROOT/.env..."
    # Export non-comment lines
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
    set +a
elif [[ -f "$BACKEND_DIR/.env" ]]; then
    echo "==> [Backend Startup] Loading environment variables from $BACKEND_DIR/.env..."
    set -a
    # shellcheck disable=SC1091
    source "$BACKEND_DIR/.env"
    set +a
fi

# Locate Python environment
PYTHON_BIN=""
if [[ -f "$BACKEND_DIR/venv/bin/python" ]]; then
    PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
    GUNICORN_BIN="$BACKEND_DIR/venv/bin/gunicorn"
elif [[ -f "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
    GUNICORN_BIN="$REPO_ROOT/.venv/bin/gunicorn"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
    GUNICORN_BIN="$(command -v gunicorn 2>/dev/null || true)"
else
    echo "ERROR: No suitable Python executable found in virtualenvs or PATH." >&2
    exit 1
fi

echo "    Python binary: $PYTHON_BIN"
export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"

cd "$BACKEND_DIR"

# Launch using Gunicorn if available, otherwise fallback to app.py
if [[ -n "${GUNICORN_BIN:-}" && -x "$GUNICORN_BIN" ]]; then
    echo "==> [Backend Startup] Launching production WSGI server via Gunicorn..."
    exec "$GUNICORN_BIN" --config gunicorn.conf.py wsgi:app
else
    echo "==> [Backend Startup] Gunicorn binary not directly executable. Running via Python..."
    if "$PYTHON_BIN" -c "import gunicorn" >/dev/null 2>&1; then
        exec "$PYTHON_BIN" -m gunicorn --config gunicorn.conf.py wsgi:app
    else
        echo "WARNING: Gunicorn not installed in selected environment. Falling back to Flask app.py..."
        exec "$PYTHON_BIN" app.py
    fi
fi
