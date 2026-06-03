#!/usr/bin/env python3
"""Lightweight reproducible dataset audit.

This script reads a run config and raw CSV, then writes audit summaries without
modifying raw data or inferring physics rules.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit(
        "PyYAML is required to read run configs. Install pyyaml before running."
    ) from exc


STATUS = "provisional, unverified, pending review"
MISSING_MARKERS = {"", "NA", "NaN", "nan", "null", "None"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a registered CSV dataset.")
    parser.add_argument("--config", required=True, help="Path to run YAML config.")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return data


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = list(reader.fieldnames or [])
    return columns, rows


def is_missing(value: Any) -> bool:
    return value is None or str(value).strip() in MISSING_MARKERS


def infer_dtype(values: list[str]) -> str:
    nonmissing = [value for value in values if not is_missing(value)]
    if not nonmissing:
        return "empty"
    try:
        for value in nonmissing:
            int(value)
        return "int64"
    except ValueError:
        pass
    try:
        for value in nonmissing:
            float(value)
        return "float64"
    except ValueError:
        return "string"


def numeric_values(rows: list[dict[str, str]], column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(column)
        if is_missing(value):
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            return []
    return values


def numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "std": None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    var_x = sum((value - mean_x) ** 2 for value in xs)
    var_y = sum((value - mean_y) ** 2 for value in ys)
    if var_x == 0 or var_y == 0:
        return None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return cov / math.sqrt(var_x * var_y)


def build_audit(config_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    raw_path = Path(config["raw_data_path"])
    columns, rows = load_csv(raw_path)
    target = config.get("target_column")
    feature_columns = list(config.get("feature_columns", []))
    audit_only_columns = list(config.get("audit_only_columns", []))

    dtypes = {
        column: infer_dtype([row.get(column, "") for row in rows]) for column in columns
    }
    missing_values = {
        column: sum(is_missing(row.get(column)) for row in rows) for column in columns
    }
    row_tuples = [tuple(row.get(column, "") for column in columns) for row in rows]

    target_values = [row.get(target, "") for row in rows] if target in columns else []
    target_counts = Counter(target_values)

    summaries = {}
    for column in columns:
        values = numeric_values(rows, column)
        if values and len(values) == sum(
            not is_missing(row.get(column)) for row in rows
        ):
            summaries[column] = numeric_summary(values)

    negative_mass_counts = {}
    for column in feature_columns:
        values = numeric_values(rows, column)
        if values:
            negative_mass_counts[column] = sum(value < 0 for value in values)

    mass_order_check = None
    if {"mchi1", "mchipm1"}.issubset(columns):
        mchi1 = numeric_values(rows, "mchi1")
        mchipm1 = numeric_values(rows, "mchipm1")
        mass_order_check = {
            "checked": True,
            "mchipm1_greater_than_or_equal_mchi1_always": all(
                right >= left for left, right in zip(mchi1, mchipm1)
            ),
            "violations": sum(right < left for left, right in zip(mchi1, mchipm1)),
        }

    correlation = None
    if "Final_CLs" in columns and target in columns:
        final_cls = numeric_values(rows, "Final_CLs")
        target_numeric = numeric_values(rows, target)
        correlation = {
            "columns": ["Final_CLs", target],
            "pearson": pearson_correlation(final_cls, target_numeric),
            "interpretation": (
                "Numerical association only; no physics meaning or exclusion rule "
                "is inferred."
            ),
        }

    command = " ".join(sys.argv)
    return {
        "status": STATUS,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "config_path": str(config_path),
        "dataset_path": str(raw_path),
        "run_id": config.get("run_id"),
        "dataset_id": config.get("dataset_id"),
        "task_type": config.get("task_type"),
        "review_status": config.get("review_status", "draft"),
        "shape": {"rows": len(rows), "columns": len(columns)},
        "columns": columns,
        "dtypes": dtypes,
        "missing_values": missing_values,
        "duplicate_rows": len(row_tuples) - len(set(row_tuples)),
        "target": {
            "column": target,
            "unique_values": sorted(set(target_values)),
            "class_counts": dict(sorted(target_counts.items())),
        },
        "numeric_summary": summaries,
        "negative_mass_counts": negative_mass_counts,
        "mass_order_check": mass_order_check,
        "audit_only_columns": audit_only_columns,
        "Final_CLs_target_correlation": correlation,
        "notes": [
            "Raw data was read only and not modified.",
            "Final_CLs is treated as audit-only.",
            "No exclusion rule is inferred.",
            "No empirical model performance is claimed.",
        ],
    }


def write_json(path: Path, audit: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Dataset Audit",
        "",
        f"Status: {audit['status']}.",
        "",
        "## Provenance",
        "",
        f"- Timestamp UTC: `{audit['timestamp_utc']}`",
        f"- Command: `{audit['command']}`",
        f"- Config path: `{audit['config_path']}`",
        f"- Dataset path: `{audit['dataset_path']}`",
        f"- Run id: `{audit['run_id']}`",
        f"- Dataset id: `{audit['dataset_id']}`",
        "",
        "## Summary",
        "",
        f"- Shape: {audit['shape']['rows']} rows, {audit['shape']['columns']} columns",
        f"- Columns: {', '.join(f'`{column}`' for column in audit['columns'])}",
        f"- Duplicate rows: {audit['duplicate_rows']}",
        "",
        "## Dtypes",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in audit["dtypes"].items())
    lines.extend(["", "## Missing Values", ""])
    lines.extend(
        f"- `{key}`: {value}" for key, value in audit["missing_values"].items()
    )
    target = audit["target"]
    lines.extend(
        [
            "",
            "## Target",
            "",
            f"- Target column: `{target['column']}`",
            f"- Unique values: {target['unique_values']}",
            f"- Class counts: {target['class_counts']}",
            "",
            "## Numeric Summary",
            "",
        ]
    )
    for column, summary in audit["numeric_summary"].items():
        lines.append(f"- `{column}`: {summary}")
    lines.extend(["", "## Mass Checks", ""])
    lines.append(f"- Negative mass counts: {audit['negative_mass_counts']}")
    lines.append(f"- Mass ordering check: {audit['mass_order_check']}")
    lines.extend(["", "## Audit-Only Columns", ""])
    lines.append(f"- Audit-only columns: {audit['audit_only_columns']}")
    lines.append(
        f"- Final_CLs/target correlation: {audit['Final_CLs_target_correlation']}"
    )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in audit["notes"])
    lines.append("")

    with path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    output_dir = Path(config["output_directory"])
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "dataset_audit.json"
    md_path = output_dir / "dataset_audit.md"
    existing = [path for path in (json_path, md_path) if path.exists()]
    if existing:
        existing_list = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing audit outputs: {existing_list}")

    audit = build_audit(config_path, config)
    write_json(json_path, audit)
    write_markdown(md_path, audit)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
