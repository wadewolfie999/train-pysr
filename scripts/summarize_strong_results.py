#!/usr/bin/env python3
"""Create a concise review summary for the strong-baseline run."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


STATUS = "provisional, unverified, pending review"
RUN_DIR = Path("outputs/runs/masses_exclusions_strong_baselines_v1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a concise review summary for the strong-baseline run."
    )
    return parser.parse_args()


def read_metrics() -> list[dict[str, str]]:
    path = RUN_DIR / "strong_metrics.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def best(rows: list[dict[str, str]], predicate) -> dict[str, str] | None:
    subset = [row for row in rows if row["status"] == "completed" and predicate(row)]
    if not subset:
        return None
    return max(subset, key=lambda row: float(row["roc_auc"]))


def line_for(label: str, row: dict[str, str] | None) -> str:
    if row is None:
        return f"- {label}: not available."
    return (
        f"- {label}: `{row['feature_set']}` / `{row['model_variant']}` "
        f"ROC-AUC = {float(row['roc_auc']):.6f}, "
        f"average precision = {float(row['average_precision']):.6f}."
    )


def main() -> int:
    parse_args()
    rows = read_metrics()
    raw_best = best(rows, lambda row: row["feature_set"] == "raw_masses")
    engineered_best = best(rows, lambda row: row["feature_set"] == "mass_engineered_v1")
    diagnostic_best = best(rows, lambda row: row["diagnostic"] == "True")
    any_gt = any(
        row["status"] == "completed" and float(row["roc_auc"]) > 0.97 for row in rows
    )

    lines = [
        "# Strong Baseline Review Summary",
        "",
        f"Status: {STATUS}.",
        "",
        "This summary is a review aid only. It does not establish an accepted thesis result.",
        "",
        "## Observed Results",
        "",
        line_for("Best approved raw-mass result", raw_best),
        line_for("Best approved engineered-feature result", engineered_best),
        line_for("Best diagnostic Final_CLs result", diagnostic_best),
        "",
        "## AUC Target",
        "",
        (
            "- AUC > 0.97 was observed in the strong-baseline run; pending review."
            if any_gt
            else "- AUC > 0.97 was not observed in the strong-baseline run."
        ),
        "",
        "## Diagnostic Final_CLs",
        "",
        "- Final_CLs diagnostics are not accepted feature evidence because Final_CLs is audit-only and may encode label construction or leakage.",
        "- Final_CLs must not be promoted to an approved feature without explicit review.",
        "",
        "## Recommended Next Step",
        "",
        "- Run robustness validation on approved feature sets only before deciding whether to launch PySR search.",
        "",
        "All recommendations are provisional, unverified, pending review.",
        "",
    ]
    output = RUN_DIR / "review_summary.md"
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing summary: {output}")
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
