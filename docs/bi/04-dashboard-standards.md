# 04 — Dashboard Design Standards

> Phase 12 · Task 4 — Dashboard Design Standards

Consistent standards so every dashboard is readable, accessible, and behaves
predictably regardless of author.

## Layout

- **F-pattern**: KPI tiles top row, trends middle, detail tables bottom.
- **12-column grid**; tiles span 3–4 columns, trends 6–12, tables 12.
- Max **6 KPI tiles** per header row (executive discipline — see business KPIs).
- One dashboard = one audience = one RBAC role.

## Navigation

- Dashboards grouped into folders by track: `MVP`, `Platform`, `Sim`.
- Every operational chart drills to the relevant detail dashboard.
- Breadcrumb: Executive → EO → AOI detail → validation.

## Filters

- A **global time range** native filter on every dashboard (default: last 30 days;
  Platform Ops: 24 h).
- Shared entity filters (`aoi_name`, `collection`, `flag`) as native filters so
  they cross-apply to every chart on the tab.
- Filters bind to the certified dataset columns — never to ad-hoc SQL.

## Drill-down & Cross-filtering

- **Cross-filtering enabled**: clicking a severity slice filters the map + bars.
- **Drill-down** paths documented per dashboard in
  [`bi/dashboards/`](../../bi/dashboards/).
- Drill-through to a row-level table is always available for auditability.

## Accessibility

| Requirement | Standard |
| --- | --- |
| Colour | Never colour-only encoding; pair colour with icon/label |
| Contrast | WCAG AA (≥4.5:1 text) |
| Colour-blind | Use a CVD-safe palette; severity uses shape + colour |
| Font | ≥12px body, ≥24px KPI numbers |
| Keyboard | All filters keyboard-navigable (Superset default) |

## Colour Conventions

| Meaning | Colour | Applies to |
| --- | --- | --- |
| Good / nominal / corroborated | green | status, trust, SLA-met |
| Warning / degraded / amber band | amber | thresholds near breach |
| Critical / extreme / breach | red | severity extreme, SLA breach |
| Informational / sim | grey/blue + `sim` tag | simulation-track charts |
| Flood / water | blue | NDWI, flood-day |
| Fire | orange-red | detections, FRP |

## Time Filtering

- All time columns are named `*_date` and typed `DATE` in the certified datasets.
- Default grain: day. Executive trends: last 30 days; Platform: last 24 h/7 d.
- Sim launch is month-grain (`month_key`).

## Sim Labelling Standard

Every simulation-track chart title ends with the ` sim ` tag and a grey ribbon,
and the dashboard description states "Simulation-Track demonstrator (ADR-09)".
This is a hard standard, not a suggestion.

## Checklist (pre-publish)

- [ ] ≤6 KPI tiles in header row
- [ ] Global time filter present
- [ ] Cross-filtering configured
- [ ] CVD-safe colours + labels
- [ ] Drill-down documented
- [ ] Sim charts labelled
- [ ] Exported to `bi/superset/`
