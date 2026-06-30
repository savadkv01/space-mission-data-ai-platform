# 12 - Latency Strategy

> **Phase 8 - Data Ingestion** · Document 12 of 17

## Purpose

Define ingestion latency targets and the trade-offs between latency, cost, and complexity.

## Targets

| Path | Target | Driver |
| --- | --- | --- |
| Streaming telemetry | **< 5 s** producer → Bronze | operational alerting |
| Space weather events | < 1 min | near-real-time feed |
| Orbit updates | minutes | TLE cadence |
| Batch API (FIRMS/SWPC) | 15 min – 1 h | source NRT cadence |
| Batch weather (POWER) | daily | daily product |

## How Targets Are Met

- Low `linger_ms` (50 ms) + gzip balances batching vs latency on the producer.
- Separate raw writer commits quickly; validation runs in parallel.
- Bronze write batches sized to keep p95 within target without tiny-file blowup.

## Trade-offs

| Lower latency | Higher latency |
| --- | --- |
| smaller batches, more requests | larger batches, fewer requests |
| more CPU/network | cheaper, simpler |
| better for alerts | fine for archives |

On a 16 GB laptop we keep telemetry hot (small batches) but let imagery/weather run as larger, cheaper batch pulls.

## Cross References

- [11-observability.md](11-observability.md) · [13-scalability.md](13-scalability.md) · [15-trade-offs.md](15-trade-offs.md)
