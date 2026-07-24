#!/usr/bin/env python3
"""Independently validate saved PySR continuous-score run artifacts.

This command reads saved labels and scores and does not fit or reload a model.
Validation remains provisional, unverified, and pending thesis-author review.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "provisional, unverified, pending review"
REQUIRED_FILES = [
    "pysr_metrics.json",
    "pysr_equations.csv",
    "pysr_run_metadata.json",
    "pysr_environment.json",
    "pysr_git_state.json",
    "pysr_runtime_settings.json",
    "pysr_preprocessing.json",
    "pysr_test_scores.csv",
    "pysr_roc_curve_data.csv",
    "pysr_model.pkl",
    "pysr_stdout_stderr.log",
    "pysr_artifact_manifest.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate saved PySR scores and metrics.")
    parser.add_argument("--run-dir", required=True, help="PySR output run directory.")
    parser.add_argument(
        "--output",
        help="Optional new JSON integrity-record path. Omit to print JSON only.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def close_enough(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1.0e-12, abs_tol=1.0e-15)


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    try:
        import numpy as np
        import pandas as pd
        from sklearn.metrics import average_precision_score, roc_auc_score
    except ImportError as exc:
        raise SystemExit("numpy, pandas, and scikit-learn are required.") from exc

    metrics = load_json(run_dir / "pysr_metrics.json")
    metadata = load_json(run_dir / "pysr_run_metadata.json")
    environment = load_json(run_dir / "pysr_environment.json")
    runtime = load_json(run_dir / "pysr_runtime_settings.json")
    preprocessing = load_json(run_dir / "pysr_preprocessing.json")
    git_state = load_json(run_dir / "pysr_git_state.json")
    scores = pd.read_csv(run_dir / "pysr_test_scores.csv")

    required_score_columns = {
        "row_index",
        "split_membership",
        "mchi1",
        "mchipm1",
        "y_true",
        "score",
        "score_source",
        "positive_label",
    }
    missing_score_columns = sorted(required_score_columns - set(scores.columns))
    if missing_score_columns:
        raise SystemExit(f"Missing score columns: {missing_score_columns}")
    if "Final_CLs" in scores.columns:
        raise SystemExit("Final_CLs must not appear in score artifacts")
    if metadata.get("target") != "exclusion":
        raise SystemExit(f"Unexpected target: {metadata.get('target')}")
    if metadata.get("base_features") != ["mchi1", "mchipm1"]:
        raise SystemExit(f"Unexpected base features: {metadata.get('base_features')}")
    if metrics.get("score_source") != "PySRRegressor.predict_continuous_score":
        raise SystemExit(f"Unexpected score source: {metrics.get('score_source')}")
    if metrics.get("auc_rule") != "continuous_scores_only":
        raise SystemExit(f"Unexpected AUC rule: {metrics.get('auc_rule')}")
    forbidden_metric_keys = [
        key
        for key in metrics
        if "reference" in key.lower() or key.lower() == "auc_minus_reference"
    ]
    if forbidden_metric_keys:
        raise SystemExit(f"Obsolete reference-comparison metrics found: {forbidden_metric_keys}")
    if not environment.get("julia_backend_initialized"):
        raise SystemExit("Julia backend was not recorded as initialized")
    requested_threads = runtime.get("requested_environment", {}).get("julia_threads")
    observed_threads = environment.get("julia", {}).get("threads")
    if requested_threads is None or int(requested_threads) != int(observed_threads):
        raise SystemExit(
            f"Julia thread record mismatch: requested={requested_threads}, observed={observed_threads}"
        )
    if preprocessing.get("fit_scope") not in {"training_rows_only", "no_test_fit"}:
        raise SystemExit(f"Unexpected preprocessing fit scope: {preprocessing.get('fit_scope')}")
    if preprocessing.get("non_finite_policy") != "reject":
        raise SystemExit("Preprocessing must record non-finite rejection")
    if scores["row_index"].duplicated().any():
        raise SystemExit("Duplicate test row indices found")
    if sorted(scores["split_membership"].unique().tolist()) != ["test"]:
        raise SystemExit("Score artifact must contain only test rows")
    if sorted(scores["y_true"].unique().tolist()) != [0, 1]:
        raise SystemExit("Saved labels must contain binary values 0 and 1")
    if not np.isfinite(scores["score"].to_numpy(dtype=float)).all():
        raise SystemExit("Continuous scores contain non-finite values")
    if scores["score"].nunique() < 2:
        raise SystemExit("Continuous scores are constant")

    recomputed_auc = float(roc_auc_score(scores["y_true"], scores["score"]))
    recomputed_ap = float(average_precision_score(scores["y_true"], scores["score"]))
    recorded_auc = float(metrics["roc_auc"])
    recorded_ap = float(metrics["average_precision"])
    if not close_enough(recomputed_auc, recorded_auc):
        raise SystemExit(
            f"Recomputed ROC-AUC {recomputed_auc!r} does not match {recorded_auc!r}"
        )
    if not close_enough(recomputed_ap, recorded_ap):
        raise SystemExit(
            f"Recomputed average precision {recomputed_ap!r} does not match {recorded_ap!r}"
        )

    result = {
        "validation_status": "passed",
        "status": STATUS,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "run_id": metadata.get("run_id"),
        "test_rows": int(len(scores)),
        "recomputed_roc_auc": recomputed_auc,
        "recorded_roc_auc": recorded_auc,
        "recomputed_average_precision": recomputed_ap,
        "recorded_average_precision": recorded_ap,
        "score_source": metrics.get("score_source"),
        "julia_version": environment.get("julia", {}).get("version"),
        "symbolic_regression_version": environment.get("julia", {}).get(
            "symbolic_regression_version"
        ),
        "requested_julia_threads": requested_threads,
        "observed_julia_threads": observed_threads,
        "git_head": git_state.get("head"),
        "git_is_clean": git_state.get("is_clean"),
        "fit_performed_by_validator": False,
        "reference_model_comparison_performed": False,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output)
        if output_path.exists():
            raise SystemExit(f"Refusing to overwrite integrity record: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
