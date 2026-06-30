# Scheduling Strategy

| DAG | Schedule | Increment |
| --- | --- | --- |
| FIRMS | `@hourly` | trailing 1-day window per region |
| SWPC | `*/15 * * * *` | latest snapshot |
| CelesTrak | `0 */6 * * *` | per-group refresh |
| POWER | `@daily` | trailing 7-day window per point |

## Retry / backoff (all DAGs)
- retries=3, exponential backoff (2 min → 30 min cap), `catchup=False`.
- Idempotent: each run tags a new `batch_id`; Bronze is append-only → safe re-runs.

Defaults: [dags/_defaults.py](dags/_defaults.py) · narrative: [docs/ingestion/03-batch-design.md](../../docs/ingestion/03-batch-design.md).
