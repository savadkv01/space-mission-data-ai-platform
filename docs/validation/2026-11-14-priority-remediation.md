# Priority Remediation — 2026-11-14

> **Superseded evidence:** vegetation, flood and climate-indicator figures below
> were computed on sign-inverted GEE indices (SG-01, fixed later the same day).
> See [2026-11-14-india-regional-e2e.md](./2026-11-14-india-regional-e2e.md) for
> corrected results. The contract changes in this document are unaffected.

Remediation of five priority insights raised by data analysis, verified against
the [2026-11-01 end-to-end readiness assessment](./2026-11-01-end-to-end-readiness.md)
and re-checked against the live lake on 2026-11-14.

> **Scope.** Serving-contract and pipeline-assertion fixes only. No Gold schema,
> source, or dataset scope was changed. Domain certification is still pending
> for every product listed here.

---

## 1. Verification of the Insights

| # | Insight | Prior evidence | Re-verified 2026-11-14 | Verdict |
|---|---|---|---|---|
| 1 | Streaming field contract drops anomaly labels | V01: 0/60 anomaly contributions | [Validation consumer](../../ingestion/streaming/consumers/validation_consumer.py) forwards generator records unchanged; `health` / `label_anomaly` are nested under `metadata`, while [the Spark parser](../../transformation/streaming/spark_streaming.py) read root fields only, so it always parsed `null`. | **Confirmed** |
| 2 | Wildfire results must be blocked/stale until FIRMS freshness passes | V09: 6.306 h > 6 h objective | Latest acquired FIRMS detection `2026-10-31T14:20Z`, ~339.6 h old; serving still published 10 rows with no freshness signal. [The FIRMS connector](../../ingestion/api/nasa_firms.py) also recorded *any* non-CSV body (for example an invalid key) as "no fire rows". | **Confirmed**, plus a connector defect |
| 3 | Missing measurements look like negatives in AQ / dust / climate | V05, §4.2–4.5 | Serving coerced Gold `false`/missing to `False`. Live rebuild shows 96 AQ AOI-days with no surface PM and all 55 climate rows without LST/SST anomalies. | **Confirmed** |
| 4 | Vessel alerts are triage signals pending domain review | V12, §4.5 | `review_priority = 'high'` was published with no basis or review state (85 of 101 vessel-days are high in the current build). | **Confirmed** |
| 5 | Zero-row launch mart is unavailable data, not zero launches | V13 | `kpi_launch_monthly` has 0 rows; BI `SUM(launches)` returned 0, and the run log recorded `SUCCESS rows=0` with no availability state. | **Confirmed** |

---

## 2. Changes and Design Decisions

### 2.1 Streaming field contract (insight 1)

| Item | Detail |
|---|---|
| Change | `STREAM_FIELD_PATHS` in [spark_streaming.py](../../transformation/streaming/spark_streaming.py) is the single contract: `metadata.<field>` first, root as fallback. The Spark parser (`parse_telemetry_json`) and a pure-Python reference (`extract_stream_fields`) both read it. |
| End-to-end assertion | The [streaming DAG](../../pipelines/dags/streaming_pipeline_dag.py) injects a deterministic all-anomalous wave 1 (`failure_rate = 1.0`) and an all-nominal wave 2 (`0.0`). It then requires Silver `anomaly_samples >= 60` and zero mixed windows; otherwise the unit and stage fail. |
| Why | The generator contract is the source of truth. Parsing it instead of flattening in the validation consumer avoids a raw-versus-cleaned schema fork. |
| Alternatives | Flatten in the validation consumer; change the generator to root fields. Both break existing Bronze/raw consumers or historical topic data. |
| Trade-off | Dual-path coalescing keeps legacy flat demo NDJSON working, but a record with conflicting nested and root values silently prefers nested. |

### 2.2 Wildfire freshness gate (insight 2)

| Item | Detail |
|---|---|
| Change | New one-row `serving_wildfire_freshness` model (Gold `fire_aoi_attribution` event time). Every `serving_wildfire_daily` row carries `latest_observation_ts`, `observation_age_hours`, `freshness_status` (`current` / `stale` / `no_observations`) and `publication_status` (`exploratory` / `blocked`). |
| Query-time re-evaluation | The Superset `wildfire_daily` dataset recomputes age against `now()`, so a materialized table cannot look current after it ages. |
| Zero records | A header-only FIRMS CSV is the only valid zero-detection response. Any other body fails the source. Zero-row sources/marts are logged with `data_availability = unavailable`. |
| Why | Event-time freshness separates provider latency from landing success (V09). A product-level row keeps an empty feed visible instead of disappearing. |
| Alternatives | Fail the serving build when stale; this hides all evidence and blocks unrelated products. Delete stale rows; absence would then read as "no fire". |
| Trade-off | Stale rows remain queryable, so consumers must honour `publication_status`; dashboards should filter or banner on it. |

### 2.3 Evidence states for AQ / dust / climate (insight 3)

