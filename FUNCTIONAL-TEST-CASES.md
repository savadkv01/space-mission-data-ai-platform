# Functional Test Cases — Business Use-Case Acceptance

Business-level (functional) acceptance tests for the Space Mission Data & AI Platform.
These validate **business outcomes and decision workflows** — "does the platform produce the
right operational answer for each use case?" — **not** code syntax, unit logic, or infrastructure
health (those are covered by `make test`, dbt schema tests, and Phase 21 testing).

**Scope:** MVP Earth-Observation & Maritime use cases (⭐), Simulation-track demonstrators (🔄),
and planned Climate/AI use cases (📐, authored not built).

**Traceability:** each test links to a use case ([docs/business/04-use-case-ranking.md](docs/business/04-use-case-ranking.md))
and a KPI ([bi/kpis/kpi-catalog.md](bi/kpis/kpi-catalog.md)). Data objects referenced here are
catalogued in [DATA-INVENTORY.md](DATA-INVENTORY.md).

---

## How to read a test case

| Field | Meaning |
| --- | --- |
| **ID** | `FT-<area>-<n>` stable identifier |
| **Given / When / Then** | Business precondition → action/observation → expected operational outcome |
| **Acceptance** | Objective pass criteria (KPI value, band, flag, or decision) |
| **UC / KPI** | Traceability to business use case and KPI |
| **Priority** | P1 critical business path · P2 important · P3 supporting |

**Pass/Fail rule:** a test passes only when the **Then** and **Acceptance** both hold on the
certified serving product / BI dataset (not on raw Bronze). A misleading `0` where input is empty
is a **fail** — empty input must surface as "no data", never a false zero.

---

## Traceability Matrix

| Use Case | ID | Suite | Primary KPI | Product/Dataset |
| --- | --- | --- | --- | --- |
| UC-15 Wildfire detection & progression | FT-FIRE-* | Wildfire | Total Fire Detections, Mean FRP | `serving_wildfire_daily` |
| UC-16 Flood monitoring & impact | FT-FLOOD-* | Flood | Flood Day Rate | `serving_flood_daily` |
| UC-18 Illegal fishing detection | FT-VESSEL-* | Maritime | Suspicious Vessel Rate | `serving_vessel_activity` |
| UC-27 Disaster damage prioritization | FT-AOI-* | Validation | EMS Corroboration Rate | `serving_aoi_validation` |
| UC-14 EO change detection | FT-CHANGE-* | Change | NDVI/NBR change | `obs_index` / marts |
| UC-25 Image metadata & catalog | FT-CAT-* | Catalog | Searchable Scene Rate | `serving_scene_catalog` |
| Cross-product executive view | FT-EXEC-* | Executive | Platform daily rollup | `mv_kpi_platform_daily` |
| Trust / freshness / access | FT-TRUST-* | Governance | Freshness, RLS | multiple |
| Sim: satellite / launch / weather | FT-SIM-* | Simulation | Health, Launch, Storm | sim products |
| Planned: climate / dust / AQ | FT-CLIM-* | Climate 📐 | AQI, AOD, LST anomaly | planned marts |

---

## Suite 1 — Wildfire Monitoring (UC-15) ⭐

| ID | Given | When | Then (business outcome) | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-FIRE-01 | A monitored AOI has ≥1 satellite fire detection on day D | An analyst opens the wildfire product for AOI/day D | Detection count for that AOI-day equals the number of real detections | `detection_count` matches source count; 1 row per AOI-day (no duplicates) | P1 |
| FT-FIRE-02 | An AOI-day contains a very intense fire (`max_frp ≥ 100`) | The severity band is computed | The AOI-day is classified **extreme** and prioritized for response | severity = extreme (≥100) / high (≥30) / moderate (≥10) bands correct | P1 |
| FT-FIRE-03 | Today's detections for an AOI exceed 3× its trailing 7-day mean | The wildfire KPI refreshes | The AOI is surfaced as an **amber spike** for operator attention | Day-over-day spike >3× 7-day mean → amber flag raised | P2 |
| FT-FIRE-04 | An AOI has no fire activity on day D | The analyst views AOI/day D | The AOI shows **no detections** (not a missing/false value) | Empty input → "no data"/0 detections explicitly, never null-as-error | P2 |
| FT-FIRE-05 | Fire detections exist inside and outside an AOI polygon | Point-in-polygon attribution runs | Only detections **within** the AOI are counted for that AOI | Detections outside polygon excluded; boundary correctness | P1 |

---

