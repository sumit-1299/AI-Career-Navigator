#!/usr/bin/env bash
# ==============================================================================
# AI Career Navigator — Frontend Production Build Script
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

echo "==> [Frontend Build] Starting production build process..."
echo "    Working directory: $FRONTEND_DIR"

if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo "ERROR: Frontend directory not found at $FRONTEND_DIR" >&2
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is not installed or not in PATH." >&2
    exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo "==> [Frontend Build] node_modules not detected. Running npm install..."
    npm --prefix "$FRONTEND_DIR" install
fi

echo "==> [Frontend Build] Executing Vite production bundling..."
npm --prefix "$FRONTEND_DIR" run build

if [[ ! -f "$FRONTEND_DIR/dist/index.html" ]]; then
    echo "ERROR: Production build completed, but dist/index.html was not found." >&2
    exit 1
fi

echo "==> [Frontend Build] SUCCESS: Production assets built in $FRONTEND_DIR/dist"
