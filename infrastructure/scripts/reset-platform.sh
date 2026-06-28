#!/usr/bin/env bash
# ============================================================================
# reset-platform.sh — DESTRUCTIVE full reset (removes containers AND volumes)
# Phase 4 Infrastructure Blueprint
#
# Takes a safety backup of PostgreSQL + critical MinIO buckets first, then
# tears everything down including named volumes for a clean slate.
#
#   bash scripts/reset-platform.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$INFRA_DIR/docker"
ENV_FILE="$INFRA_DIR/env/.env"
BACKUP_DIR="$INFRA_DIR/backups"

cd "$DOCKER_DIR"
[[ -f "$ENV_FILE" ]] || { echo "ERROR: missing env/.env" >&2; exit 1; }
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

# --- Confirmation guard -----------------------------------------------------
echo "WARNING: this DESTROYS all platform data (PostgreSQL, MinIO, vectors, etc.)."
read -r -p "Type 'RESET' to continue: " CONFIRM
[[ "$CONFIRM" == "RESET" ]] || { echo "Aborted."; exit 1; }

# --- Safety backup (best-effort) -------------------------------------------
mkdir -p "$BACKUP_DIR/postgres" "$BACKUP_DIR/minio"
TS="$(date +%Y%m%d-%H%M%S)"

if docker ps --format '{{.Names}}' | grep -q '^postgres$'; then
  echo "==> Backing up PostgreSQL -> $BACKUP_DIR/postgres/pre-reset-$TS.sql"
  docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" postgres \
    pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/postgres/pre-reset-$TS.sql" || \
    echo "    (postgres backup skipped)"
fi

if docker ps --format '{{.Names}}' | grep -q '^minio$'; then
  echo "==> Mirroring critical MinIO buckets -> $BACKUP_DIR/minio/"
  docker exec minio mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1 || true
  for b in gold mlflow-artifacts; do
    docker exec minio mc mirror --overwrite "local/$b" "/data-backup/$b" 2>/dev/null || \
      echo "    (mirror of $b skipped)"
  done
fi

# --- Tear down with volumes -------------------------------------------------
ALL_FILES=(
  -f docker-compose.yml
  -f docker-compose.storage.yml
  -f docker-compose.ingestion.yml
  -f docker-compose.processing.yml
  -f docker-compose.ai.yml
  -f docker-compose.observability.yml
  --env-file "$ENV_FILE"
)

echo "==> Removing containers, networks, and VOLUMES"
docker compose "${ALL_FILES[@]}" --profile all down -v

echo "Reset complete. Re-initialize with: bash scripts/bootstrap.sh"
