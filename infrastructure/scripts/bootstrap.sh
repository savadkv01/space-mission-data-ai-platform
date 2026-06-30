#!/usr/bin/env bash
# ============================================================================
# bootstrap.sh — one-time platform initialization
# Phase 4 Infrastructure Blueprint
#
# Creates MinIO buckets, PostgreSQL schemas/roles, runs framework migrations,
# and pulls the default LLM model. Safe to re-run (idempotent where possible).
#
# Run from infrastructure/:  bash scripts/bootstrap.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$INFRA_DIR/docker"
ENV_FILE="$INFRA_DIR/env/.env"

cd "$DOCKER_DIR"

# --- 0. Preconditions -------------------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Run: cp env/.env.example env/.env" >&2
  exit 1
fi
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

COMPOSE_BASE=(-f docker-compose.yml --env-file "$ENV_FILE")
STORAGE_CTX=(-f docker-compose.yml -f docker-compose.storage.yml --env-file "$ENV_FILE")
BUCKETS=(bronze silver gold warehouse mlflow-artifacts staging)
SCHEMAS=(metadata gold iceberg_catalog airflow mlflow superset feast)

echo "==> [1/5] Pulling base images (storage stack)"
docker compose "${COMPOSE_BASE[@]}" -f docker-compose.storage.yml --profile storage pull

echo "==> [2/5] Starting storage stack (postgres, minio, iceberg-rest)"
docker compose "${COMPOSE_BASE[@]}" -f docker-compose.storage.yml --profile storage up -d

echo "    Waiting for PostgreSQL and MinIO to become healthy..."
until docker compose "${STORAGE_CTX[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
  sleep 3; echo "    ...postgres not ready yet"
done
until docker compose "${STORAGE_CTX[@]}" exec -T minio curl -sf http://localhost:9000/minio/health/live >/dev/null 2>&1; do
  sleep 3; echo "    ...minio not ready yet"
done

echo "==> [3/5] Creating PostgreSQL schemas"
for schema in "${SCHEMAS[@]}"; do
  docker compose "${STORAGE_CTX[@]}" exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" postgres \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "CREATE SCHEMA IF NOT EXISTS ${schema};"
  echo "    schema ready: ${schema}"
done

echo "==> [4/5] Creating MinIO buckets (one-off minio/mc client on data-net)"
docker run --rm --network space-data-net \
  -e MC_HOST_local="http://${MINIO_ROOT_USER}:${MINIO_ROOT_PASSWORD}@minio:9000" \
  minio/mc mb --ignore-existing $(printf 'local/%s ' "${BUCKETS[@]}")
for bucket in "${BUCKETS[@]}"; do echo "    bucket ready: ${bucket}"; done

echo "==> [5/5] (Optional) Pull default LLM model if AI stack is desired"
echo "    Skipping by default. To pull later:"
echo "      docker compose -f docker-compose.yml -f docker-compose.ai.yml --env-file ../env/.env exec ollama ollama pull ${OLLAMA_DEFAULT_MODEL:-llama3.2:3b}"

echo ""
echo "Bootstrap complete. Next: bash scripts/start-platform.sh --profile core"