## Suite 2 — Flood Monitoring & Impact (UC-16) ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-FLOOD-01 | A scene over an AOI has open water above the NDWI threshold | The flood product is built for that AOI-day | The AOI-day is flagged **flooded** | `flood_flag = true` when NDWI ≥ threshold; else false | P1 |
| FT-FLOOD-02 | A scene is largely cloud-covered / low valid-pixel fraction | The analyst reviews flood evidence | The result is marked **low-confidence** (insufficient valid pixels) | `valid_pixel_fraction` surfaced; low coverage does not assert a flood | P1 |
| FT-FLOOD-03 | Several AOI-days over a week are flooded | The Flood Day Rate KPI is computed | Emergency-management sees the **share of flooded AOI-days** rising | `flood_day_rate = avg(flood_flag)`; trend visible on dashboard | P2 |
| FT-FLOOD-04 | Before/after scenes span a flood event | The analyst compares the two dates | Water extent **increase** is evident between the dates | NDWI/extent after > before for the affected AOI | P2 |

---

## Suite 3 — Illegal Fishing / Maritime (UC-18) ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-VESSEL-01 | A vessel exhibits the illegal-fishing heuristic pattern on day D | The vessel activity product is built | That vessel-day is flagged **suspicious** and enters the triage queue | `suspicious_flag = true`; `review_priority = high` | P1 |
| FT-VESSEL-02 | A normal transiting vessel on day D | The product is built | The vessel-day is **not** flagged suspicious | `suspicious_flag = false`; not in high-priority queue | P1 |
| FT-VESSEL-03 | A maritime analyst without global scope is assigned a region | The analyst opens the vessel dashboard | They see **only vessels within their permitted scope** (RLS) | Row-level security filters out-of-scope vessels; no leakage | P1 |
| FT-VESSEL-04 | Suspicious detections spike above baseline | The Suspicious Vessel Rate KPI refreshes | Enforcement sees an **amber** signal to expand triage | `suspicious_vessel_rate` spike → amber; queue populated | P2 |

---

## Suite 4 — Disaster Damage Prioritization / Validation (UC-27) ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-AOI-01 | An AOI's detections align with a Copernicus-EMS activation | The AOI validation product is built | The AOI is marked **EMS-corroborated** (trusted) | `corroborated = true` when EMS ground truth agrees | P1 |
| FT-AOI-02 | Across all EMS AOIs, most detections are corroborated | The EMS Corroboration Rate KPI is computed | The executive trust KPI shows **green** | `corroboration_rate ≥ 0.8` green / 0.6–0.8 amber / <0.6 red | P1 |
| FT-AOI-03 | Detections in an AOI are **not** corroborated by EMS | Validation runs | The AOI is flagged for **QA / possible false positive** | `corroborated = false`; surfaced for review | P2 |
| FT-AOI-04 | Multiple hazards affect several AOIs | The responder opens the prioritization view | AOIs are **ranked** by corroborated evidence for response ordering | AOIs ordered by corroboration + evidence days | P2 |

---

## Suite 5 — EO Change Detection (UC-14) ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-CHANGE-01 | Two dated observations of an AOI with real land change | Change detection compares the indices | A **meaningful change** is reported (e.g. NDVI/NBR delta) | Index delta exceeds change threshold; direction correct | P2 |
| FT-CHANGE-02 | Two near-identical observations (no real change) | Change detection runs | **No significant change** is reported (no false alarm) | Delta below threshold → no change event | P2 |
| FT-CHANGE-03 | A post-fire scene vs pre-fire scene | NBR-based burn severity is derived | **Burned area / severity** is identified for the AOI | NBR drop maps to burn-severity band | P3 |

---

## Suite 6 — Image Metadata Quality & Catalog (UC-25) ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-CAT-01 | A scene has complete required metadata | The catalog product is built | The scene is **searchable/discoverable** | `is_searchable = true`; appears in catalog search | P1 |
| FT-CAT-02 | A scene is missing required metadata | The catalog product is built | The scene is marked **not searchable** and counted against quality | `is_searchable = false`; excluded from searchable rate | P1 |
| FT-CAT-03 | A collection's scenes are mostly complete | Searchable Scene Rate is computed | Data steward sees a **green** discoverability KPI | `searchable_rate ≥ 0.9` green / 0.75–0.9 amber / <0.75 red | P1 |
| FT-CAT-04 | An analyst searches by AOI + date + cloud-cover | The catalog is queried | Matching scenes are **returned and filterable** | Query returns correct scenes; filters honored | P2 |

---

## Suite 7 — Executive & Cross-Product View ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-EXEC-01 | A day with activity across fire/flood/vessel/catalog | Leadership opens the Executive dashboard | A **single daily rollup** shows all headline KPIs consistently | `mv_kpi_platform_daily` = 1 row/day; values match source products | P1 |
| FT-EXEC-02 | The same KPI appears on BI, API, and (future) RAG | Each surface displays the KPI | All surfaces show the **identical certified value** | Semantic-layer single-source; no divergence across surfaces | P1 |
| FT-EXEC-03 | A KPI has no data for the selected day | The tile renders | The tile shows **"no data"**, not a misleading `0` | Empty → None/no-data, never false zero | P2 |

