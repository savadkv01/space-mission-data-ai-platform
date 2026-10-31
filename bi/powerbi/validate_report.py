"""Validate PBIP references and Microsoft's public PBIR JSON schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from build_report import HERE, MODEL, REPORT, assets


def validate(folder: Path, online: bool = True) -> dict[str, int]:
    source = assets()
    coverage = json.loads((folder / "coverage.json").read_text(encoding="utf-8"))
    if {item["chart_uuid"] for item in coverage} != set(source["charts"]):
        raise ValueError("Missing chart coverage")
    if {item["dashboard"] for item in coverage} != {item["slug"] for item in source["dashboards"].values()}:
        raise ValueError("Missing dashboard coverage")
    model = json.loads((folder / MODEL / "model.bim").read_text(encoding="utf-8"))
    tables = {table["name"]: table for table in model["model"]["tables"]}
    fields = {name: {column["name"] for column in table["columns"]} for name, table in tables.items()}
    measures = {name: {measure["name"] for measure in table.get("measures", [])} for name, table in tables.items()}
    measure_names = [measure["name"] for table in tables.values() for measure in table.get("measures", [])]
    if len(measure_names) != len(set(measure_names)):
        raise ValueError("Measure names must be globally unique")
    for relationship in model["model"]["relationships"]:
        if relationship["fromColumn"] not in fields[relationship["fromTable"]]:
            raise ValueError(f"Invalid relationship source: {relationship['name']}")
        if relationship["toColumn"] not in fields[relationship["toTable"]]:
            raise ValueError(f"Invalid relationship target: {relationship['name']}")
    reference = json.loads((folder / REPORT / "definition.pbir").read_text(encoding="utf-8"))
    if (folder / REPORT / reference["datasetReference"]["byPath"]["path"]).resolve() != (folder / MODEL).resolve():
        raise ValueError("Report references the wrong semantic model")
    pages = folder / REPORT / "definition" / "pages"
    metadata = json.loads((pages / "pages.json").read_text(encoding="utf-8"))
    if not all((pages / page / "page.json").is_file() for page in metadata["pageOrder"]):
        raise ValueError("Page order references a missing page")
    for path in pages.rglob("visual.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        for role in document["visual"]["query"]["queryState"].values():
            for projection in role["projections"]:
                kind = "Measure" if "Measure" in projection["field"] else "Column"
                expression = projection["field"][kind]
                table = expression["Expression"]["SourceRef"]["Entity"]
                if expression["Property"] not in (measures if kind == "Measure" else fields)[table]:
                    raise ValueError(f"Unresolved visual field: {path}: {expression['Property']}")
    checked = 0
    if online:
        cache: dict[str, Any] = {}

        def retrieve(uri: str) -> Resource[Any]:
            parsed = urlparse(uri)
            prefix = "/json-schemas/fabric/"
            if parsed.scheme != "https" or parsed.netloc != "developer.microsoft.com" or not parsed.path.startswith(prefix):
                raise ValueError(f"Unexpected schema host: {uri}")
            if uri not in cache:
                relative = parsed.path[len("/json-schemas/"):]
                url = "https://raw.githubusercontent.com/microsoft/json-schemas/main/" + relative
                with urlopen(url, timeout=30) as response:
                    cache[uri] = json.load(response)
            return Resource.from_contents(cache[uri], default_specification=DRAFT7)

        registry: Registry[Any] = Registry(retrieve=retrieve)
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix in (".json", ".pbip", ".pbir", ".pbism") and "data" not in path.parts:
                document = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(document, dict) and "$schema" in document:
                    resource = retrieve(document["$schema"])
                    validator = Draft7Validator(resource.contents, registry=registry)
                    errors = list(validator.iter_errors(document))
                    if errors:
                        raise ValueError(f"{path}: " + "\n".join(error.message for error in errors))
                    checked += 1
    result = {
        "dashboards": len(source["dashboards"]), "unique_charts": len(source["charts"]),
        "chart_placements": len(coverage), "pages": len(metadata["pageOrder"]),
        "datasets": len(source["datasets"]), "schema_validated_files": checked,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=HERE)
    parser.add_argument("--offline", action="store_true", help="Check references only, without fetching public schemas")
    arguments = parser.parse_args()
    validate(arguments.folder, not arguments.offline)
