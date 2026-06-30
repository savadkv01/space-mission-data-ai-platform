# Operations Runbook

> **Living operational cheat-sheet** for the Space Mission Data & AI Platform.
> Day-to-day commands to run, start/stop, inspect, and query the platform.
> Updated each phase — see the [Phase Status & Changelog](#phase-status--changelog) at the bottom.

This runbook is **PowerShell-first** (Windows + Docker Desktop), with the equivalent
`bash` convenience scripts noted where they exist. The deeper *design* rationale
lives in [docs/infrastructure/](docs/infrastructure/README.md); this file is the
hands-on operator guide.

---

## Table of Contents

1. [Conventions & one-time setup](#1-conventions--one-time-setup)
2. [Start / stop the platform](#2-start--stop-the-platform)
3. [Status & health checks](#3-status--health-checks)
4. [Logs, resources, troubleshooting](#4-logs-resources-troubleshooting)
5. [Service URLs & login guidance](#5-service-urls--login-guidance)
6. [Querying PostgreSQL yourself](#6-querying-postgresql-yourself)
7. [Object storage (MinIO) — buckets & files](#7-object-storage-minio--buckets--files)
8. [Viewing & querying Bronze / Silver / Gold](#8-viewing--querying-bronze--silver--gold)
9. [Kafka operations](#9-kafka-operations)
10. [Running the ingestion layer](#10-running-the-ingestion-layer)
11. [Phase status & changelog](#phase-status--changelog)

---

## 1. Conventions & one-time setup

### Where commands run

All Docker commands run from the **docker compose directory**. Because the platform
uses six modular stack files, set a reusable Compose context **once per terminal**:

```powershell
# Run once per PowerShell session
Set-Location "c:\D Drive\Projects\DE\Projects\space-data-ai-platform\infrastructure\docker"

$ALL = @(
  '-f','docker-compose.yml',
  '-f','docker-compose.storage.yml',
  '-f','docker-compose.ingestion.yml',
  '-f','docker-compose.processing.yml',
  '-f','docker-compose.ai.yml',
  '-f','docker-compose.observability.yml',
  '-f','docker-compose.bi.yml',
  '--env-file','../env/.env'
)

# Then every command becomes:  docker compose @ALL <command>
docker compose @ALL ps
```

> Containers are **project-prefixed** (`space-platform-<service>-1`). Always address
> services by their **service name** (`postgres`, `minio`, …) through
> `docker compose @ALL exec <service>` — never `docker exec postgres`.

### One-time initialization

```powershell
# 1. Create your local env file from the template (git-ignored)
Copy-Item ../env/.env.example ../env/.env
# 2. Edit ../env/.env — replace every CHANGE_ME_* value, fill any API keys

# 3. Bootstrap: create PostgreSQL schemas + MinIO buckets (idempotent)
#    Easiest cross-platform path is the bash script (WSL / Git Bash):
bash ../scripts/bootstrap.sh
```

**PowerShell-only equivalent** (no bash), after storage is up (see §2):

```powershell
# Schemas
$env:PGPASSWORD = (Select-String '../env/.env' -Pattern '^POSTGRES_PASSWORD=').Line.Split('=')[1]
foreach ($s in 'metadata','gold','iceberg_catalog','airflow','mlflow','superset','feast') {
  docker compose @ALL exec -T postgres psql -U platform -d platform -c "CREATE SCHEMA IF NOT EXISTS $s;"
}
# Buckets (one-off mc client on the data network)
$minioPass = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_PASSWORD=').Line.Split('=')[1]
$minioUser = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_USER=').Line.Split('=')[1]
docker run --rm --network space-data-net -e MC_HOST_local="http://${minioUser}:${minioPass}@minio:9000" `
  minio/mc mb --ignore-existing local/bronze local/silver local/gold local/warehouse local/mlflow-artifacts local/staging
```

---

## 2. Start / stop the platform

Services are grouped into **profiles**. Start the smallest set you need — on a 16 GB
laptop, avoid running the Spark (`processing`) and Ollama (`ai`) peaks at the same time.

| Profile | Stacks started | Approx. idle RAM |
| --- | --- | --- |
| `storage` | postgres, minio, iceberg-rest | ~2 GB |
| `core` | storage + kafka + spark + airflow | ~7 GB |
| `ai` | storage + mlflow, jupyter, qdrant, ollama, open-webui | ~7 GB |
| `obs` | storage + prometheus, grafana, otel | ~3 GB |
| `bi` | storage + superset | ~3 GB |
| `all` | everything (mind the Spark+Ollama peak) | ~10 GB |

### Start

```powershell
# Foundation only
docker compose @ALL --profile storage up -d

# Data-engineering core (storage + ingestion + processing)
docker compose @ALL --profile core up -d

# Observability stack
docker compose @ALL --profile obs up -d

# BI (Superset)
docker compose @ALL --profile bi up -d

# Everything
docker compose @ALL --profile all up -d

# A single service (dependencies start automatically)
docker compose @ALL --profile core up -d kafka
```

> `depends_on` health conditions make Compose wait for upstreams (e.g. `postgres`
> healthy) before starting dependents, so a single `up -d` brings a profile up in order.

**Bash convenience scripts** (staged startup with explicit health waits, WSL / Git Bash):

```bash
bash ../scripts/start-platform.sh --profile core   # storage|core|ai|obs|all
```

### Stop

```powershell
# Stop everything, KEEP all data (named volumes preserved)
docker compose @ALL --profile all down

# Stop a single stack's services (example: processing)
docker compose @ALL --profile core stop spark-master spark-worker airflow
```

```bash
bash ../scripts/stop-platform.sh        # graceful stop, data preserved
```

### Reset (DESTRUCTIVE)

```powershell
# Removes containers, networks AND volumes — wipes all data. Backup first!
docker compose @ALL --profile all down -v
```

```bash
bash ../scripts/reset-platform.sh       # backs up Postgres + key buckets, then wipes
```

---

## 3. Status & health checks

```powershell
# Compose view of targeted services (status + health + ports)
docker compose @ALL ps

# All running platform containers with health
docker ps --filter "name=space-platform" --format "table {{.Names}}\t{{.Status}}"

# Health of one service
docker inspect space-platform-airflow-1 --format '{{.State.Health.Status}}'
```

### Quick verification checklist

```powershell
# PostgreSQL reachable + list schemas
docker compose @ALL exec -T postgres psql -U platform -d platform -c "\dn"

# MinIO buckets present (via console UI is easiest — see §5/§7)

# Kafka broker reachable + list topics
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Iceberg REST catalog config (from inside the data network)
docker run --rm --network space-data-net curlimages/curl:latest -s http://iceberg-rest:8181/v1/config
```

Expected after bootstrap: schemas `metadata, gold, iceberg_catalog, airflow, mlflow,
superset, feast`; buckets `bronze, silver, gold, warehouse, mlflow-artifacts, staging`.

---

## 4. Logs, resources, troubleshooting

```powershell
# Tail logs for a service
docker compose @ALL logs -f airflow

# Last 80 lines, no follow
docker compose @ALL logs --tail 80 spark-master

# Live resource usage (RAM/CPU per container)
docker stats --no-stream

# Restart a single service
docker compose @ALL restart grafana

# Recreate a service after editing its compose/healthcheck
docker compose @ALL up -d --force-recreate iceberg-rest
```

| Symptom | Likely cause / fix |
| --- | --- |
| `Conflict. The container name "minio" is already in use` | A *different* project squats the name. This platform uses project-prefixed names; ensure you pull latest compose. Remove the stray container or stop the other project. |
| Service stuck `health: starting` then `unhealthy` on first boot | Slow first-boot (Airflow/Superset). `start_period` grace windows are configured; it recovers on the next successful probe. |
| `psql: could not connect` from host tools | PostgreSQL port is **not published**; query via `docker compose @ALL exec postgres psql …` (see §6). |
| Out of memory / Docker freezes | Run one heavy profile at a time; never peak `processing` (Spark) and `ai` (Ollama) together. |

---

## 5. Service URLs & login guidance

> Replace passwords with the values in your `../env/.env`. Print one quickly:
> `(Select-String '../env/.env' -Pattern '^GRAFANA_ADMIN_PASSWORD=').Line`

| Service | URL | Login |
| --- | --- | --- |
| MinIO Console | http://localhost:9001 | user `MINIO_ROOT_USER` (default `platform_minio`) / `MINIO_ROOT_PASSWORD` |
| Kafka UI | http://localhost:8088 | no auth |
| Spark Master UI | http://localhost:8080 | no auth |
| Spark Worker UI | http://localhost:8081 | no auth |
| Airflow | http://localhost:8082 | user `admin` / auto-generated (see below) |
| MLflow | http://localhost:5000 | no auth |
| Jupyter Lab | http://localhost:8888 | token = `JUPYTER_TOKEN` (append `?token=…`) |
| Qdrant dashboard | http://localhost:6333/dashboard | no auth |
| Open WebUI (LLM) | http://localhost:3000 | auth disabled (`WEBUI_AUTH=false`) |
| Prometheus | http://localhost:9090 | no auth |
| Grafana | http://localhost:3001 | user `admin` (`GRAFANA_ADMIN_USER`) / `GRAFANA_ADMIN_PASSWORD` |
| Superset | http://localhost:8089 | user `admin` (`SUPERSET_ADMIN_USER`) / `SUPERSET_ADMIN_PASSWORD` |
| FastAPI (later phase) | http://localhost:8000 | — |

**Airflow admin password** (standalone generates it on first boot):

```powershell
docker compose @ALL exec airflow cat /opt/airflow/standalone_admin_password.txt
# Fallback: search the logs
docker compose @ALL logs airflow | Select-String "Password for user 'admin'"
```

---

## 6. Querying PostgreSQL yourself

PostgreSQL hosts the `gold` serving tables plus metadata for Airflow/MLflow/Superset/
Feast. The port is intentionally **not** exposed to the host; query through the container.

```powershell
# Interactive psql session (database: platform, user: platform)
docker compose @ALL exec postgres psql -U platform -d platform
```

Useful psql meta-commands once inside:

```text
\dn               -- list schemas
\dt gold.*        -- list tables in the gold schema
\d gold.<table>   -- describe a table
\du               -- list roles (note: analyst_ro is a read-only role on gold)
\q                -- quit
```

One-off queries (non-interactive):

```powershell
# List all schemas
docker compose @ALL exec -T postgres psql -U platform -d platform -c "\dn"

# List tables in gold
docker compose @ALL exec -T postgres psql -U platform -d platform -c "\dt gold.*"

# Run an ad-hoc query
docker compose @ALL exec -T postgres psql -U platform -d platform -c "SELECT * FROM gold.<table> LIMIT 20;"

# Pipe a .sql file from the host
Get-Content .\my_query.sql | docker compose @ALL exec -T postgres psql -U platform -d platform
```

**Using a GUI client (DBeaver / pgAdmin):** the host port is closed by default. To connect
a desktop client, publish the port by adding `ports: ["5432:5432"]` to the `postgres`
service in `docker-compose.storage.yml`, then connect to `localhost:5432`, db `platform`,
user `platform`. (Left closed by default to avoid clashing with other local Postgres.)

> Note: until the serving phase populates `gold`, these queries return empty result sets —
> the schemas exist but contain no business tables yet.

---

## 7. Object storage (MinIO) — buckets & files

The lakehouse layers live as objects in MinIO (S3-compatible). Two ways to browse:

**A) MinIO Console (easiest):** open http://localhost:9001 and log in with the MinIO
credentials. Browse buckets `bronze / silver / gold / warehouse / mlflow-artifacts / staging`.

**B) `mc` CLI (scriptable, one-off container on the data network):**

```powershell
# Build a reusable mc host string from your .env
$u = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_USER=').Line.Split('=')[1]
$p = (Select-String '../env/.env' -Pattern '^MINIO_ROOT_PASSWORD=').Line.Split('=')[1]
$MC = @('run','--rm','--network','space-data-net','-e',"MC_HOST_local=http://${u}:${p}@minio:9000",'minio/mc')

# List all buckets
docker @MC ls local/

# List objects in a bucket (recursive)
docker @MC ls --recursive local/bronze

# Show object size/metadata
docker @MC stat local/gold/<path/to/object>

# Print a (text/JSON) object to stdout
docker @MC cat local/staging/<path/to/file.json>

# Copy an object out to the host
docker @MC cp local/gold/<object> /tmp/out && docker @MC --help | Out-Null
```

> Buckets are created empty by bootstrap. They fill up once the ingestion and
> transformation phases write data (see changelog).

---

## 8. Viewing & querying Bronze / Silver / Gold

The medallion layers are served three ways depending on what you want:

| Layer | Where it lives | Query method |
| --- | --- | --- |
| **Bronze** (raw) | MinIO `bronze/` (+ Iceberg in `warehouse/`) | MinIO console / `mc`; Spark SQL on the `lakehouse` catalog |
| **Silver** (conformed) | Iceberg tables in `warehouse/` (MinIO) | Spark SQL on the `lakehouse` catalog; DuckDB |
| **Gold** (serving) | Iceberg `warehouse/` **and** PostgreSQL `gold` schema | `psql` (§6) for relational gold; Spark SQL for Iceberg gold |

### Spark SQL over the Iceberg lakehouse

The Spark config wires an Iceberg **REST catalog named `lakehouse`**
(warehouse `s3://warehouse/`, via `iceberg-rest` + MinIO). With the `processing`
stack running:

```powershell
# Open a Spark SQL shell (requires the Iceberg + S3 runtime jars — see note)
docker compose @ALL exec `
  -e AWS_ACCESS_KEY_ID=$u -e AWS_SECRET_ACCESS_KEY=$p `
  spark-master /opt/spark/bin/spark-sql `
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,org.apache.hadoop:hadoop-aws:3.3.4
```

```sql
-- Inside spark-sql:
SHOW NAMESPACES IN lakehouse;            -- bronze, silver, gold (once created)
SHOW TABLES IN lakehouse.silver;
SELECT * FROM lakehouse.gold.<table> LIMIT 20;
```

> The base `apache/spark:3.5.1` image does not bundle the Iceberg/S3 jars, so the
> first run downloads them via `--packages` (needs internet). The **transformation
> phase** ships preconfigured Spark jobs and `make` targets so you won't pass
> `--packages` by hand — this section will be updated then.

### DuckDB (lightweight, 16 GB-friendly)

DuckDB can read Parquet/Iceberg directly from MinIO and is ideal for quick local
analysis. It is introduced as part of the transformation phase; a ready example
(`duckdb` + `httpfs`/`iceberg` extensions pointed at `http://localhost:9000`) will be
added here once that phase lands.

> **Current state (Phase 8):** the **Bronze** layer now holds real landed data —
> raw telemetry plus API-sourced objects under `bronze/<SOURCE>/ingest_date=…/` (run it
> yourself via §10). **Silver/Gold** Iceberg tables still appear after the transformation
> phase; the Spark/DuckDB commands above are the mechanisms you'll use then.

---

## 9. Kafka operations

With the `ingestion` (or `core`) stack running:

```powershell
# List topics
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Describe a topic
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic <topic>

# Create a topic (manual; pipelines create their own later)
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic demo --partitions 3 --replication-factor 1

# Consume the latest messages from a topic
docker compose @ALL exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic <topic> --from-beginning --max-messages 10
```

Or use **Kafka UI** at http://localhost:8088 to browse topics, partitions, and messages.

---

## 10. Running the ingestion layer

The ingestion code lives in [ingestion/](ingestion/README.md) (streaming producers/consumers,
API connectors, synthetic generators, quality + Bronze landing). This section is the
**operator** guide for running it against the live platform.

### Why ingestion runs *inside* the Docker network

Kafka advertises only `INTERNAL://kafka:9092` and is **not published to the host**, so a
producer/consumer started from your laptop shell **cannot reach the broker**. Run the
ingestion modules from a throwaway container attached to the platform network. Kafka and
MinIO both share **`space-ops-net`**, so a single attachment reaches both by DNS
(`kafka:9092`, `minio:9000`).

> Offline development (no infra) still works from the host: `make test` and `make demo`
> exercise the full logical flow in-memory — see [ingestion/README.md](ingestion/README.md).

### One-time: start a reusable ingestion runner

With the `storage` + `ingestion` (and `processing` for Airflow) stacks up (see §2):

```powershell
$REPO = "c:\D Drive\Projects\DE\Projects\space-data-ai-platform"
docker rm -f space-ingest-runner 2>$null
docker run -d --name space-ingest-runner --network space-ops-net `
  -v "${REPO}:/work" -w /work `
  -e KAFKA_BOOTSTRAP=kafka:9092 -e MINIO_ENDPOINT=http://minio:9000 `
  python:3.11-slim sleep infinity
docker exec space-ingest-runner pip install -q -r ingestion/requirements.txt
```

> The runner bind-mounts the repo, so code edits are picked up immediately. Credentials
> (MinIO + API keys) are read from the mounted `infrastructure/env/.env`; the `-e`
> endpoint overrides win because `load_dotenv` runs with `override=False`.

### A) Synthetic streaming pipeline (telemetry → Bronze → cleaned/DLQ)

```powershell
# 1. Create the Kafka topics (idempotent)
docker exec space-ingest-runner python -m ingestion.scripts.create_topics

# 2. Produce N synthetic telemetry records to telemetry.satellite.raw
docker exec space-ingest-runner python -m ingestion.streaming.producers.telemetry_producer --max 300 --rate 200

# 3. Land raw telemetry in Bronze (MinIO). Size the run so it exits cleanly:
#    consumers have no idle timeout, so --max-batches * --batch-size must cover the produced count.
docker exec space-ingest-runner python -m ingestion.streaming.consumers.raw_ingest_consumer --batch-size 100 --max-batches 3

# 4. Validate raw -> cleaned topic / quarantine + DLQ (reads the same topic, different group)
docker exec space-ingest-runner python -m ingestion.streaming.consumers.validation_consumer --max 300
```

### B) API connectors → Bronze (real online sources)

Anonymous sources need no keys; keyed sources read credentials from `infrastructure/env/.env`.

| Connector | Source | Auth |
| --- | --- | --- |
| `PowerConnector` | NASA POWER (daily weather) | anonymous |
| `SwpcConnector` | NOAA SWPC (planetary K-index) | anonymous |
| `CelestrakConnector` | CelesTrak GP/TLE | anonymous |
| `FirmsConnector` | NASA FIRMS / VIIRS active fire | `FIRMS_MAP_KEY` |
| `GfwConnector` | Global Fishing Watch (vessel identity) | `GFW_API_TOKEN` |
| `SentinelHubConnector` | Sentinel Hub Catalog (STAC scene metadata) | `SENTINELHUB_CLIENT_ID` / `_SECRET` |

```powershell
# Land a batch from any connector to Bronze (example: NASA POWER + NOAA SWPC + CelesTrak)
docker exec space-ingest-runner python -c "
from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.api.nasa_power import PowerConnector
from ingestion.api.noaa_swpc import SwpcConnector
from ingestion.api.celestrak import CelestrakConnector
for c in (PowerConnector(), SwpcConnector(), CelestrakConnector()):
    print(run_connector_to_bronze(c))
"

# Keyed sources (keys must be set in infrastructure/env/.env)
docker exec space-ingest-runner python -c "
from ingestion.batch.ingest_task import run_connector_to_bronze
from ingestion.api.nasa_firms import FirmsConnector
from ingestion.api.gfw import GfwConnector
print(run_connector_to_bronze(FirmsConnector(), source='VIIRS_SNPP_NRT', area='-10,-10,10,10', days=1))
print(run_connector_to_bronze(GfwConnector(), query='Maria', limit=20))
"
```

The two frequently-updating sources can instead be **bridged to Kafka** (request/response → stream):

```powershell
docker exec space-ingest-runner python -m ingestion.streaming.producers.api_bridge_producer --source swpc       # -> space.weather.events
docker exec space-ingest-runner python -m ingestion.streaming.producers.api_bridge_producer --source celestrak  # -> orbit.position.stream
```

### Verify the run

```powershell
# Kafka end offsets (message counts) per topic
docker exec space-ingest-runner python -c "
from kafka import KafkaConsumer
from kafka.structs import TopicPartition as TP
c=KafkaConsumer(bootstrap_servers='kafka:9092')
for t in ['telemetry.satellite.raw','telemetry.satellite.cleaned','telemetry.satellite.dlq','space.weather.events','orbit.position.stream']:
    ps=c.partitions_for_topic(t) or set(); tps=[TP(t,p) for p in ps]
    print(t, sum(c.end_offsets(tps).values()) if tps else 0)
c.close()"

# Bronze object counts per source (in MinIO)
docker exec space-ingest-runner python -c "
import boto3; from botocore.config import Config
from ingestion.config.settings import settings as s
cl=boto3.client('s3',endpoint_url=s.minio.endpoint,aws_access_key_id=s.minio.access_key,aws_secret_access_key=s.minio.secret_key,region_name=s.minio.region,config=Config(s3={'addressing_style':'path'}))
for p in ['telemetry/','POWER/','SWPC/','CELESTRAK/','FIRMS/','GFW/','SENTINELHUB/']:
    objs=cl.list_objects_v2(Bucket='bronze',Prefix=p).get('Contents',[])
    print(p, len(objs), 'objs', sum(o['Size'] for o in objs), 'bytes')"
```

You can also browse the landed objects in the **MinIO Console** (§7) under `bronze/<SOURCE>/ingest_date=YYYY-MM-DD/<batch_id>/part-0000.jsonl`, or inspect topics in **Kafka UI** (§9).

### Clean up the runner

```powershell
docker rm -f space-ingest-runner
```

| Symptom | Likely cause / fix |
| --- | --- |
| Producer raises `Unrecognized configs: {'enable_idempotence': True}` | Old code with a config unsupported by `kafka-python==2.0.2`; pull latest (`create_producer` no longer sets it). |
| A consumer **hangs** after draining the topic | Consumers have no idle timeout. Bound them: `raw_ingest_consumer --batch-size B --max-batches N` (cover the produced count) and `validation_consumer --max N`. |
| `NoBrokersAvailable` from the host shell | You ran a module from the laptop, not the runner. Kafka isn't published to the host — run inside `space-ingest-runner` (above). |
| Keyed connector raises `... is not configured` | The API key/secret is missing from `infrastructure/env/.env`. |
| API connector read-timeout | Transient upstream/network issue; the resilient client already retries 4× with backoff. Re-run the connector. |

---

## Phase Status & Changelog

What is operationally available today, and what each future phase will add to this runbook.

| Phase | Adds to this runbook | Status |
| --- | --- | --- |
| 04 / 07 — Infrastructure | Start/stop, status, URLs, PostgreSQL & MinIO access, Kafka basics, lakehouse query *mechanisms* | ✅ Available |
| 08 — Ingestion | §10 runner pattern; live Kafka topics + offset checks; synthetic streaming pipeline; API connectors → Bronze; Bronze object inspection | ✅ Available |
| Transformation | Preconfigured Spark/DuckDB query helpers (no manual `--packages`); Silver/Gold Iceberg tables to query | 🔜 Update §8 |
| AI/ML | MLflow experiment/run queries; Feast feature retrieval; model registry commands | 🔜 Add MLflow section |
| RAG / LLM | Qdrant collection queries; Ollama model pull/run; Open WebUI usage | 🔜 Add LLM section |
| Serving (API) | FastAPI endpoints, auth, example requests | 🔜 Add API section |
| Observability | Grafana dashboards, Prometheus queries, alert checks | 🔜 Expand §3 |

> **Keep this current:** when a phase adds a runnable component, add its start command,
> URL/credentials, and a "how to query it yourself" snippet to the matching section above.
