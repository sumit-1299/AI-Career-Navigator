#!/usr/bin/env bash
# ==============================================================================
# AI Career Navigator — Production Deployment Preparation & Verification Script
# ==============================================================================
# Performs pre-deployment environment validation, frontend bundling, and
# verification without performing destructive database schema modifications.
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$REPO_ROOT/scripts"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"

echo "========================================================================"
echo "AI CAREER NAVIGATOR — DEPLOYMENT PREPARATION & VERIFICATION"
echo "========================================================================"

# Step 1: Check Environment Configuration
echo "==> [1/4] Checking environment configuration..."
if [[ ! -f "$REPO_ROOT/.env" && ! -f "$BACKEND_DIR/.env" ]]; then
    echo "WARNING: No active .env file detected in repository root or backend/."
    echo "         Please copy .env.example to .env and configure production credentials:"
    echo "         cp .env.example .env"
else
    echo "    Environment configuration file found."
fi

# Step 2: Validate Backend Dependencies & Python Environment
echo "==> [2/4] Validating backend runtime environment..."
PYTHON_BIN=""
if [[ -f "$BACKEND_DIR/venv/bin/python" ]]; then
    PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
elif [[ -f "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERROR: Python 3 runtime not located." >&2
    exit 1
fi

echo "    Using Python: $PYTHON_BIN"
if ! "$PYTHON_BIN" -c "import flask, sqlalchemy, jwt" >/dev/null 2>&1; then
    echo "ERROR: Essential backend packages (flask, sqlalchemy, jwt) missing in $PYTHON_BIN." >&2
    echo "       Please run: pip install -r $BACKEND_DIR/requirements.txt" >&2
    exit 1
fi
echo "    Backend core libraries verified."

# Step 3: Build Frontend Production Assets
echo "==> [3/4] Building production frontend assets..."
if [[ -f "$SCRIPTS_DIR/build_frontend.sh" ]]; then
    bash "$SCRIPTS_DIR/build_frontend.sh"
else
    echo "ERROR: build_frontend.sh not found at $SCRIPTS_DIR/build_frontend.sh" >&2
    exit 1
fi

# Step 4: Verify Live Service Health (if backend is active)
echo "==> [4/4] Checking backend service health..."
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:5000/api/health}"
if curl -s --connect-timeout 2 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "    Backend server detected on $HEALTH_URL. Running health check..."
    bash "$SCRIPTS_DIR/health_check.sh" "$HEALTH_URL"
else
    echo "    Backend server is not currently running on $HEALTH_URL."
    echo "    To start the backend in production mode, run:"
    echo "        ./scripts/start_backend.sh"
fi

echo "========================================================================"
echo "DEPLOYMENT PREPARATION COMPLETE: Application is ready for serving."
echo "========================================================================"
