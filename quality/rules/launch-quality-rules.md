# Launch Events — Data Quality Rules

> **Track:** Simulation (post-MVP). Launch events feed the launch-performance
> demonstrator (`kpi_launch_monthly`). Retained for realism, not on the MVP
> critical path (ADR-09).

Entity: `silver_launch` (natural key `launch_id`, or `provider` + `event_ts`).

---

## Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `event_ts` | ISO-8601 UTC | Non-null, parseable (launch datetime) |
| `provider` | string | Non-null; controlled vocabulary |
| `success` | bool | Non-null (outcome flag) |

## Optional fields

| Field | Type | Rule |
|-------|------|------|
| `mission_name` | string | Trimmed |
| `vehicle` | string | Controlled vocabulary |
| `delay_days` | float | `≥ 0` |
| `mission_completion_ts` | ISO-8601 | If present, `≥ event_ts` |

## Accepted ranges

| Signal | Range |
|--------|-------|
| `delay_days` | `[0, 3650]` |
| `success` | `{true, false}` |

## Referential integrity, duplicates, timestamp, geospatial

- **Duplicate rule:** `launch_id` unique; identical `(provider, event_ts,
  mission_name)` collapse to one event (guards against duplicate launch feeds).
- **Timestamp rule:** `launch_date` cannot occur **after** mission completion;
  `mission_completion_ts ≥ event_ts`.
- **Integrity rule:** each launch references a known provider; a mission maps to
  exactly one launch event.
- **Geospatial:** launch site coordinates (if present) within earth bounds.

**Business impact of failure:** duplicate or misdated launches distort provider
success rate and monthly cadence KPIs.
