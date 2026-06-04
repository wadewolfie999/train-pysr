#!/usr/bin/env python3
"""Run stronger binary-classification baselines and diagnostic feature checks.

Outputs are provisional, unverified, and pending review. ROC/AUC is computed
from continuous scores only. Diagnostic Final_CLs feature sets are never treated
as approved feature sets or thesis-accepted evidence.
"""

from __future__ import annotations

import argparse
import csv
import itertools
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
    "strong_metrics.json",
    "strong_metrics.csv",
    "strong_roc_curve_data.csv",
    "strong_run_metadata.json",
    "strong_summary.md",
    "strong_predictions.csv",
    "strong_roc_curve.png",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate stronger approved and diagnostic binary baselines."
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


def validate_config(config: dict[str, Any]) -> None:
    require_config(
        config,
        [
            "run_id",
            "dataset_id",
            "dataset_config",
            "raw_path",
            "task_type",
            "target",
            "positive_label",
            "test_size",
            "split_method",
            "random_seed",
            "auc_rule",
            "review_status",
            "output_dir",
            "approved_feature_sets",
            "diagnostic_feature_sets",
            "models",
            "metrics",
        ],
    )
    if config["task_type"] != "strong_binary_classification_eval":
        raise ValueError(f"Unexpected task_type: {config['task_type']}")
    if config["auc_rule"] != "continuous_scores_only":
        raise ValueError("AUC rule must be continuous_scores_only.")
    if config["split_method"] != "stratified":
        raise ValueError("Only stratified split is implemented.")


def make_engineered_features(data: Any) -> Any:
    import numpy as np
    import pandas as pd

    if "mchi1" not in data.columns or "mchipm1" not in data.columns:
        raise ValueError("Engineered mass features require mchi1 and mchipm1.")
    delta_m = data["mchipm1"] - data["mchi1"]
    safe_mchi1 = data["mchi1"].replace(0, np.nan)
    engineered = pd.DataFrame(index=data.index)
    engineered["mchi1"] = data["mchi1"]
    engineered["mchipm1"] = data["mchipm1"]
    engineered["delta_m"] = delta_m
    engineered["sum_m"] = data["mchipm1"] + data["mchi1"]
    engineered["ratio_m"] = (data["mchipm1"] / safe_mchi1).replace(
        [np.inf, -np.inf], np.nan
    )
    engineered["log_mchi1"] = np.log1p(data["mchi1"].clip(lower=0))
    engineered["log_mchipm1"] = np.log1p(data["mchipm1"].clip(lower=0))
    engineered["log_delta_m"] = np.log1p(delta_m.clip(lower=0))
    if engineered.isna().any().any():
        raise ValueError("Engineered features contain NaN or infinite values.")
    return engineered


