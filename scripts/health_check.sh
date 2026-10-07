#!/usr/bin/env bash
# ==============================================================================
# AI Career Navigator — Backend Production Health Check Script
# ==============================================================================
set -euo pipefail

TARGET_URL="${1:-${HEALTH_URL:-http://127.0.0.1:5000/api/health}}"

echo "==> [Health Check] Probing backend endpoint: $TARGET_URL"

# Use python to probe and validate JSON response
VALIDATION_SCRIPT=$(cat << 'EOF'
import sys, urllib.request, json

url = sys.argv[1]
try:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        code = resp.getcode()
        body = resp.read().decode("utf-8")
        
        if code != 200:
            print(f"FAIL: Expected HTTP 200, received HTTP {code}. Body: {body}", file=sys.stderr)
            sys.exit(1)
            
        data = json.loads(body)
        status = data.get("status")
        db = data.get("database")
        
        if status != "healthy":
            print(f"FAIL: Status is '{status}', expected 'healthy'. Full response: {data}", file=sys.stderr)
            sys.exit(1)
            
        if db != "connected":
            print(f"FAIL: Database connection status is '{db}', expected 'connected'. Full response: {data}", file=sys.stderr)
            sys.exit(1)
            
        print(f"SUCCESS: Backend service is {status} and database is {db}.")
        print(f"Details: service='{data.get('service')}', environment='{data.get('environment')}'")
        sys.exit(0)
except urllib.error.HTTPError as e:
    print(f"FAIL: HTTP Error {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"FAIL: Connection or parsing error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)

if python3 -c "$VALIDATION_SCRIPT" "$TARGET_URL"; then
    echo "==> [Health Check] PASS: Application is healthy and responsive."
    exit 0
else
    echo "==> [Health Check] FAIL: Health check did not pass." >&2
    exit 1
fi
