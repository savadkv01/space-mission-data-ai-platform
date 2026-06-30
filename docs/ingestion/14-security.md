# 14 - Security in Ingestion

> **Phase 8 - Data Ingestion** · Document 14 of 17

## Purpose

Define how the ingestion layer handles authentication, credentials, network isolation, and boundary protection. Aligns with [architecture/09-security-architecture.md](../../architecture/09-security-architecture.md).

## API Authentication Handling

| Source | Auth | Storage |
| --- | --- | --- |
| FIRMS | `FIRMS_MAP_KEY` | `infrastructure/env/.env` (git-ignored) |
| Sentinel Hub | OAuth client credentials | `.env` |
| GFW | bearer token | `.env` |
| POWER / SWPC / CelesTrak | anonymous | — |

Credentials are read via [`settings.py`](../../ingestion/config/settings.py); **no secret is ever hard-coded** and `.env` is git-ignored.

## Secure Ingestion Credentials

- One source of truth: `infrastructure/env/.env`.
- Verified out-of-band by [tools/datasource-preflight](../../tools/datasource-preflight/) before use.
- Pre-flight and ingestion both ignore `.env` / `output/` in `.gitignore`.

## Internal Network Isolation

Docker Compose networks segment traffic (`stream-net`, `data-net`, `ops-net`, `edge-net`). Kafka/MinIO are reachable only on internal networks; only required ports are published for local dev.

## Ingestion Boundary Protection

| Boundary | Control |
| --- | --- |
| Inbound API responses | treated as untrusted; validated before promotion |
| Payload integrity | `_checksum` (SHA-256) on every Bronze record |
| Injection / malformed data | schema + range + geo validation, quarantine |
| Rate abuse | per-connector rate limiting (good citizenship) |

## Cross References

- [04-api-ingestion.md](04-api-ingestion.md) · [09-data-quality.md](09-data-quality.md)
