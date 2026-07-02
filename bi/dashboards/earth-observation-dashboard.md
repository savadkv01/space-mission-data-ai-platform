# Earth Observation Dashboard

> Phase 12 · Task 2 — Dashboard Catalog · Audience: **EO Analysts, Emergency
> Management, Maritime Intelligence** · Superset slug: `earth-observation`
> Roles: `ops_eo`, `ops_maritime` (RLS-scoped) · **MVP-primary dashboard**

## Purpose

The operational heart of the MVP. Combines the four real-data EO/maritime data
products into one investigative surface: wildfire activity, flood extent, imagery
availability/coverage, and maritime risk. Optimised for event triage — detect,
prioritise, review evidence.

## Tabs & Charts

### Tab 1 — Wildfire (dataset `wildfire_daily`, UC-15)

| Chart | Type | Columns |
| --- | --- | --- |
| AOI activity map | deck.gl / geo | `aoi_key`, `detections`, `severity` |
| Severity distribution | pie | `severity` |
| Detections by day | time bar | `event_date`, `detections` |
| Peak FRP by AOI | table | `aoi_name`, `max_frp`, `ems_corroborated` |

### Tab 2 — Flood (dataset `flood_daily`, UC-16)

| Chart | Type | Columns |
| --- | --- | --- |
| NDWI trend per AOI | line | `event_date`, `ndwi_mean`, `aoi_name` |
| Flood-day calendar | calendar heatmap | `event_date`, `flood_flag` |
| Valid-pixel coverage | gauge | `valid_pixel_fraction` |

### Tab 3 — Imagery Coverage (dataset `scene_catalog`, UC-25)

| Chart | Type | Columns |
| --- | --- | --- |
| Image availability by day | time bar | `capture_date` |
| Coverage by collection/provider | bar | `collection`, `provider` |
| Observation frequency | line | `capture_date`, count |
| Geographic distribution | geo | `geo_key` |

### Tab 4 — Maritime (dataset `vessel_activity`, UC-18)  *(RLS: `ops_maritime`)*

| Chart | Type | Columns |
| --- | --- | --- |
| Suspicious vessel queue | table | `vessel_key`, `flag`, `vessel_type`, `review_priority` |
| Suspicious rate trend | line | `activity_date`, `suspicious_flag` |
| Activity by flag | bar | `flag`, `transmissions` |

## Layout (wireframe — Wildfire tab)

```
+---------------------------------------------------------------+
| EARTH OBSERVATION  [Wildfire][Flood][Imagery][Maritime]  [▾]  |
+-------------------------------+-------------------------------+
|  AOI Activity Map             | Severity distribution         |
|  (detections, severity)       |  extreme/high/moderate/low    |
+-------------------------------+-------------------------------+
|  Detections by day (bar)                                      |
+---------------------------------------------------------------+
|  Peak FRP by AOI  (table, ems_corroborated ✓/✗)              |
+---------------------------------------------------------------+
```

## Filters & Cross-filtering

- Global time range + AOI selector (`aoi_key`) shared across Wildfire/Flood tabs.
- Clicking a severity slice cross-filters the map and detection bar.
- Collection filter on the Imagery tab.

## Drill-down

- AOI row → `aoi_validation` trust detail (is this detection EMS-corroborated?).
- Suspicious vessel row → vessel activity history (all days for `vessel_key`).

## Alignment

- MVP use cases UC-15/16/18/25 (see
  [../../docs/business/05-mvp-definition.md](../../docs/business/05-mvp-definition.md)).
- Maritime (UC-18) is folded into this dashboard as Tab 4 with RLS so
  `ops_maritime` sees only maritime data, `ops_eo` sees only EO tabs.
