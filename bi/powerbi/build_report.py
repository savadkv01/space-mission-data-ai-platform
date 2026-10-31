"""Translate checked-in Superset assets into a local, snapshot-backed PBIP."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/"
REPORT = "SpaceMission.Report"
MODEL = "SpaceMission.SemanticModel"
NULL = r"\N"
AGGREGATES = {"SUM": "SUM", "AVG": "AVERAGE", "MAX": "MAX", "MIN": "MIN"}


def schema(path: str) -> str:
    return SCHEMA + path + "/schema.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def identifier(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:20]


def assets(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for kind in ("datasets", "charts", "dashboards"):
        result[kind] = {}
        for path in sorted((root / "bi" / "superset" / kind).rglob("*.yaml")):
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
            value["_file"] = str(path.relative_to(root))
            for key in ("params", "position", "metadata"):
                if isinstance(value.get(key), str):
                    value[key] = json.loads(value[key])
            result[kind][value["uuid"]] = value
    return result


def source_hashes(source: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {
        item["_file"]: hashlib.sha256((ROOT / item["_file"]).read_bytes()).hexdigest()
        for category in source.values() for item in category.values()
    }


def dax_column(table: str, column: str) -> str:
    return "'" + table.replace("'", "''") + "'[" + column.replace("]", "]]") + "]"


def metric_dax(table: str, expression: str) -> str:
    """Support the aggregate grammar actually present in certified YAML."""
    expression = expression.strip()
    if re.fullmatch(r"COUNT\s*\(\s*\*\s*\)", expression, re.I):
        return f"COALESCE(COUNTROWS('{table}'), 0)"
    simple = re.fullmatch(r"(SUM|AVG|MAX|MIN)\s*\(\s*(\w+)\s*\)", expression, re.I)
    if simple:
        return f"{AGGREGATES[simple[1].upper()]}({dax_column(table, simple[2])})"
    case = re.fullmatch(
        r"(SUM|AVG)\s*\(\s*CASE\s+WHEN\s+(\w+)(?:\s*(>=|>|=|<=|<)\s*"
        r"(-?\d+(?:\.\d+)?))?\s+THEN\s+(-?\d+(?:\.\d+)?)\s+ELSE\s+"
        r"(-?\d+(?:\.\d+)?)\s+END\s*\)",
        expression,
        re.I,
    )
    if case:
        function, column, comparison, threshold, yes, no = case.groups()
        condition = dax_column(table, column)
        if comparison:
            # SQL NULL comparisons choose ELSE; DAX otherwise coerces BLANK to zero.
            condition = f"NOT ISBLANK({condition}) && {condition} {comparison} {threshold}"
        else:
            condition += " = TRUE()"
        iterator = "SUMX" if function.upper() == "SUM" else "AVERAGEX"
        return f"{iterator}('{table}', IF({condition}, {yes}, {no}))"
    raise ValueError(f"Unsupported certified metric for {table}: {expression}")


def metric_definition(dataset: dict[str, Any], metric: Any) -> tuple[str, str, str]:
    if isinstance(metric, str):
        definitions = {item["metric_name"]: item for item in dataset.get("metrics", [])}
        if metric not in definitions:
            raise ValueError(f"Unknown metric {metric} in {dataset['table_name']}")
        item = definitions[metric]
        return metric, item.get("verbose_name", metric), item["expression"]
    if metric.get("expressionType") == "SQL":
        expression = metric["sqlExpression"]
    elif metric.get("expressionType") == "SIMPLE":
        expression = f"{metric['aggregate']}({metric['column']['column_name']})"
    else:
        raise ValueError(f"Unsupported ad-hoc metric: {metric}")
    label = metric.get("label") or metric.get("metric_name") or expression
    return metric.get("metric_name") or label, label, expression


def metric_list(params: dict[str, Any]) -> list[Any]:
    return params.get("metrics") or ([params["metric"]] if "metric" in params else [])


def model_types(sql_type: str) -> tuple[str, str]:
    if sql_type in ("DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE"):
        return "dateTime", "type datetime"
    if sql_type == "BOOLEAN":
        return "boolean", "type logical"
    if sql_type in ("BIGINT", "INTEGER", "HUGEINT", "SMALLINT", "TINYINT", "UBIGINT"):
        return "int64", "Int64.Type"
    if sql_type in ("DOUBLE", "FLOAT") or sql_type.startswith("DECIMAL"):
        return "double", "type number"
    if sql_type == "VARCHAR":
        return "string", "type text"
    raise ValueError(f"Unsupported snapshot type: {sql_type}")


def write_csv(path: Path, columns: list[str], rows: list[tuple[Any, ...]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for row in rows:
            values = []
            for value in row:
                if value == NULL:
                    raise ValueError(f"Reserved CSV null marker found in {path.name}")
                if isinstance(value, int) and not isinstance(value, bool):
                    if not -(2**63) <= value < 2**63:
                        raise OverflowError(f"Power BI Int64 overflow in {path.name}")
                if isinstance(value, (date, datetime)):
                    value = value.isoformat()
                values.append(NULL if value is None else value)
            writer.writerow(values)


def configure_minio(connection: duckdb.DuckDBPyConnection, env_file: Path, endpoint: str) -> None:
    values = dict(os.environ)
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    for key in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"):
        if not values.get(key):
            raise ValueError(f"{key} must be provided in the environment or local env file")
    connection.execute("INSTALL httpfs")
    connection.execute("LOAD httpfs")
    for name, value in {
        "s3_endpoint": endpoint,
        "s3_use_ssl": False,
        "s3_url_style": "path",
        "s3_access_key_id": values["MINIO_ROOT_USER"],
        "s3_secret_access_key": values["MINIO_ROOT_PASSWORD"],
    }.items():
        connection.execute(f"SET {name} = ?", [value])


def extract(
    source: dict[str, dict[str, Any]], database: Path, output: Path, env_file: Path, endpoint: str
) -> tuple[dict[str, list[tuple[str, str]]], list[dict[str, Any]]]:
    if not database.is_file():
        raise FileNotFoundError(f"Build the serving DuckDB before exporting: {database}")
    columns: dict[str, list[tuple[str, str]]] = {}
    status = []
    dates: set[date] = set()
    with duckdb.connect(":memory:") as connection:
        # An alias avoids the existing file basename's serving catalog/schema collision.
        escaped = str(database).replace("'", "''")
        connection.execute(f"ATTACH '{escaped}' AS serving_products (READ_ONLY)")
        connection.execute("USE serving_products")
        if any("s3://" in dataset["sql"] for dataset in source["datasets"].values()):
            configure_minio(connection, env_file, endpoint)
        for dataset in source["datasets"].values():
            name = dataset["table_name"]
            cursor = connection.execute(dataset["sql"])
            description = [(item[0], str(item[1])) for item in cursor.description]
            rows = cursor.fetchall()
            columns[name] = description
            for _, sql_type in description:
                model_types(sql_type)
            write_csv(output / f"{name}.csv", [item[0] for item in description], rows)
            date_column = dataset.get("main_dttm_col")
            present_dates = []
            if date_column:
                index = [item[0] for item in description].index(date_column)
                present_dates = [row[index] for row in rows if row[index] is not None]
                dates.update(value.date() if isinstance(value, datetime) else value for value in present_dates)
            status.append({
                "dataset": name,
                "rows": len(rows),
                "state": "EMPTY SOURCE" if not rows else "AVAILABLE",
                "min_date": str(min(present_dates)) if present_dates else None,
                "max_date": str(max(present_dates)) if present_dates else None,
                "source": dataset["_file"],
                "sql_sha256": hashlib.sha256(dataset["sql"].encode()).hexdigest(),
            })
            print(f"{name}: {len(rows)} rows" + (" (EMPTY SOURCE)" if not rows else ""))
    dates.add(datetime.now(timezone.utc).date())
    first, last = min(dates), max(dates)
    day_rows = []
    current = first
    while current <= last:
        day_rows.append((current, current.strftime("%Y-%m"), current.day))
        current += timedelta(days=1)
    columns["ReportDate"] = [("Date", "DATE"), ("Month", "VARCHAR"), ("Day", "INTEGER")]
    write_csv(output / "ReportDate.csv", ["Date", "Month", "Day"], day_rows)
    columns["DataStatus"] = [
        ("Dataset", "VARCHAR"), ("Rows", "BIGINT"), ("State", "VARCHAR"),
        ("MinDate", "VARCHAR"), ("MaxDate", "VARCHAR"), ("ExportedUTC", "VARCHAR"),
    ]
    exported = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_csv(output / "DataStatus.csv", [item[0] for item in columns["DataStatus"]], [
        (item["dataset"], item["rows"], item["state"], item["min_date"], item["max_date"], exported)
        for item in status
    ])
    write_json(output / "manifest.json", {"exported_utc": exported, "datasets": status})
    return columns, status


def m_source(name: str, columns: list[tuple[str, str]]) -> str:
    types = ", ".join("{" + json.dumps(column) + ", " + model_types(sql_type)[1] + "}"
                      for column, sql_type in columns)
    return "\n".join([
        "let",
        f'    Raw = Csv.Document(File.Contents(SnapshotFolder & "\\{name}.csv"), '
        f'[Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        '    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),',
        f'    Nulls = Table.ReplaceValue(Headers, "{NULL}", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
        f'    Typed = Table.TransformColumnTypes(Nulls, {{{types}}}, "en-US")',
        "in",
        "    Typed",
    ])


def make_model(
    source: dict[str, dict[str, Any]], columns: dict[str, list[tuple[str, str]]], folder: Path
) -> tuple[dict[str, Any], dict[tuple[str, str], str]]:
    tables = []
    measure_names: dict[tuple[str, str], str] = {}
    dataset_by_name = {dataset["table_name"]: dataset for dataset in source["datasets"].values()}
    relationships = []
    for name, description in columns.items():
        table: dict[str, Any] = {
            "name": name,
            "columns": [
                {
                    "name": column, "dataType": model_types(sql_type)[0],
                    "sourceColumn": column, "summarizeBy": "none",
                    **({"formatString": "yyyy-MM-dd"} if sql_type == "DATE" else {}),
                }
                for column, sql_type in description
            ],
            "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": m_source(name, description)}}],
        }
        dataset = dataset_by_name.get(name)
        if dataset:
            metrics: dict[str, tuple[str, str]] = {
                metric["metric_name"]: (metric.get("verbose_name", metric["metric_name"]), metric["expression"])
                for metric in dataset.get("metrics", [])
            }
            for chart in source["charts"].values():
                if chart["dataset_uuid"] == dataset["uuid"]:
                    for metric in metric_list(chart["params"]):
                        key, label, sql = metric_definition(dataset, metric)
                        if key in metrics and metrics[key][1] != sql:
                            raise ValueError(f"Conflicting metric definitions in {name}: {key}")
                        metrics[key] = (label, sql)
            measures = []
            for key, (label, sql) in metrics.items():
                measure_name = "KPI " + name + " - " + key
                measure_names[(dataset["uuid"], key)] = measure_name
                measures.append({
                    "name": measure_name, "expression": metric_dax(name, sql),
                    "description": f"{label}. Superset SQL: {sql}",
                    "formatString": "0.0%" if "rate" in key else ("#,0" if sql.upper().startswith(("SUM", "COUNT")) else "#,0.00"),
                    "annotations": [{"name": "SupersetMetricSQL", "value": sql}],
                })
            table["measures"] = measures
            if dataset.get("main_dttm_col"):
                relationships.append({
                    "name": identifier(name + "_date"), "fromTable": name,
                    "fromColumn": dataset["main_dttm_col"], "toTable": "ReportDate", "toColumn": "Date",
                    "fromCardinality": "many", "toCardinality": "one",
                    "crossFilteringBehavior": "oneDirection",
                })
        tables.append(table)
    model = {
        "name": "SpaceMission", "compatibilityLevel": 1600,
        "model": {
            "culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": False},
            "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(list(columns))}],
            "expressions": [{
                "name": "SnapshotFolder", "kind": "m",
                "expression": '"' + str(folder.resolve()).replace('"', '""') +
                '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
            }],
            "tables": tables, "relationships": relationships,
        },
    }
    return model, measure_names


def field(table: str, property_name: str, measure: bool = False) -> dict[str, Any]:
    return {
        "Measure" if measure else "Column": {
            "Expression": {"SourceRef": {"Entity": table}}, "Property": property_name,
        }
    }


def projection(table: str, property_name: str, measure: bool = False, label: str | None = None) -> dict[str, Any]:
    return {
        "field": field(table, property_name, measure), "queryRef": f"{table}.{property_name}",
        "nativeQueryRef": property_name, **({"displayName": label} if label else {}),
    }


def literal(value: str) -> dict[str, Any]:
    return {"expr": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}


def visual(
    name: str, kind: str, title: str, roles: dict[str, list[dict[str, Any]]],
    x: float, y: float, width: float, height: float, z: int,
) -> dict[str, Any]:
    return {
        "$schema": schema("item/report/definition/visualContainer/2.1.0"),
        "name": name, "position": {"x": x, "y": y, "width": width, "height": height, "z": z, "tabOrder": z},
        "visual": {
            "visualType": kind,
            "query": {"queryState": {key: {"projections": values} for key, values in roles.items()}},
            "visualContainerObjects": {
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": literal(title)}}],
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": literal("#FFFFFF")}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                }}],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def boolean_filter(table: str, column: str) -> dict[str, Any]:
    return {
        "name": identifier(table + column), "field": field(table, column), "type": "Advanced",
        "filter": {
            "Version": 2, "From": [{"Name": "s", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"Comparison": {
                "ComparisonKind": 0,
                "Left": {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": column}},
                "Right": {"Literal": {"Value": "true"}},
            }}}],
        },
        "howCreated": "User",
    }


def window_filter(days: int, now: datetime) -> dict[str, Any]:
    end = now.date() + timedelta(days=1)
    start = end - timedelta(days=days)
    left = {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "Date"}}
    return {
        "name": identifier(f"window_{days}"), "field": field("ReportDate", "Date"), "type": "Advanced",
        "filter": {
            "Version": 2, "From": [{"Name": "d", "Entity": "ReportDate", "Type": 0}],
            "Where": [{"Condition": {"And": {
                "Left": {"Comparison": {
                    "ComparisonKind": 2, "Left": left,
                    "Right": {"Literal": {"Value": f"datetime'{start.isoformat()}T00:00:00'"}},
                }},
                "Right": {"Comparison": {
                    "ComparisonKind": 3, "Left": left,
                    "Right": {"Literal": {"Value": f"datetime'{end.isoformat()}T00:00:00'"}},
                }},
            }}}],
        },
        "howCreated": "User",
    }


def chart_visual(
    chart: dict[str, Any], dataset: dict[str, Any], measure_names: dict[tuple[str, str], str],
    name: str, x: float, y: float, width: float, height: float, z: int,
) -> tuple[dict[str, Any], str | None]:
    params = chart["params"]
    table = dataset["table_name"]
    metrics = []
    for item in metric_list(params):
        key, label, _ = metric_definition(dataset, item)
        metrics.append(projection(table, measure_names[(dataset["uuid"], key)], True, label))
    categories = [projection(table, column) for column in params.get("groupby", [])]
    source_kind = params["viz_type"]
    deviation = None
    if source_kind == "big_number_total":
        kind, roles = "card", {"Values": metrics}
    elif source_kind == "pie":
        kind, roles = "pieChart", {"Category": categories, "Y": metrics}
    elif source_kind in ("echarts_timeseries_line", "echarts_timeseries_bar"):
        kind = "lineChart" if source_kind.endswith("line") else "clusteredColumnChart"
        grain = params.get("time_grain_sqla", "P1D")
        if grain not in ("P1D", "P1M"):
            raise ValueError(f"Unsupported time grain: {grain}")
        axis = projection("ReportDate", "Month") if grain == "P1M" else projection(table, params["x_axis"])
        roles = {"Category": [axis], "Y": metrics}
        if categories:
            roles["Series"] = categories
    elif source_kind == "table":
        kind = "tableEx"
        roles = {"Values": [projection(table, column) for column in params.get("all_columns", [])] + categories + metrics}
    elif source_kind == "cal_heatmap":
        kind = "pivotTable"
        roles = {
            "Rows": [projection("ReportDate", "Month")],
            "Columns": [projection("ReportDate", "Day")], "Values": metrics,
        }
        deviation = "Calendar heatmap translated to a month/day matrix; no custom visual or heatmap colouring."
    else:
        raise ValueError(f"Unsupported Superset visual: {source_kind}")
    result = visual(name, kind, chart["slice_name"], roles, x, y, width, height, z)
    filters = []
    for item in params.get("adhoc_filters", []):
        match = re.fullmatch(r"(\w+)\s*=\s*true", item.get("sqlExpression", ""), re.I)
        if item.get("clause") != "WHERE" or item.get("expressionType") != "SQL" or not match:
            raise ValueError(f"Unsupported chart filter: {item}")
        filters.append(boolean_filter(table, match[1]))
    if filters:
        for config in filters:
            config["name"] = identifier(name + config["name"])
        result["filterConfig"] = {"filters": filters}
    if "Category" in roles:
        result["visual"]["query"]["sortDefinition"] = {
            "sort": [{"field": roles["Category"][0]["field"], "direction": "Ascending"}],
        }
    return result, deviation


def page_rows(position: dict[str, Any], node_id: str) -> list[list[dict[str, Any]]]:
    node = position[node_id]
    if node["type"] == "ROW":
        charts = [position[child] for child in node.get("children", [])]
        if any(child["type"] != "CHART" for child in charts):
            raise ValueError(f"Unsupported non-chart row: {node_id}")
        return [charts]
    result = []
    for child in node.get("children", []):
        result.extend(page_rows(position, child))
    return result


def make_report(
    source: dict[str, dict[str, Any]], measures: dict[tuple[str, str], str], destination: Path
) -> list[dict[str, Any]]:
    definition = destination / REPORT / "definition"
    write_json(destination / "SpaceMission.pbip", {
        "$schema": schema("pbip/pbipProperties/1.0.0"), "version": "1.0",
        "artifacts": [{"report": {"path": REPORT}}], "settings": {"enableAutoRecovery": True},
    })
    write_json(destination / REPORT / "definition.pbir", {
        "$schema": schema("item/report/definitionProperties/2.0.0"), "version": "4.0",
        "datasetReference": {"byPath": {"path": "../" + MODEL}},
    })
    write_json(definition / "version.json", {
        "$schema": schema("item/report/definition/versionMetadata/1.0.0"), "version": "2.0.0",
    })
    write_json(definition / "report.json", {
        "$schema": schema("item/report/definition/report/2.0.0"), "themeCollection": {},
        "settings": {"useStylableVisualContainerHeader": True},
    })
    order = []
    coverage = []
    now = datetime.now(timezone.utc)
    dashboards = sorted(source["dashboards"].values(), key=lambda item: (
        item["slug"] != "executive", item["slug"] != "earth-observation", item["slug"]
    ))
    for dashboard in dashboards:
        position = dashboard["position"]
        tabs = [(key, node["meta"]["text"]) for key, node in position.items()
                if isinstance(node, dict) and node["type"] == "TAB"]
        if not tabs:
            tabs = [("GRID_ID", "Overview")]
        metadata = dashboard.get("metadata", {})
        filters = metadata.get("native_filter_configuration", [])
        for tab_id, tab_label in tabs:
            page_name = identifier(dashboard["uuid"] + tab_id)
            order.append(page_name)
            label = dashboard["dashboard_title"].split(" \u2014 ")[0] + " - " + tab_label
            rows = page_rows(position, tab_id)
            folder = definition / "pages" / page_name
            y = 104.0
            page: dict[str, Any] = {
                "$schema": schema("item/report/definition/page/2.0.0"),
                "name": page_name, "displayName": label, "displayOption": "FitToWidth", "width": 1280, "height": 720,
            }
            page_filters = []
            for config in filters:
                if config["filterType"] == "filter_time":
                    value = config.get("defaultDataMask", {}).get("filterState", {}).get("value", "No filter")
                    match = re.fullmatch(r"Last (\d+) days", value)
                    if match:
                        config_filter = window_filter(int(match[1]), now)
                        config_filter["name"] = identifier(page_name + config_filter["name"])
                        page_filters.append(config_filter)
                    elif value != "No filter":
                        raise ValueError(f"Unsupported dashboard time default: {value}")
                elif config["filterType"] == "filter_select":
                    for target in config["targets"]:
                        dataset = source["datasets"][target["datasetUuid"]]
                        slicer_name = identifier(page_name + config["id"] + dataset["uuid"])
                        write_json(folder / "visuals" / slicer_name / "visual.json", visual(
                            slicer_name, "slicer", config["name"],
                            {"Values": [projection(dataset["table_name"], target["column"]["name"])]},
                            650, 12, 606, 76, 1,
                        ))
                else:
                    raise ValueError(f"Unsupported native filter: {config['filterType']}")
            if page_filters:
                page["filterConfig"] = {"filters": page_filters}
            date_slicer = identifier(page_name + "_date_slicer")
            write_json(folder / "visuals" / date_slicer / "visual.json", visual(
                date_slicer, "slicer", "Date (UTC export window; edit page filter to widen)",
                {"Values": [projection("ReportDate", "Date")]}, 24, 12, 602, 76, 0,
            ))
            z = 2
            for row in rows:
                total_width = sum(node["meta"].get("width", 12 / len(row)) for node in row)
                row_height = 170 if all(source["charts"][node["meta"]["uuid"]]["params"]["viz_type"] == "big_number_total" for node in row) else 310
                x = 24.0
                for node in row:
                    chart = source["charts"][node["meta"]["uuid"]]
                    dataset = source["datasets"][chart["dataset_uuid"]]
                    width = 1232 * node["meta"].get("width", 12 / len(row)) / total_width - 12
                    name = identifier(page_name + node["id"])
                    result, deviation = chart_visual(chart, dataset, measures, name, x, y, width, row_height, z)
                    write_json(folder / "visuals" / name / "visual.json", result)
                    coverage.append({
                        "dashboard": dashboard["slug"], "page": label, "chart": chart["slice_name"],
                        "chart_uuid": chart["uuid"], "dataset": dataset["table_name"],
                        "source": chart["_file"], "powerbi_visual": result["visual"]["visualType"],
                        "deviation": deviation,
                    })
                    x += width + 12
                    z += 1
                y += row_height + 16
            page["height"] = max(720, y + 12)
            write_json(folder / "page.json", page)
    status_page = "DataStatus"
    order.append(status_page)
    folder = definition / "pages" / status_page
    write_json(folder / "page.json", {
        "$schema": schema("item/report/definition/page/2.0.0"), "name": status_page,
        "displayName": "Data status - local snapshot", "displayOption": "FitToPage", "width": 1280, "height": 720,
    })
    write_json(folder / "visuals" / "SnapshotStatus" / "visual.json", visual(
        "SnapshotStatus", "tableEx", "Snapshot availability (EMPTY SOURCE is not a zero KPI)",
        {"Values": [projection("DataStatus", name) for name in ("Dataset", "Rows", "State", "MinDate", "MaxDate", "ExportedUTC")]},
        24, 24, 1232, 650, 0,
    ))
    write_json(definition / "pages" / "pages.json", {
        "$schema": schema("item/report/definition/pagesMetadata/1.0.0"),
        "pageOrder": order, "activePageName": order[0],
    })
    write_json(destination / "coverage.json", coverage)
    return coverage


def build(database: Path, output: Path, env_file: Path, endpoint: str, refresh_only: bool = False) -> None:
    source = assets()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="powerbi-export-", dir=output) as temporary:
        staging = Path(temporary)
        columns, status = extract(source, database, staging / "data", env_file, endpoint)
        if refresh_only:
            original_sources = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
            if original_sources != source_hashes(source):
                raise ValueError("Superset definitions changed. Close Desktop and rebuild the PBIP.")
            existing = json.loads((output / MODEL / "model.bim").read_text(encoding="utf-8"))
            expected = {table["name"]: [(column["name"], column["dataType"]) for column in table["columns"]]
                        for table in existing["model"]["tables"]}
            actual = {name: [(column, model_types(sql_type)[0]) for column, sql_type in description]
                      for name, description in columns.items()}
            if actual != expected:
                raise ValueError("Snapshot schema changed. Close Desktop and rebuild the PBIP.")
        else:
            model, measures = make_model(source, columns, output / "data")
            write_json(staging / MODEL / "definition.pbism", {
                "$schema": schema("item/semanticModel/definitionProperties/1.0.0"), "version": "4.0",
            })
            write_json(staging / MODEL / "model.bim", model)
            write_json(staging / "source-manifest.json", source_hashes(source))
            coverage = make_report(source, measures, staging)
            if {item["chart_uuid"] for item in coverage} != set(source["charts"]):
                raise ValueError("Some source charts are not represented in the report")
        # Publish only after every dataset/query and every translation succeeds.
        for path in staging.rglob("*"):
            if path.is_file():
                target = output / path.relative_to(staging)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, target)
    empty = [item["dataset"] for item in status if item["state"] == "EMPTY SOURCE"]
    if empty:
        print("WARNING: empty source datasets: " + ", ".join(empty), file=sys.stderr)
    print(f"Snapshots refreshed: {output / 'data'}" if refresh_only else f"Open in Desktop: {output / 'SpaceMission.pbip'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "serving" / "dbt" / "serving.duckdb")
    parser.add_argument("--output", type=Path, default=HERE)
    parser.add_argument("--env-file", type=Path, default=ROOT / "infrastructure" / "env" / ".env")
    parser.add_argument("--minio-endpoint", default="localhost:9000")
    parser.add_argument("--refresh-only", action="store_true", help="Update CSV snapshots without overwriting Desktop edits")
    args = parser.parse_args()
    build(args.database.resolve(), args.output.resolve(), args.env_file.resolve(), args.minio_endpoint, args.refresh_only)


if __name__ == "__main__":
    main()
