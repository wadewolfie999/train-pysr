#!/usr/bin/env python3
"""Validate PySR binary continuous-score run artifacts.

Validation outputs are review aids only. Scientific acceptance remains
provisional, unverified, and pending thesis-author review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_FEATURES = ["mchi1", "mchipm1"]
REQUIRED_FILES = [
    "pysr_metrics.json",
    "pysr_equations.csv",
    "pysr_run_metadata.json",
    "pysr_environment.json",
    "pysr_git_state.json",
    "pysr_runtime_settings.json",
    "pysr_test_scores.csv",
    "pysr_roc_curve_data.csv",
    "pysr_model.pkl",
    "pysr_stdout_stderr.log",
    "pysr_artifact_manifest.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate PySR run artifacts.")
    parser.add_argument("--run-dir", required=True, help="PySR output run directory.")
    parser.add_argument(
        "--reference-auc",
        type=float,
        required=True,
        help="Reference fixed-split HistGradientBoosting ROC-AUC.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Validate as a smoke run; performance is not interpreted scientifically.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")

    missing = [name for name in REQUIRED_FILES if not (run_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    try:
        import pandas as pd
        from sklearn.metrics import average_precision_score, roc_auc_score
    except ImportError as exc:
        raise SystemExit("pandas and scikit-learn are required for validation.") from exc

    metrics = load_json(run_dir / "pysr_metrics.json")
    metadata = load_json(run_dir / "pysr_run_metadata.json")
    environment = load_json(run_dir / "pysr_environment.json")
    runtime = load_json(run_dir / "pysr_runtime_settings.json")
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
        raise SystemExit("Final_CLs must not appear in score artifacts.")
    if list(metadata.get("features", [])) != EXPECTED_FEATURES:
        raise SystemExit(f"Unexpected features in metadata: {metadata.get('features')}")
    if metadata.get("target") != "exclusion":
        raise SystemExit(f"Unexpected target in metadata: {metadata.get('target')}")
    if metrics.get("score_source") != "PySRRegressor.predict_continuous_score":
        raise SystemExit(f"Unexpected score source: {metrics.get('score_source')}")
    if metrics.get("auc_rule") != "continuous_scores_only":
        raise SystemExit(f"Unexpected AUC rule: {metrics.get('auc_rule')}")
    if not environment.get("julia_backend_initialized"):
        raise SystemExit("Julia backend was not recorded as initialized.")
    expected_loss = "loss(prediction, target, weight) = weight * (prediction - target)^2"
    if runtime.get("elementwise_loss") != expected_loss:
        raise SystemExit(f"Unexpected PySR loss: {runtime.get('elementwise_loss')}")
    if sorted(scores["split_membership"].unique().tolist()) != ["test"]:
        raise SystemExit("Score artifact must contain only test split rows.")
    if scores["score"].isna().any():
        raise SystemExit("Continuous score column contains missing values.")
    if scores["score"].nunique() < 2:
        raise SystemExit("Continuous scores are constant; ROC-AUC validation is not meaningful.")

    recomputed_auc = float(roc_auc_score(scores["y_true"], scores["score"]))
    recomputed_ap = float(average_precision_score(scores["y_true"], scores["score"]))
    recorded_auc = float(metrics["roc_auc"])
    if recomputed_auc != recorded_auc:
        raise SystemExit(
            f"Recomputed AUC {recomputed_auc!r} does not match recorded {recorded_auc!r}."
        )

    result = {
        "validation_status": "passed",
        "run_dir": str(run_dir),
        "smoke": bool(args.smoke),
        "run_id": metadata.get("run_id"),
        "features": metadata.get("features"),
        "target": metadata.get("target"),
        "positive_label_status": metadata.get("positive_label_status"),
        "test_rows": int(len(scores)),
        "recomputed_roc_auc": recomputed_auc,
        "recomputed_average_precision": recomputed_ap,
        "reference_auc": float(args.reference_auc),
        "auc_minus_reference": recomputed_auc - float(args.reference_auc),
        "julia_version": environment.get("julia", {}).get("version"),
        "symbolic_regression_version": environment.get("julia", {}).get(
            "symbolic_regression_version"
        ),
        "git_head": git_state.get("head"),
        "git_is_clean": git_state.get("is_clean"),
        "status": "provisional, unverified, pending review",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
