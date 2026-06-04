#!/usr/bin/env python3
"""Evaluate approved-feature AUC robustness across splits and folds.

Outputs are provisional, unverified, and pending review. Final_CLs is never used.
ROC/AUC is computed from continuous scores only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "provisional, unverified, pending review"
THRESHOLD = 0.5
OUTPUT_FILES = (
    "robustness_metrics.csv",
    "robustness_metrics.json",
    "robustness_summary.md",
    "robustness_run_metadata.json",
    "robustness_auc_boxplot.png",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate approved-feature AUC robustness.")
    parser.add_argument("--config", required=True, help="Path to robustness YAML config.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing robustness outputs.",
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
            "auc_rule",
            "review_status",
            "output_dir",
            "approved_feature_sets",
            "validation",
            "models",
            "metrics",
        ],
    )
    if config["task_type"] != "robust_binary_classification_eval":
        raise ValueError(f"Unexpected task_type: {config['task_type']}")
    if config["auc_rule"] != "continuous_scores_only":
        raise ValueError("AUC rule must be continuous_scores_only.")


def prepare_output_dir(output_dir: Path, overwrite: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [output_dir / name for name in OUTPUT_FILES if (output_dir / name).exists()]
    if existing and not overwrite:
        paths = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing robustness outputs: {paths}")
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
    raise ValueError("positive_label requires review and cannot be inferred.")


def make_engineered_features(data: Any) -> Any:
    import numpy as np
    import pandas as pd

    delta_m = data["mchipm1"] - data["mchi1"]
    safe_mchi1 = data["mchi1"].replace(0, np.nan)
    features = pd.DataFrame(index=data.index)
    features["mchi1"] = data["mchi1"]
    features["mchipm1"] = data["mchipm1"]
    features["delta_m"] = delta_m
    features["sum_m"] = data["mchipm1"] + data["mchi1"]
    features["ratio_m"] = (data["mchipm1"] / safe_mchi1).replace([np.inf, -np.inf], np.nan)
    features["log_mchi1"] = np.log1p(data["mchi1"].clip(lower=0))
    features["log_mchipm1"] = np.log1p(data["mchipm1"].clip(lower=0))
    features["log_delta_m"] = np.log1p(delta_m.clip(lower=0))
    if features.isna().any().any():
        raise ValueError("Engineered features contain NaN or infinite values.")
    return features


def build_feature_sets(data: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
    feature_sets = []
    for entry in config["approved_feature_sets"]:
        if entry["name"] == "mass_engineered_v1":
            frame = make_engineered_features(data)
            columns = list(frame.columns)
        else:
            columns = list(entry["columns"])
            frame = data[columns].copy()
        if "Final_CLs" in columns:
            raise ValueError("Final_CLs must not be used in robustness validation.")
        feature_sets.append({"name": entry["name"], "columns": columns, "frame": frame})
    return feature_sets


def model_specs(seed: int, declared: list[str]) -> list[dict[str, Any]]:
    try:
        from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise SystemExit("scikit-learn is required for robustness validation.") from exc

    specs = []
    if "hist_gradient_boosting_grid_01_or_best_equivalent" in declared:
        params = {
            "learning_rate": 0.03,
            "max_iter": 300,
            "max_leaf_nodes": 31,
            "l2_regularization": 0.0,
            "random_state": seed,
        }
        specs.append(
            {
                "model": "hist_gradient_boosting_grid_01_or_best_equivalent",
                "variant": "hist_gradient_boosting_grid_01_equivalent",
                "params": params,
                "assumption": "Equivalent to strong-baseline grid_01 with run-specific seed.",
                "factory": lambda p=params: HistGradientBoostingClassifier(**p),
            }
        )
    if "knn_grid_04_or_best_equivalent" in declared:
        params = {"n_neighbors": 31, "weights": "distance"}
        specs.append(
            {
                "model": "knn_grid_04_or_best_equivalent",
                "variant": "knn_grid_04_equivalent",
                "params": params,
                "assumption": "Equivalent to strong-baseline KNN grid_04.",
                "factory": lambda p=params: Pipeline(
                    [("scale", StandardScaler()), ("model", KNeighborsClassifier(**p))]
                ),
            }
        )
    if "extra_trees_best_small_grid" in declared:
        for i, params in enumerate(
            [
                {
                    "n_estimators": 500,
                    "max_depth": None,
                    "min_samples_leaf": 4,
                    "class_weight": "balanced",
                    "random_state": seed,
                    "n_jobs": -1,
                },
                {
                    "n_estimators": 500,
                    "max_depth": 16,
                    "min_samples_leaf": 4,
                    "class_weight": "balanced",
                    "random_state": seed,
                    "n_jobs": -1,
                },
            ],
            start=1,
        ):
            specs.append(
                {
                    "model": "extra_trees_best_small_grid",
                    "variant": f"extra_trees_best_small_grid_{i:02d}",
                    "params": params,
                    "assumption": "Small-grid equivalent focused on prior best leaf-size settings.",
                    "factory": lambda p=params: ExtraTreesClassifier(**p),
                }
            )
    return specs


def fit_model(estimator: Any, x_train: Any, y_train: Any, sample_weight: Any) -> None:
    if hasattr(estimator, "steps"):
        estimator.fit(x_train, y_train)
        return
    estimator.fit(x_train, y_train, sample_weight=sample_weight)


def continuous_scores(estimator: Any, x_test: Any) -> tuple[Any, str, bool]:
    if hasattr(estimator, "predict_proba"):
        probabilities = estimator.predict_proba(x_test)
        return probabilities[:, 1], "predict_proba_positive_class", True
    if hasattr(estimator, "decision_function"):
        return estimator.decision_function(x_test), "decision_function", False
    raise ValueError("Estimator exposes neither predict_proba nor decision_function.")


def run_one(
    *,
    validation_type: str,
    validation_id: str,
    seed: int | None,
    feature_set: dict[str, Any],
    spec: dict[str, Any],
    train_index: Any,
    test_index: Any,
    y: Any,
) -> dict[str, Any]:
    from sklearn.metrics import (
        average_precision_score,
        balanced_accuracy_score,
        confusion_matrix,
        roc_auc_score,
    )
    from sklearn.utils.class_weight import compute_sample_weight

    x_all = feature_set["frame"]
    x_train = x_all.loc[train_index]
    x_test = x_all.loc[test_index]
    y_train = y.loc[train_index]
    y_test = y.loc[test_index]
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)

    row = {
        "validation_type": validation_type,
        "validation_id": validation_id,
        "seed": seed,
        "feature_set": feature_set["name"],
        "model": spec["model"],
        "model_variant": spec["variant"],
        "status": "started",
        "score_source": None,
        "roc_auc": None,
        "average_precision": None,
        "balanced_accuracy_at_threshold": None,
        "true_negative": None,
        "false_positive": None,
        "false_negative": None,
        "true_positive": None,
        "threshold": None,
        "hyperparameters": spec["params"],
        "assumption": spec["assumption"],
        "note": STATUS,
        "error": None,
    }
    try:
        estimator = spec["factory"]()
        fit_model(estimator, x_train, y_train, sample_weight)
        scores, score_source, probability_like = continuous_scores(estimator, x_test)
        row.update(
            {
                "status": "completed",
                "score_source": score_source,
                "roc_auc": float(roc_auc_score(y_test, scores)),
                "average_precision": float(average_precision_score(y_test, scores)),
            }
        )
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
        if row["roc_auc"] > 0.97:
            row["note"] = "AUC > 0.97 observed in this run; pending review."
    except Exception as exc:  # noqa: BLE001 - record and continue.
        row.update({"status": "failed", "error": repr(exc), "note": STATUS})
    return row


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "validation_type",
        "validation_id",
        "seed",
        "feature_set",
        "model",
        "model_variant",
        "status",
        "score_source",
        "roc_auc",
        "average_precision",
        "balanced_accuracy_at_threshold",
        "threshold",
        "true_negative",
        "false_positive",
        "false_negative",
        "true_positive",
        "assumption",
        "note",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    completed = [row for row in rows if row["status"] == "completed"]
    groups: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in completed:
        key = (
            row["validation_type"],
            row["feature_set"],
            row["model"],
            row["model_variant"],
        )
        groups[key].append(float(row["roc_auc"]))
    summary = []
    for key, values in sorted(groups.items()):
        validation_type, feature_set, model, variant = key
        mean_auc = sum(values) / len(values)
        variance = sum((value - mean_auc) ** 2 for value in values) / len(values)
        summary.append(
            {
                "validation_type": validation_type,
                "feature_set": feature_set,
                "model": model,
                "model_variant": variant,
                "mean_roc_auc": mean_auc,
                "std_roc_auc": math.sqrt(variance),
                "min_roc_auc": min(values),
                "max_roc_auc": max(values),
                "n_runs_or_folds": len(values),
                "all_auc_gt_0_97": all(value > 0.97 for value in values),
                "mean_auc_gt_0_97": mean_auc > 0.97,
            }
        )
    return summary


def write_summary(path: Path, summary: list[dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Robustness Validation Summary",
        "",
        f"Status: {STATUS}.",
        "",
        "This summary reports observed validation outputs only. It is not an accepted thesis result.",
        "",
        "| Validation | Feature set | Model variant | Mean AUC | Std | Min | Max | N | All > 0.97 | Mean > 0.97 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for item in sorted(summary, key=lambda row: row["mean_roc_auc"], reverse=True):
        lines.append(
            f"| `{item['validation_type']}` | `{item['feature_set']}` | "
            f"`{item['model_variant']}` | {item['mean_roc_auc']:.6f} | "
            f"{item['std_roc_auc']:.6f} | {item['min_roc_auc']:.6f} | "
            f"{item['max_roc_auc']:.6f} | {item['n_runs_or_folds']} | "
            f"{item['all_auc_gt_0_97']} | {item['mean_auc_gt_0_97']} |"
        )
    failed = [row for row in rows if row["status"] == "failed"]
    if failed:
        lines.extend(["", "## Failures", ""])
        for row in failed:
            lines.append(
                f"- `{row['validation_type']}` `{row['feature_set']}` "
                f"`{row['model_variant']}`: {row['error']}"
            )
    if any(item["mean_auc_gt_0_97"] for item in summary):
        lines.extend(
            [
                "",
                "AUC > 0.97 mean observed in at least one validation group; pending review.",
            ]
        )
    lines.extend(["", "All recommendations are provisional, unverified, pending review.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def maybe_boxplot(path: Path, rows: list[dict[str, Any]]) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    completed = [row for row in rows if row["status"] == "completed"]
    groups: dict[str, list[float]] = defaultdict(list)
    for row in completed:
        key = f"{row['validation_type']}:{row['feature_set']}:{row['model_variant']}"
        groups[key].append(float(row["roc_auc"]))
    labels = list(groups)
    values = [groups[label] for label in labels]
    if not values:
        return False
    plt.figure(figsize=(max(8, len(labels) * 0.45), 6))
    plt.boxplot(values, labels=labels, showmeans=True)
    plt.axhline(0.97, color="red", linestyle="--", linewidth=1, label="AUC 0.97 target")
    plt.ylabel("ROC-AUC")
    plt.title("Robustness AUC distribution - provisional")
    plt.xticks(rotation=80, ha="right", fontsize="x-small")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return True


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    validate_config(config)

    try:
        import pandas as pd
        from sklearn.model_selection import StratifiedKFold, train_test_split
    except ImportError as exc:
        raise SystemExit("pandas and scikit-learn are required.") from exc

    output_dir = Path(config["output_dir"])
    prepare_output_dir(output_dir, args.overwrite)
    data = pd.read_csv(config["raw_path"])
    if "Final_CLs" in [column for fs in config["approved_feature_sets"] for column in fs.get("columns", [])]:
        raise ValueError("Final_CLs must not be used as an approved robustness feature.")
    target = config["target"]
    positive_label, positive_label_status = resolve_positive_label(
        data[target].tolist(), config["positive_label"]
    )
    y = (data[target] == positive_label).astype(int)
    feature_sets = build_feature_sets(data, config)
    base_specs = model_specs(int(config["validation"]["cross_validation"]["random_seed"]), config["models"])

    rows: list[dict[str, Any]] = []
    repeated = config["validation"]["repeated_splits"]
    if repeated.get("enabled"):
        for seed in repeated["seeds"]:
            specs = model_specs(int(seed), config["models"])
            train_index, test_index = train_test_split(
                data.index,
                test_size=float(repeated["test_size"]),
                random_state=int(seed),
                stratify=y,
            )
            for feature_set in feature_sets:
                for spec in specs:
                    rows.append(
                        run_one(
                            validation_type="repeated_split",
                            validation_id=f"seed_{seed}",
                            seed=int(seed),
                            feature_set=feature_set,
                            spec=spec,
                            train_index=train_index,
                            test_index=test_index,
                            y=y,
                        )
                    )

    cv = config["validation"]["cross_validation"]
    if cv.get("enabled"):
        splitter = StratifiedKFold(
            n_splits=int(cv["n_splits"]),
            shuffle=bool(cv["shuffle"]),
            random_state=int(cv["random_seed"]),
        )
        for fold, (train_pos, test_pos) in enumerate(splitter.split(data.index, y), start=1):
            train_index = data.index[train_pos]
            test_index = data.index[test_pos]
            for feature_set in feature_sets:
                for spec in base_specs:
                    rows.append(
                        run_one(
                            validation_type="cross_validation",
                            validation_id=f"fold_{fold}",
                            seed=int(cv["random_seed"]),
                            feature_set=feature_set,
                            spec=spec,
                            train_index=train_index,
                            test_index=test_index,
                            y=y,
                        )
                    )

    summary = summarize_rows(rows)
    write_metrics_csv(output_dir / "robustness_metrics.csv", rows)
    with (output_dir / "robustness_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(
            to_jsonable({"status": STATUS, "run_id": config["run_id"], "metrics": rows, "summary": summary}),
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")
    write_summary(output_dir / "robustness_summary.md", summary, rows)
    maybe_boxplot(output_dir / "robustness_auc_boxplot.png", rows)

    metadata = {
        "status": STATUS,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "config_path": str(config_path),
        "dataset_path": config["raw_path"],
        "dataset_config": config["dataset_config"],
        "run_id": config["run_id"],
        "dataset_id": config["dataset_id"],
        "task_type": config["task_type"],
        "review_status": config["review_status"],
        "target": target,
        "positive_label": to_jsonable(positive_label),
        "positive_label_status": positive_label_status,
        "auc_rule": config["auc_rule"],
        "code_version_or_commit": git_commit(),
        "feature_sets": [
            {"name": fs["name"], "columns": fs["columns"]} for fs in feature_sets
        ],
        "models": [
            {
                "model": spec["model"],
                "model_variant": spec["variant"],
                "hyperparameters": to_jsonable(spec["params"]),
                "assumption": spec["assumption"],
            }
            for spec in base_specs
        ],
        "validation": config["validation"],
        "notes": [
            "Raw data was read only and not modified.",
            "Final_CLs was not used.",
            "ROC/AUC was computed from continuous scores only.",
            "Outputs are provisional, unverified, and pending review.",
        ],
    }
    with (output_dir / "robustness_run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metadata), handle, indent=2, sort_keys=True)
        handle.write("\n")

    best = max(
        [row for row in rows if row["status"] == "completed"],
        key=lambda row: float(row["roc_auc"]),
        default=None,
    )
    print(f"Wrote robustness outputs to {output_dir}")
    if best:
        print(
            "Best robustness ROC-AUC observed, pending review: "
            f"{best['feature_set']} / {best['model_variant']} / "
            f"{best['validation_id']} = {best['roc_auc']:.6f}"
        )
    if any(item["mean_auc_gt_0_97"] for item in summary):
        print("Mean AUC > 0.97 observed in at least one group; pending review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
