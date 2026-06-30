#!/usr/bin/env bash
# ============================================================================
# start-platform.sh — bring the platform up in dependency order
# Phase 4 Infrastructure Blueprint
#
#   bash scripts/start-platform.sh [--profile storage|core|ai|obs|all]
#
# Profiles (see docs/infrastructure/10-deployment-runbook.md):
#   storage : postgres, minio, iceberg-rest                 (~2 GB)
#   core    : storage + ingestion + processing              (~7 GB)
#   ai      : storage + ai/ml                                (~7 GB)
#   obs     : storage + observability + bi                   (~3 GB)
#   all     : everything (avoid Spark+Ollama peak together)  (~10 GB idle)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$INFRA_DIR/docker"
ENV_FILE="$INFRA_DIR/env/.env"

PROFILE="core"
if [[ "${1:-}" == "--profile" && -n "${2:-}" ]]; then PROFILE="$2"; fi

cd "$DOCKER_DIR"
[[ -f "$ENV_FILE" ]] || { echo "ERROR: missing env/.env (cp env/.env.example env/.env)" >&2; exit 1; }

BASE=(-f docker-compose.yml --env-file "$ENV_FILE")
STORAGE=(-f docker-compose.storage.yml)
INGEST=(-f docker-compose.ingestion.yml)
PROC=(-f docker-compose.processing.yml)
AI=(-f docker-compose.ai.yml)
OBS=(-f docker-compose.observability.yml)
BI=(-f docker-compose.bi.yml)

# Full file set used only to resolve container ids by service name.
PS_FILES=(-f docker-compose.yml
  -f docker-compose.storage.yml -f docker-compose.ingestion.yml
  -f docker-compose.processing.yml -f docker-compose.ai.yml
  -f docker-compose.observability.yml -f docker-compose.bi.yml
  --env-file "$ENV_FILE")

wait_healthy() {  # $1 = compose SERVICE name (container is project-prefixed)
  local svc="$1" cid status
  echo "    waiting for $svc to be healthy..."
  while true; do
    cid="$(docker compose "${PS_FILES[@]}" ps -q "$svc" 2>/dev/null || true)"
    if [[ -n "$cid" ]]; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || echo starting)"
      [[ "$status" == "healthy" ]] && break
    fi
    sleep 3
  done
}

echo "==> Starting platform with profile: $PROFILE"

# Storage is always the foundation
echo "--> Storage stack"
docker compose "${BASE[@]}" "${STORAGE[@]}" --profile storage up -d
wait_healthy postgres
wait_healthy minio

case "$PROFILE" in
  storage)
    ;;
  core)
    echo "--> Ingestion stack"
    docker compose "${BASE[@]}" "${STORAGE[@]}" "${INGEST[@]}" --profile core up -d
    wait_healthy kafka
    echo "--> Processing stack"
    docker compose "${BASE[@]}" "${STORAGE[@]}" "${INGEST[@]}" "${PROC[@]}" --profile core up -d
    ;;
  ai)
    echo "--> AI/ML stack"
    docker compose "${BASE[@]}" "${STORAGE[@]}" "${AI[@]}" --profile ai up -d
    ;;
  obs)
    echo "--> Observability + BI stack"
    docker compose "${BASE[@]}" "${STORAGE[@]}" "${OBS[@]}" "${BI[@]}" --profile obs --profile bi up -d
    ;;
  all)
    echo "--> All stacks (mind the Spark+Ollama peak rule)"
    docker compose "${BASE[@]}" "${STORAGE[@]}" "${INGEST[@]}" "${PROC[@]}" "${AI[@]}" "${OBS[@]}" "${BI[@]}" --profile all up -d
    ;;
  *)
    echo "ERROR: unknown profile '$PROFILE' (use storage|core|ai|obs|all)" >&2
    exit 1
    ;;
esac

echo ""
echo "Platform started. Status:"
docker compose "${PS_FILES[@]}" ps
echo ""
echo "Access URLs: see docs/infrastructure/10-deployment-runbook.md"
