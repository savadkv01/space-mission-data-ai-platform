# Retry, Rate Limiting & Backoff

Implemented in [common/http.py](../common/http.py). Narrative: [docs/ingestion/04-api-ingestion.md](../../docs/ingestion/04-api-ingestion.md), [docs/ingestion/10-error-handling.md](../../docs/ingestion/10-error-handling.md).

| Concern | Strategy |
| --- | --- |
| Retry | `urllib3.Retry` total=4 on 429/5xx |
| Backoff | exponential (`backoff_factor=0.8`), honours `Retry-After` |
| Rate limit | sliding-window `RateLimiter` per connector (calls/sec) |
| Timeout | 30 s per request |
| Fallback | exhaustion → raise → Airflow retry/backoff; partial batch still lands in Bronze |

Per-connector limits: FIRMS 2/s, POWER 3/s, SWPC 3/s, CelesTrak 1/s (fair-use).
