#!/usr/bin/env bash
# ============================================================================
# stop-platform.sh — gracefully stop all services, PRESERVING volumes/data
# Phase 4 Infrastructure Blueprint
#
#   bash scripts/stop-platform.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$INFRA_DIR/docker"
ENV_FILE="$INFRA_DIR/env/.env"

cd "$DOCKER_DIR"

ALL_FILES=(
  -f docker-compose.yml
  -f docker-compose.storage.yml
  -f docker-compose.ingestion.yml
  -f docker-compose.processing.yml
  -f docker-compose.ai.yml
  -f docker-compose.observability.yml
  -f docker-compose.bi.yml
  --env-file "$ENV_FILE"
)

echo "==> Stopping all platform services (volumes preserved)"
# 'down' without -v removes containers/networks but KEEPS named volumes.
docker compose "${ALL_FILES[@]}" --profile all down

echo "Done. Data volumes are preserved. Restart with: bash scripts/start-platform.sh"
