#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV_FILE="$SCRIPT_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"
DB="${POSTGRES_DB:-surveillance_db}"
USER="${POSTGRES_USER:-surveillance_user}"
PASSWORD="${POSTGRES_PASSWORD:-surveillance_pass_2026}"

export PGPASSWORD="$PASSWORD"

MIGRATIONS_DIR="$SCRIPT_DIR/migrations"

echo "[db-init] Ensuring database '$DB' exists..."
psql -h "$HOST" -p "$PORT" -U postgres -d postgres -c "SELECT 1" >/dev/null 2>&1 || {
  echo "[db-init] WARNING: Cannot connect as postgres. Trying to create via user '$USER'..."
}
set +e
DB_EXISTS=$(psql -h "$HOST" -p "$PORT" -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" 2>/dev/null)
if [[ "$DB_EXISTS" != "1" ]]; then
  psql -h "$HOST" -p "$PORT" -U postgres -d postgres -c "CREATE DATABASE $DB;" 2>/dev/null || true
  psql -h "$HOST" -p "$PORT" -U postgres -d postgres -c "CREATE USER $USER WITH PASSWORD '$PASSWORD';" 2>/dev/null || true
  psql -h "$HOST" -p "$PORT" -U postgres -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB TO $USER;" 2>/dev/null || true
fi
set -e

echo "[db-init] Applying migrations to $DB..."
for f in "$MIGRATIONS_DIR"/*.sql; do
  [[ -f "$f" ]] || continue
  echo "  -> $(basename "$f")"
  psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -f "$f"
done

echo "[db-init] Done."