def build_feature_sets(data: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
    feature_sets: list[dict[str, Any]] = []
    for entry in config["approved_feature_sets"]:
        name = entry["name"]
        if name == "mass_engineered_v1":
            frame = make_engineered_features(data)
            columns = list(frame.columns)
        else:
            columns = list(entry["columns"])
            frame = data[columns].copy()
        if "Final_CLs" in columns:
            raise ValueError("Approved feature sets must not include Final_CLs.")
        feature_sets.append(
            {
                "name": name,
                "kind": "approved",
                "diagnostic": False,
                "uses_final_cls": False,
                "warning": None,
                "columns": columns,
                "frame": frame,
            }
        )

    for entry in config["diagnostic_feature_sets"]:
        columns = list(entry["columns"])
        feature_sets.append(
            {
                "name": entry["name"],
                "kind": "diagnostic",
                "diagnostic": True,
                "uses_final_cls": "Final_CLs" in columns,
                "warning": entry.get(
                    "warning",
                    "diagnostic_only_possible_label_leakage_not_for_thesis_claims",
                ),
                "columns": columns,
                "frame": data[columns].copy(),
            }
        )
    return feature_sets


def parameter_grid(base: dict[str, Any], grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(grid)
    rows = []
    for values in itertools.product(*(grid[key] for key in keys)):
        params = dict(base)
        params.update(dict(zip(keys, values)))
        rows.append(params)
    return rows


def model_candidates(seed: int, declared: list[str]) -> list[dict[str, Any]]:
    try:
        from sklearn.ensemble import (
            ExtraTreesClassifier,
            HistGradientBoostingClassifier,
            RandomForestClassifier,
        )
        from sklearn.linear_model import LogisticRegression
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import PolynomialFeatures, StandardScaler
        from sklearn.svm import SVC
    except ImportError as exc:
        raise SystemExit("scikit-learn is required for strong baseline evaluation.") from exc

    candidates: list[dict[str, Any]] = []

    if "tuned_random_forest" in declared:
        configs = parameter_grid(
            {
                "n_estimators": 500,
                "class_weight": "balanced",
                "random_state": seed,
                "n_jobs": -1,
            },
            {"max_depth": [None, 16], "min_samples_leaf": [1, 4]},
        )
        for i, params in enumerate(configs, start=1):
            candidates.append(
                {
                    "model": "tuned_random_forest",
                    "variant": f"tuned_random_forest_{i:02d}",
                    "estimator": RandomForestClassifier(**params),
                    "params": params,
                }
            )

    if "extra_trees" in declared:
        configs = parameter_grid(
            {
                "n_estimators": 500,
                "class_weight": "balanced",
                "random_state": seed,
                "n_jobs": -1,
            },
            {"max_depth": [None, 16], "min_samples_leaf": [1, 4]},
        )
        for i, params in enumerate(configs, start=1):
            candidates.append(
                {
                    "model": "extra_trees",
                    "variant": f"extra_trees_{i:02d}",
                    "estimator": ExtraTreesClassifier(**params),
                    "params": params,
                }
            )

    if "hist_gradient_boosting_grid" in declared:
        configs = parameter_grid(
            {"random_state": seed},
            {
                "learning_rate": [0.03, 0.06],
                "max_iter": [300],
                "max_leaf_nodes": [31, 63],
                "l2_regularization": [0.0],
            },
        )
        for i, params in enumerate(configs, start=1):
            candidates.append(
                {
                    "model": "hist_gradient_boosting_grid",
                    "variant": f"hist_gradient_boosting_grid_{i:02d}",
                    "estimator": HistGradientBoostingClassifier(**params),
                    "params": params,
                }
            )

    if "logistic_polynomial_degree_3" in declared:
        for i, c_value in enumerate([0.3, 1.0, 3.0], start=1):
            params = {
                "degree": 3,
                "C": c_value,
                "class_weight": "balanced",
                "max_iter": 4000,
                "random_state": seed,
            }
            estimator = Pipeline(
                [
                    ("poly", PolynomialFeatures(degree=3, include_bias=False)),
                    ("scale", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(
                            C=c_value,
                            class_weight="balanced",
                            max_iter=4000,
                            random_state=seed,
                            solver="lbfgs",
                        ),
                    ),
                ]
            )
            candidates.append(
                {
                    "model": "logistic_polynomial_degree_3",
                    "variant": f"logistic_polynomial_degree_3_{i:02d}",
                    "estimator": estimator,
                    "params": params,
                }
            )

    if "rbf_svm_grid" in declared:
        configs = parameter_grid(
            {
                "kernel": "rbf",
                "class_weight": "balanced",
                "probability": False,
                "random_state": seed,
                "cache_size": 512,
            },
            {"C": [1.0, 10.0], "gamma": ["scale", 0.01]},
        )
        for i, params in enumerate(configs, start=1):
            estimator = Pipeline(
                [("scale", StandardScaler()), ("model", SVC(**params))]
            )
            candidates.append(
                {
                    "model": "rbf_svm_grid",
                    "variant": f"rbf_svm_grid_{i:02d}",
                    "estimator": estimator,
                    "params": params,
                }
            )

    if "knn_grid" in declared:
        configs = parameter_grid(
            {},
            {"n_neighbors": [15, 31], "weights": ["uniform", "distance"]},
        )
        for i, params in enumerate(configs, start=1):
            estimator = Pipeline(
                [("scale", StandardScaler()), ("model", KNeighborsClassifier(**params))]
            )
            candidates.append(
                {
                    "model": "knn_grid",
                    "variant": f"knn_grid_{i:02d}",
                    "estimator": estimator,
                    "params": params,
                }
            )

    return candidates


def fit_estimator(estimator: Any, x_train: Any, y_train: Any, sample_weight: Any) -> None:
    if hasattr(estimator, "steps"):
        final_name = estimator.steps[-1][0]
        final_estimator = estimator.steps[-1][1]
        if final_estimator.__class__.__name__ == "KNeighborsClassifier":
            estimator.fit(x_train, y_train)
        else:
            estimator.fit(x_train, y_train, **{f"{final_name}__sample_weight": sample_weight})
        return
    estimator.fit(x_train, y_train, sample_weight=sample_weight)


def continuous_scores(estimator: Any, x_test: Any) -> tuple[Any, str, bool]:
    if hasattr(estimator, "predict_proba"):
        probabilities = estimator.predict_proba(x_test)
        return probabilities[:, 1], "predict_proba_positive_class", True
    if hasattr(estimator, "decision_function"):
        return estimator.decision_function(x_test), "decision_function", False
    raise ValueError("Estimator exposes neither predict_proba nor decision_function.")


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "feature_set",
        "feature_set_kind",
        "diagnostic",
        "uses_final_cls",
        "model",
        "model_variant",
        "status",
        "score_source",
        "roc_auc",
        "average_precision",
        "threshold",
        "balanced_accuracy_at_threshold",
        "true_negative",
        "false_positive",
        "false_negative",
        "true_positive",
        "warning",
        "note",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_roc_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "feature_set",
        "feature_set_kind",
        "diagnostic",
        "uses_final_cls",
        "model",
        "model_variant",
        "fpr",
        "tpr",
        "threshold",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_predictions_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "row_index",
        "y_true",
        "feature_set",
        "model",
        "model_variant",
        "score",
        "predicted_label_if_probability_like",
        "split_membership",
        "diagnostic",
        "uses_final_cls",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def maybe_write_roc_plot(path: Path, metrics_rows: list[dict[str, Any]], roc_rows: list[dict[str, Any]]) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    completed = [row for row in metrics_rows if row.get("status") == "completed"]
    selected = sorted(completed, key=lambda row: row["roc_auc"], reverse=True)[:10]
    selected_keys = {(row["feature_set"], row["model_variant"]) for row in selected}
    for feature_set, variant in selected_keys:
        rows = [
            row
            for row in roc_rows
            if row["feature_set"] == feature_set and row["model_variant"] == variant
        ]
        if rows:
            label = f"{feature_set}:{variant}"
            plt.plot([row["fpr"] for row in rows], [row["tpr"] for row in rows], label=label)
    plt.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("Strong baseline ROC curves - provisional")
    plt.legend(fontsize="x-small")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return True


def write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    completed = [row for row in rows if row.get("status") == "completed"]
    approved = [row for row in completed if not row["diagnostic"]]
    diagnostic = [row for row in completed if row["diagnostic"]]
    approved_best = max(approved, key=lambda row: row["roc_auc"]) if approved else None
    diagnostic_best = max(diagnostic, key=lambda row: row["roc_auc"]) if diagnostic else None
    ranked = sorted(completed, key=lambda row: row["roc_auc"], reverse=True)

    lines = [
        "# Strong Baseline Summary",
        "",
        f"Status: {STATUS}.",
        "",
        "This summary reports observed run outputs only. It does not establish accepted thesis results.",
        "",
        "## Best Observed AUC",
        "",
    ]
    if approved_best:
        lines.append(
            "- Best approved feature-set ROC-AUC: "
            f"{approved_best['roc_auc']:.6f} "
            f"({approved_best['feature_set']}, {approved_best['model_variant']})."
        )
    if diagnostic_best:
        lines.append(
            "- Best diagnostic Final_CLs ROC-AUC: "
            f"{diagnostic_best['roc_auc']:.6f} "
            f"({diagnostic_best['feature_set']}, {diagnostic_best['model_variant']})."
        )
    if any(row["roc_auc"] > 0.97 for row in completed):
        lines.append("- AUC > 0.97 observed in this run; pending review.")
    else:
        lines.append("- AUC > 0.97 was not observed in this run.")

    lines.extend(
        [
            "",
            "## Ranked Results",
            "",
            "| Rank | Feature set | Type | Model variant | ROC-AUC | Average precision | Note |",
            "| ---: | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for rank, row in enumerate(ranked, start=1):
        note = "diagnostic only" if row["diagnostic"] else "approved feature set"
        lines.append(
            f"| {rank} | `{row['feature_set']}` | `{row['feature_set_kind']}` | "
            f"`{row['model_variant']}` | {row['roc_auc']:.6f} | "
            f"{row['average_precision']:.6f} | {note} |"
        )

    failed = [row for row in rows if row.get("status") == "failed"]
    if failed:
        lines.extend(["", "## Failures", ""])
        for row in failed:
            lines.append(
                f"- `{row['feature_set']}` / `{row['model_variant']}`: {row['error']}"
            )
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- Diagnostic Final_CLs feature sets are possible leakage checks and are not thesis-accepted feature sets.",
            "- ROC/AUC values use continuous scores only.",
            "- All recommendations are provisional, unverified, pending review.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    validate_config(config)

    try:
        import pandas as pd
        from sklearn.metrics import (
            average_precision_score,
            balanced_accuracy_score,
            confusion_matrix,
            roc_auc_score,
            roc_curve,
        )
        from sklearn.model_selection import train_test_split
        from sklearn.utils.class_weight import compute_sample_weight
    except ImportError as exc:
        raise SystemExit("pandas and scikit-learn are required.") from exc

    output_dir = Path(config["output_dir"])
    prepare_output_dir(output_dir, args.overwrite)

    raw_path = Path(config["raw_path"])
    data = pd.read_csv(raw_path)
    target = config["target"]
    if target not in data.columns:
        raise ValueError(f"Target column not found: {target}")
    positive_label, positive_label_status = resolve_positive_label(
        data[target].tolist(), config["positive_label"]
    )
    y = (data[target] == positive_label).astype(int)
    train_index, test_index = train_test_split(
        data.index,
        test_size=float(config["test_size"]),
        random_state=int(config["random_seed"]),
        stratify=y,
    )
    y_train = y.loc[train_index]
    y_test = y.loc[test_index]
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
    class_counts = {str(key): int(value) for key, value in y.value_counts().sort_index().items()}

    feature_sets = build_feature_sets(data, config)
    candidates = model_candidates(int(config["random_seed"]), list(config["models"]))

    metrics_rows: list[dict[str, Any]] = []
    roc_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    model_metadata: list[dict[str, Any]] = []

    for feature_set in feature_sets:
        x_all = feature_set["frame"]
        x_train = x_all.loc[train_index]
        x_test = x_all.loc[test_index]
        for candidate in candidates:
            row: dict[str, Any] = {
                "feature_set": feature_set["name"],
                "feature_set_kind": feature_set["kind"],
                "diagnostic": feature_set["diagnostic"],
                "uses_final_cls": feature_set["uses_final_cls"],
                "model": candidate["model"],
                "model_variant": candidate["variant"],
                "status": "started",
                "threshold": None,
                "warning": feature_set["warning"],
                "note": STATUS,
                "error": None,
                "hyperparameters": candidate["params"],
            }
            model_metadata.append(
                {
                    "feature_set": feature_set["name"],
                    "model": candidate["model"],
                    "model_variant": candidate["variant"],
                    "hyperparameters": to_jsonable(candidate["params"]),
                }
            )
            try:
                estimator = candidate["estimator"]
                fit_estimator(estimator, x_train, y_train, sample_weight)
                scores, score_source, probability_like = continuous_scores(estimator, x_test)
                auc = roc_auc_score(y_test, scores)
                average_precision = average_precision_score(y_test, scores)
                fpr, tpr, thresholds = roc_curve(y_test, scores)
                for fpr_value, tpr_value, threshold_value in zip(fpr, tpr, thresholds):
                    roc_rows.append(
                        {
                            "feature_set": feature_set["name"],
                            "feature_set_kind": feature_set["kind"],
                            "diagnostic": feature_set["diagnostic"],
                            "uses_final_cls": feature_set["uses_final_cls"],
                            "model": candidate["model"],
                            "model_variant": candidate["variant"],
                            "fpr": float(fpr_value),
                            "tpr": float(tpr_value),
                            "threshold": float(threshold_value),
                        }
                    )

                predicted = None
                if probability_like:
                    predicted = (scores >= THRESHOLD).astype(int)
                    cm = confusion_matrix(y_test, predicted, labels=[0, 1])
                    row.update(
                        {
                            "threshold": THRESHOLD,
                            "balanced_accuracy_at_threshold": float(
                                balanced_accuracy_score(y_test, predicted)
                            ),
                            "true_negative": int(cm[0, 0]),
                            "false_positive": int(cm[0, 1]),
                            "false_negative": int(cm[1, 0]),
                            "true_positive": int(cm[1, 1]),
                        }
                    )

                for position, original_index in enumerate(test_index):
                    prediction_rows.append(
                        {
                            "row_index": int(original_index),
                            "y_true": int(y.loc[original_index]),
                            "feature_set": feature_set["name"],
                            "model": candidate["model"],
                            "model_variant": candidate["variant"],
                            "score": float(scores[position]),
                            "predicted_label_if_probability_like": (
                                int(predicted[position]) if predicted is not None else ""
                            ),
                            "split_membership": "test",
                            "diagnostic": feature_set["diagnostic"],
                            "uses_final_cls": feature_set["uses_final_cls"],
                        }
                    )

                row.update(
                    {
                        "status": "completed",
                        "score_source": score_source,
                        "roc_auc": float(auc),
                        "average_precision": float(average_precision),
                        "note": (
                            "AUC > 0.97 observed in this run; pending review."
                            if auc > 0.97
                            else STATUS
                        ),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - record and continue.
                row.update({"status": "failed", "error": repr(exc), "note": STATUS})
            metrics_rows.append(row)

    completed = [row for row in metrics_rows if row.get("status") == "completed"]
    for rank, row in enumerate(
        sorted(completed, key=lambda item: item["roc_auc"], reverse=True), start=1
    ):
        row["rank"] = rank

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
        "target": target,
        "positive_label": to_jsonable(positive_label),
        "positive_label_status": positive_label_status,
        "split_method": config["split_method"],
        "test_size": float(config["test_size"]),
        "random_seed": int(config["random_seed"]),
        "train_rows": int(len(train_index)),
        "test_rows": int(len(test_index)),
        "class_counts_binary": class_counts,
        "auc_rule": config["auc_rule"],
        "code_version_or_commit": git_commit(),
        "feature_sets": [
            {
                "name": item["name"],
                "kind": item["kind"],
                "columns": item["columns"],
                "diagnostic": item["diagnostic"],
                "uses_final_cls": item["uses_final_cls"],
                "warning": item["warning"],
            }
            for item in feature_sets
        ],
        "models": model_metadata,
        "notes": [
            "Raw data was read only and not modified.",
            "Approved feature sets do not use Final_CLs.",
            "Final_CLs feature sets are diagnostic-only possible leakage checks.",
            "ROC/AUC was computed from continuous scores only.",
            "Outputs are provisional, unverified, and pending review.",
        ],
    }

    with (output_dir / "strong_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(
            to_jsonable({"status": STATUS, "run_id": config["run_id"], "metrics": metrics_rows}),
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")
    write_metrics_csv(output_dir / "strong_metrics.csv", metrics_rows)
    write_roc_csv(output_dir / "strong_roc_curve_data.csv", roc_rows)
    write_predictions_csv(output_dir / "strong_predictions.csv", prediction_rows)
    with (output_dir / "strong_run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metadata), handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_summary(output_dir / "strong_summary.md", metrics_rows)
    maybe_write_roc_plot(output_dir / "strong_roc_curve.png", metrics_rows, roc_rows)

    approved_completed = [
        row for row in completed if not row["diagnostic"]
    ]
    diagnostic_completed = [
        row for row in completed if row["diagnostic"]
    ]
    best_approved = (
        max(approved_completed, key=lambda item: item["roc_auc"])
        if approved_completed
        else None
    )
    best_diagnostic = (
        max(diagnostic_completed, key=lambda item: item["roc_auc"])
        if diagnostic_completed
        else None
    )
    print(f"Wrote outputs to {output_dir}")
    if best_approved:
        print(
            "Best approved ROC-AUC observed in this run, pending review: "
            f"{best_approved['feature_set']} / {best_approved['model_variant']} = "
            f"{best_approved['roc_auc']:.6f}"
        )
    if best_diagnostic:
        print(
            "Best diagnostic ROC-AUC observed in this run, pending review: "
            f"{best_diagnostic['feature_set']} / {best_diagnostic['model_variant']} = "
            f"{best_diagnostic['roc_auc']:.6f}"
        )
    if any(row["roc_auc"] > 0.97 for row in completed):
        print("AUC > 0.97 observed in this run; pending review.")
    else:
        print("AUC > 0.97 was not observed in this run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