---

## Suite 8 — Trust, Freshness & Access Governance ⭐

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-TRUST-01 | Serving products refreshed on schedule | Freshness is measured | Insight is **timely** for operations | Data Freshness ≤ 60 min → green | P1 |
| FT-TRUST-02 | Ingestion/transformation DAGs run for the day | Pipeline success is measured | The platform is **reliable** | Pipeline Success Rate ≥ 0.98 | P2 |
| FT-TRUST-03 | Serving APIs under normal load | SLA compliance is measured | Consumers meet **service commitments** | SLA compliance ≥ 0.99 | P2 |
| FT-TRUST-04 | A restricted maritime dataset and a scoped user | User queries via BI/API | Access is **limited to permitted rows** | RLS enforced; unauthorized rows never returned | P1 |
| FT-TRUST-05 | A KPI not registered in the semantic layer is requested | The request executes | The system **fails fast**, no silent empty result | Unregistered KPI → explicit error, not empty | P2 |

---

## Suite 9 — Simulation Track (post-MVP demonstrator) 🔄

> Synthetic data (ADR-09). Functional intent only; not business-validated against real ground truth.

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-SIM-01 | Synthetic telemetry for a satellite over a day | Health scoring runs | The satellite gets a **daily health score + status band** | `health_score` present; ≥0.8 = nominal | P3 |
| FT-SIM-02 | A 1-minute telemetry window with injected anomalies | Streaming aggregation runs | Near-real-time **anomaly rate** is reported per minute | `stream_sat_health_1m` = 1 row/sat/min; anomaly rate reflects injection | P3 |
| FT-SIM-03 | A month of synthetic launches for a provider | Launch rollup runs | Monthly **success rate** is reported per provider | `success_rate` computed; ≥0.9 threshold banding | P3 |
| FT-SIM-04 | A geomagnetic storm window (Kp ≥ 5) | Weather-impact correlation runs | **Storm days** are flagged and correlated with anomalies | `count(max_kp_index ≥ 5)` ≥ threshold → alert | P3 |

---

## Suite 10 — Planned: Climate / Dust / Air-Quality (authored, not built) 📐

> Will become active when extension prompts `05b`–`16b` are executed (see [README.md](README.md#planned-expansion--climate-dust--air-quality-monitoring)).

| ID | Given | When | Then | Acceptance | Pri |
| --- | --- | --- | --- | --- | --- |
| FT-CLIM-01 | Pollutant readings for an AOI/day (OpenAQ + TROPOMI) | The air-quality product is built | The AOI-day shows **pollutant means + AQI band + exceedance flag** | AQI band per breakpoints; exceedance flag correct | P2 |
| FT-CLIM-02 | High aerosol (AOD) with dust-favorable wind | The dust product is built | The AOI-day is flagged a **dust event** with transport context | `dust_flag = true` above AOD threshold; wind context present | P2 |
| FT-CLIM-03 | Multi-year LST for an AOI | Climate indicators are built | An **LST anomaly** vs baseline is reported | Anomaly band correct (°C above baseline) | P2 |
| FT-CLIM-04 | Satellite AOD + co-located ground PM (OpenAQ) | The AOD→PM model infers | A calibrated **PM2.5/PM10 estimate** is produced | Prediction within model MAE gate vs ground truth | P3 |
| FT-CLIM-05 | New Gold climate products exist | An analyst asks for an environmental report (RAG) | A **grounded, cited climate summary** is returned | Answer cites AOI/date/metric; no ungrounded numbers | P3 |

---

## Execution & Reporting

- **Environment:** run against the certified serving products / BI datasets (post-Gold), using a
  known fixture window (e.g. a real Copernicus-EMS activation date) as ground truth for corroboration tests.
- **Cadence:** run the MVP suites (1–8) each release; sim suite (9) on demo builds; climate suite (10)
  activates after the respective `*b` phase completes.
- **Result record (per test):** ID · date · build/commit · Pass/Fail · observed value vs acceptance · notes.
- **Definition of release-ready:** all **P1** MVP tests pass; no P1 regression; open P2/P3 tracked.

| Suite | Tests | Priority focus |
| --- | --- | --- |
| Wildfire / Flood / Maritime / Validation | 17 | P1 core decision paths |
| Change / Catalog / Executive / Governance | 15 | P1–P2 reusable + trust |
| Simulation | 4 | P3 demonstrator |
| Climate (planned) | 5 | P2–P3 future |