Serving now publishes `<flag>_status ∈ {positive, negative, inconclusive, not_evaluated}`;
the flag is `true` / `false` only when evidence decides it, otherwise `NULL`.
Gold flags are unchanged. Rule semantics are documented in
[climate-products.md](../../serving/products/climate-products.md#evidence-states-air-quality-dust-climate).
`pm_coverage` and the `*_evaluated_aois` rollup counts expose coverage.

| Decision | Rationale | Alternative rejected | Trade-off |
|---|---|---|---|
| Fix at serving, not Gold | Gold Spark schemas/readers stay stable; serving already carries every input measurement | Tri-state Gold booleans | Gold still collapses states; non-serving Gold readers must apply the same rule |
| Shared dbt macro + Python mirror | One rule for dbt, Python, SQL DDL, BI | Per-model CASE copies | Thresholds are duplicated as literals in SQL; parity is pinned by a test |
| Inland SST stays `inconclusive` | No approved AOI applicability rule | Treat missing SST as negative inland | Warming rarely reaches `negative` until an applicability rule is approved |

### 2.4 Vessel triage labelling (insight 4)

`serving_vessel_activity` adds `signal_basis = 'identity_completeness_heuristic'`
and `domain_review_status = 'pending'`. `review_priority` is kept as a triage queue
priority. The dbt and dataset descriptions state that this is not verified
illegal-fishing evidence. **Alternative:** rename or suppress flags; rejected as
a breaking change before domain review.

### 2.5 Launch availability (insight 5)

`launch_monthly_availability()` reports `unavailable` for an empty mart. The
Superset dataset returns one `data_availability = 'unavailable'` row with NULL
measures (`SUM(launches)` → NULL, not 0). The batch DAG labels empty Gold marts.
Launch input wiring itself remains out of scope (V11/V13).

---

## 3. Validation Results

| Check | Result |
|---|---|
| Python suites (serving, pipelines, transformation, ingestion, Power BI builder) | 290 passed |
| Spark runtime parser (spark-master, Python 3.10) | 7/7 labels resolved (6 nested + 1 flat fallback); previously nested labels parsed `null` |
| Serving dbt against live Gold | 15/15 models built, 83/83 tests passed (including new status, freshness, and single-row tests) |
| Superset dataset SQL against rebuilt warehouse | All 7 touched datasets execute; declared columns match |
| Live streaming acceptance (bounded, DAG callables) | See §3.1 |

**Live product state after rebuild:**

| Product | Result |
|---|---|
| Wildfire | `stale` / `blocked` on all 10 rows; latest observation 339.6 h old |
| Air quality (173 AOI-days) | 72 positive, 2 negative, 3 inconclusive, **96 not_evaluated** (were `false`) |
| Dust (161 AOI-days) | 161 negative: AOD below 0.5 is a decided negative under the AND rule |
| Climate (55 AOI-days) | Warming **55 not_evaluated** (were `false`); desertification 20 positive / 30 negative / 5 not_evaluated |
| Vegetation (55 AOI-days) | Trend: 25 declining, 25 improving, **5 unknown** (were `flat`); crop stress 25 positive / 25 negative / **5 inconclusive** (were `false`) |
| Vessel (101 vessel-days) | 85 high / 16 normal, all `pending` domain review |
| Launch | One `unavailable` row; `SUM(launches)` = NULL |

### 3.1 Live streaming acceptance

The Airflow container was restart-looping during this session (pre-existing
V10). The `platform_streaming_pipeline` callables were therefore executed in DAG
order from a one-off container built from the Airflow image. Only the Postgres
run-logger was replaced by console output.

| Unit | Result |
|---|---|
| `telemetry_produce` (wave 1, `failure_rate = 1.0`) | 60 records, 60 injected anomalies |
| `raw_ingest_consumer` / `validation_consumer` | 60 to Bronze; 60 valid, 0 invalid to cleaned |
| `telemetry_produce_wave_2` (`failure_rate = 0.0`) | 30 produced and validated |
| `stream_sat_health_1m` | **SUCCESS**: 6 windows, 120 samples, **120 anomaly contributions** (60 records × 2 sliding windows), 0 mixed windows |

On 2026-11-01 the same path produced 0/60 anomaly contributions.

---

## 4. KPIs

| KPI | Target | Current |
|---|---|---|
| Injected-anomaly survival into Silver windows | ≥ 1 contribution per injected record; 0 mixed windows | 120 / 60 minimum; 0 mixed (live) |
| Wildfire rows published while FIRMS > 6 h old | 0 rows with `publication_status = 'exploratory'` | 0 |
| Climate-family flags `false` without deciding evidence | 0 | 0 (enforced by status contract) |
| Vessel rows without review state | 0 | 0 |
| Empty marts reported as zero | 0 | 0 (launch → `unavailable`) |

## 5. Risks and Follow-ups

| Risk / follow-up | Owner | Note |
|---|---|---|
| Power BI semantic model is generated from the Superset YAMLs and is not regenerated here | BI | Re-run `bi/powerbi/build_report.py` |
| Dashboards/alerts must filter on `publication_status` and `*_status` | BI / Ops | [alert-strategy.md](../../bi/alerts/alert-strategy.md) rules still key on flags; NULL no longer fires a false negative, but alert copy should cite status |
| Vegetation `ndvi_trend_dir = 'flat'` for missing trend (V05) | Climate analytics | **Resolved 2026-11-14:** missing trend → `unknown`; `crop_stress_status` added (same evidence states). The 30-observation (not 30-calendar-day) slope and missing crop mask remain open |
| Airflow restart loop (V10) | Platform | Blocks orchestrated acceptance evidence |
| Domain approval for all products | Domain owners | Unchanged |

## 6. Glossary

| Term | Definition |
|---|---|
| Evidence status | Whether available measurements decide a rule: `positive`, `negative`, `inconclusive`, or `not_evaluated`. |
| Publication status | `exploratory` when the freshness gate passes; otherwise `blocked`. Never a domain certification. |
| Event-time freshness | Age of the latest acquired observation, independent of landing time. |
| Data availability | `unavailable` means no rows or input exists; it is not a measured zero. |
| Triage signal | A heuristic prompt for analyst review, not verified evidence. |
