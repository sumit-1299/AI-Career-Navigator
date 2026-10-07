#!/bin/sh
set -e

# Wait for PostgreSQL connection if DATABASE_URL is provided
if [ -n "$DATABASE_URL" ]; then
  echo "Checking PostgreSQL database connection..."
  python - << 'EOF'
import os, time, sys
import psycopg2

db_url = os.getenv("DATABASE_URL", "")
if db_url.startswith("postgresql+psycopg2://"):
    db_url = "postgresql://" + db_url[len("postgresql+psycopg2://"):]
elif db_url.startswith("postgres://"):
    db_url = "postgresql://" + db_url[len("postgres://"):]

max_retries = int(os.getenv("DB_CONNECT_RETRIES", "30"))

for i in range(max_retries):
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print(f"PostgreSQL connection verified successfully (attempt {i+1}).")
        sys.exit(0)
    except Exception as e:
        print(f"Waiting for PostgreSQL to become ready ({i+1}/{max_retries}): {e}")
        time.sleep(2)

print("Error: Timed out waiting for PostgreSQL connection.", file=sys.stderr)
sys.exit(1)
EOF
fi

exec "$@"
