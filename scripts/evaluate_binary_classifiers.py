#!/usr/bin/env python3
"""Evaluate baseline binary classifiers from a reviewed run config.

Outputs are provisional, unverified, and pending review. ROC/AUC is computed
from continuous scores only, never thresholded class labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "provisional, unverified, pending review"
THRESHOLD = 0.5
OUTPUT_FILES = (
    "metrics.json",
    "metrics.csv",
    "roc_curve_data.csv",
    "run_metadata.json",
    "roc_curve.png",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and evaluate configured binary ML baselines."
    )
    parser.add_argument("--config", required=True, help="Path to run YAML config.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing outputs in the configured output dir.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML is required. Install pyyaml before running.") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return data


def require_config(config: dict[str, Any], keys: list[str]) -> None:
    missing = [key for key in keys if key not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")


def prepare_output_dir(output_dir: Path, overwrite: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [output_dir / name for name in OUTPUT_FILES if (output_dir / name).exists()]
    if existing and not overwrite:
        paths = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing outputs: {paths}")
    if overwrite:
        for path in existing:
            path.unlink()


def git_commit() -> str | None:
    if not shutil.which("git"):
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return None


def resolve_positive_label(y_values: list[Any], configured: Any) -> tuple[Any, str]:
    unique = sorted(set(y_values))
    if configured != "requires_review":
        if configured not in unique:
            raise ValueError(f"Configured positive_label {configured!r} not in {unique!r}")
        return configured, "configured"

    numeric_unique = sorted(float(value) for value in unique)
    if numeric_unique == [0.0, 1.0]:
        matching = [value for value in unique if float(value) == 1.0]
        return matching[0], "inferred_numeric_one_pending_review"

    raise ValueError(
        "positive_label is requires_review and cannot be inferred from labels. "
        "Set positive_label explicitly after review."
    )


def to_jsonable(value: Any) -> Any:
    try:
        import numpy as np
    except ImportError:  # pragma: no cover
        np = None

    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return str(value)


def get_models(seed: int) -> dict[str, Any]:
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import PolynomialFeatures, StandardScaler
        from sklearn.svm import SVC
    except ImportError as exc:
        raise SystemExit(
            "scikit-learn is required to evaluate ML baselines. Install scikit-learn."
        ) from exc

    logistic = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=seed,
                    solver="lbfgs",
                ),
            ),
        ]
    )
    polynomial_logistic = Pipeline(
        [
            ("poly", PolynomialFeatures(degree=2, include_bias=False)),
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=seed,
                    solver="lbfgs",
                ),
            ),
        ]
    )
    random_forest = RandomForestClassifier(
        n_estimators=500,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )
    histogram_gradient_boosting = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=300,
        l2_regularization=0.0,
        random_state=seed,
    )
    rbf_svm = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                SVC(
                    kernel="rbf",
                    C=3.0,
                    gamma="scale",
                    class_weight="balanced",
                    probability=False,
                    random_state=seed,
                ),
            ),
        ]
    )
    return {
        "logistic_regression": logistic,
        "polynomial_logistic_regression_degree_2": polynomial_logistic,
        "random_forest": random_forest,
        "histogram_gradient_boosting": histogram_gradient_boosting,
        "rbf_svm": rbf_svm,
    }


def fit_model(model: Any, name: str, x_train: Any, y_train: Any, sample_weight: Any) -> None:
    if hasattr(model, "steps"):
        final_step = model.steps[-1][0]
        model.fit(x_train, y_train, **{f"{final_step}__sample_weight": sample_weight})
    else:
        model.fit(x_train, y_train, sample_weight=sample_weight)


def continuous_scores(model: Any, x_test: Any) -> tuple[Any, str, bool]:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(x_test)
        return probabilities[:, 1], "predict_proba_positive_class", True
    if hasattr(model, "decision_function"):
        return model.decision_function(x_test), "decision_function", False
    raise ValueError("Model exposes neither predict_proba nor decision_function.")


def estimator_params(model: Any) -> dict[str, Any]:
    if hasattr(model, "get_params"):
        params = model.get_params(deep=False)
        return {key: to_jsonable(value) for key, value in params.items()}
    return {}


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "model",
        "status",
        "score_source",
        "roc_auc",
        "average_precision",
        "threshold",
        "accuracy_at_threshold",
        "balanced_accuracy_at_threshold",
        "true_negative",
        "false_positive",
        "false_negative",
        "true_positive",
        "note",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_roc_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["model", "fpr", "tpr", "threshold"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def maybe_write_roc_plot(path: Path, roc_rows: list[dict[str, Any]]) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    by_model: dict[str, list[dict[str, Any]]] = {}
    for row in roc_rows:
        by_model.setdefault(row["model"], []).append(row)
    for model, rows in by_model.items():
        plt.plot([row["fpr"] for row in rows], [row["tpr"] for row in rows], label=model)
    plt.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curves - provisional, pending review")
    plt.legend(fontsize="small")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return True


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    require_config(
        config,
        [
            "run_id",
            "dataset_id",
            "dataset_config",
            "raw_path",
            "task_type",
            "features",
            "target",
            "positive_label",
            "test_size",
            "split_method",
            "random_seed",
            "auc_rule",
            "imbalance_strategy",
            "output_dir",
            "review_status",
        ],
    )
    if config["task_type"] != "binary_classification_eval":
        raise ValueError(f"Unexpected task_type: {config['task_type']}")
    if config["auc_rule"] != "continuous_scores_only":
        raise ValueError("AUC rule must be continuous_scores_only.")
    if config["split_method"] != "stratified":
        raise ValueError("Only stratified split is implemented for this evaluator.")

    try:
        import pandas as pd
        from sklearn.metrics import (
            accuracy_score,
            average_precision_score,
            balanced_accuracy_score,
            confusion_matrix,
            roc_auc_score,
            roc_curve,
        )
        from sklearn.model_selection import train_test_split
        from sklearn.utils.class_weight import compute_sample_weight
    except ImportError as exc:
        raise SystemExit(
            "pandas and scikit-learn are required for baseline evaluation."
        ) from exc

    output_dir = Path(config["output_dir"])
    prepare_output_dir(output_dir, args.overwrite)

    raw_path = Path(config["raw_path"])
    data = pd.read_csv(raw_path)
    features = list(config["features"])
    target = config["target"]
    missing_columns = [column for column in features + [target] if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Configured columns not found in dataset: {missing_columns}")

    if any(column in features for column in config.get("audit_only_columns", [])):
        raise ValueError("Audit-only columns must not be used as features.")

    x = data[features]
    y_original = data[target]
    positive_label, positive_label_status = resolve_positive_label(
        y_original.tolist(), config["positive_label"]
    )
    y = (y_original == positive_label).astype(int)
    class_counts = {str(key): int(value) for key, value in y.value_counts().sort_index().items()}

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=float(config["test_size"]),
        random_state=int(config["random_seed"]),
        stratify=y,
    )
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)

    models = get_models(int(config["random_seed"]))
    metrics_rows: list[dict[str, Any]] = []
    roc_rows: list[dict[str, Any]] = []
    metadata_models: dict[str, Any] = {}

    for model_name, model in models.items():
        row: dict[str, Any] = {
            "model": model_name,
            "status": "started",
            "threshold": None,
            "note": STATUS,
            "error": None,
        }
        metadata_models[model_name] = {"hyperparameters": estimator_params(model)}
        try:
            fit_model(model, model_name, x_train, y_train, sample_weight)
            scores, score_source, probability_like = continuous_scores(model, x_test)
            auc = roc_auc_score(y_test, scores)
            ap = average_precision_score(y_test, scores)
            fpr, tpr, thresholds = roc_curve(y_test, scores)
            for fpr_value, tpr_value, threshold_value in zip(fpr, tpr, thresholds):
                roc_rows.append(
                    {
                        "model": model_name,
                        "fpr": float(fpr_value),
                        "tpr": float(tpr_value),
                        "threshold": float(threshold_value),
                    }
                )

            row.update(
                {
                    "status": "completed",
                    "score_source": score_source,
                    "roc_auc": float(auc),
                    "average_precision": float(ap),
                    "note": (
                        "AUC > 0.97 observed in this run; pending review."
                        if auc > 0.97
                        else STATUS
                    ),
                }
            )
            if probability_like:
                predictions = (scores >= THRESHOLD).astype(int)
                cm = confusion_matrix(y_test, predictions, labels=[0, 1])
                row.update(
                    {
                        "threshold": THRESHOLD,
                        "accuracy_at_threshold": float(accuracy_score(y_test, predictions)),
                        "balanced_accuracy_at_threshold": float(
                            balanced_accuracy_score(y_test, predictions)
                        ),
                        "true_negative": int(cm[0, 0]),
                        "false_positive": int(cm[0, 1]),
                        "false_negative": int(cm[1, 0]),
                        "true_positive": int(cm[1, 1]),
                    }
                )
        except Exception as exc:  # noqa: BLE001 - failures are recorded, not hidden.
            row.update({"status": "failed", "error": repr(exc), "note": STATUS})
        metrics_rows.append(row)

    metadata = {
        "status": STATUS,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "config_path": str(config_path),
        "dataset_path": str(raw_path),
        "dataset_config": config["dataset_config"],
        "run_id": config["run_id"],
        "dataset_id": config["dataset_id"],
        "task_type": config["task_type"],
        "review_status": config["review_status"],
        "features": features,
        "target": target,
        "positive_label": to_jsonable(positive_label),
        "positive_label_status": positive_label_status,
        "split_method": config["split_method"],
        "test_size": float(config["test_size"]),
        "random_seed": int(config["random_seed"]),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "class_counts_binary": class_counts,
        "imbalance_strategy": config["imbalance_strategy"],
        "auc_rule": config["auc_rule"],
        "code_version_or_commit": git_commit(),
        "models": metadata_models,
        "notes": [
            "Raw data was read only and not modified.",
            "Final_CLs was not used as a feature.",
            "ROC/AUC was computed from continuous scores only.",
            "Threshold-dependent metrics are secondary and use threshold 0.5 only where scores are probability-like.",
            "Outputs are provisional, unverified, and pending review.",
        ],
    }
    metrics_payload = {
        "status": STATUS,
        "run_id": config["run_id"],
        "metrics": metrics_rows,
    }

    with (output_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metrics_payload), handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_metrics_csv(output_dir / "metrics.csv", metrics_rows)
    write_roc_csv(output_dir / "roc_curve_data.csv", roc_rows)
    with (output_dir / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metadata), handle, indent=2, sort_keys=True)
        handle.write("\n")
    plot_written = maybe_write_roc_plot(output_dir / "roc_curve.png", roc_rows)

    completed = [row for row in metrics_rows if row.get("status") == "completed"]
    best = max(completed, key=lambda item: item["roc_auc"]) if completed else None
    print(f"Wrote outputs to {output_dir}")
    if plot_written:
        print(f"Wrote {output_dir / 'roc_curve.png'}")
    if best:
        print(
            "Best observed ROC-AUC in this run, pending review: "
            f"{best['model']} = {best['roc_auc']:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
