# Statistics Framework

> The concrete metric definitions behind [profiling-strategy.md](profiling-strategy.md).
> These are the exact quantities the profiler emits and the monitoring layer
> alerts on.

---

## 1. Per-column statistics

| Statistic | Definition | Applies to |
|-----------|------------|------------|
| `count` | Non-null values | all |
| `total` | Rows in batch | all |
| `null_pct` | `1 − count/total` | all |
| `distinct` | Distinct non-null values | all |
| `cardinality_ratio` | `distinct / count` | all |
| `min`, `max` | Range | numeric, temporal |
| `mean` | Arithmetic mean | numeric |
| `median` (p50) | 50th percentile | numeric |
| `stddev` | Sample standard deviation | numeric |
| `p05,p25,p75,p95` | Quantiles | numeric |
| `top_k` | K most frequent values + share | categorical |

---

## 2. Outlier detection

**IQR fence (default):**

$$\text{lower} = Q_1 - 1.5 \cdot (Q_3 - Q_1), \quad \text{upper} = Q_3 + 1.5 \cdot (Q_3 - Q_1)$$

**Z-score (near-normal signals such as battery voltage):**

$$z = \frac{x - \mu}{\sigma}, \quad \text{flag if } |z| > 3$$

Outlier **rate** per column is itself a monitored metric: a spike in outlier
rate is an early corruption signal.

---

## 3. Drift indicators

**Population Stability Index (PSI)** for a numeric/binned column vs baseline:

$$\text{PSI} = \sum_{i=1}^{b} \left( a_i - e_i \right) \cdot \ln\!\left(\frac{a_i}{e_i}\right)$$

where $a_i$ = actual share in bin $i$, $e_i$ = expected (baseline) share.

| PSI | Interpretation | Action |
|-----|----------------|--------|
| `< 0.1` | No significant shift | none |
| `0.1 – 0.25` | Moderate shift | warn, review |
| `> 0.25` | Major shift | alert, block certification |

**Categorical share shift** (for `flag`, `collection`, `index`, `event_type`):
absolute change in category share vs baseline; a new/disappeared category is
treated as a schema-evolution signal.

---

## 4. Freshness & volume statistics

| Metric | Definition | Threshold source |
|--------|------------|------------------|
| `freshness_lag` | `now − max(event_ts)` | SLA table ([../monitoring/quality-kpis.md](../monitoring/quality-kpis.md)) |
| `volume_delta` | `rows_today / mean(rows_prev_7d)` | `< 0.5` or `> 2.0` ⇒ alert |
| `late_arrival_pct` | share of rows with `event_ts < batch_window_start` | `> 5%` ⇒ warn |

---

## 5. Reference thresholds (initial, refined by observed profiles)

| Entity.column | Baseline expectation |
|---------------|----------------------|
| `silver_fire.frp` | `≥ 0`; p95 warn band tuned from profile |
| `silver_index.mean` (NDVI/NDWI/NBR) | `[-1, 1]` |
| `silver_index.valid_pixel_fraction` | `≥ 0.2` warn, `≥ 0.5` for flood use |
| `silver_scene.cloud_cover` | `[0, 100]` |
| `silver_scene.completeness_score` | `≥ 0.8` certified |
| `silver_vessel.flag null_pct` | `< 20%` (else suspicious-share alert) |
| `silver_space_weather.kp_index` | `[0, 9]` |

---

## 6. Implementation note

The statistics above are dependency-free and computable in a single pass on a
laptop. For large partitions the profiler samples (reservoir sampling for
quantiles) to stay within 16 GB RAM. Emitted profiles map 1:1 to the Prometheus
metrics in [../monitoring/monitoring-strategy.md](../monitoring/monitoring-strategy.md).
