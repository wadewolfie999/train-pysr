#!/usr/bin/env python3
"""Reproduce the approved-feature AUC >= 0.97 candidate.

Outputs are provisional, unverified, and pending review. Final_CLs is never
used. ROC-AUC is computed from continuous scores only.
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
TARGET_AUC = 0.97
OUTPUT_FILES = (
    "auc97_candidate_metrics.json",
    "auc97_candidate_metrics.csv",
    "auc97_candidate_summary.md",
    "auc97_candidate_metadata.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce the mass-engineered histogram-gradient-boosting AUC candidate."
    )
    parser.add_argument("--config", required=True, help="Path to candidate YAML config.")
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
            "feature_set",
            "model",
            "candidate_split",
            "robustness",
            "metrics",
            "class_imbalance_strategy",
        ],
    )
    if config["task_type"] != "auc97_candidate_reproduction":
        raise ValueError(f"Unexpected task_type: {config['task_type']}")
    if config["auc_rule"] != "continuous_scores_only":
        raise ValueError("AUC rule must be continuous_scores_only.")
    if config["feature_set"]["name"] != "mass_engineered_v1":
        raise ValueError("This script only reproduces mass_engineered_v1.")
    if config["model"]["family"] != "histogram_gradient_boosting":
        raise ValueError("This script only reproduces histogram gradient boosting.")
    imbalance = config["class_imbalance_strategy"]
    expected_imbalance = {
        "method": "compute_sample_weight",
        "class_weight": "balanced",
        "applied_to": "training_split_only",
    }
    if imbalance != expected_imbalance:
        raise ValueError(
            "class_imbalance_strategy must declare compute_sample_weight with "
            "class_weight balanced applied to training_split_only."
        )


def prepare_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [output_dir / name for name in OUTPUT_FILES if (output_dir / name).exists()]
    if existing:
        paths = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing candidate outputs: {paths}")


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

    required = {"mchi1", "mchipm1"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing required mass columns: {missing}")

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
    if "Final_CLs" in features.columns:
        raise ValueError("Final_CLs must not be used as a feature.")
    if features.isna().any().any():
        raise ValueError("Engineered features contain NaN or infinite values.")
    return features


def model_from_config(config: dict[str, Any], seed: int) -> Any:
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
    except ImportError as exc:
        raise SystemExit("scikit-learn is required for candidate reproduction.") from exc

    params = dict(config["model"]["hyperparameters"])
    params["random_state"] = int(seed)
    return HistGradientBoostingClassifier(**params)


def run_split(
    *,
    config: dict[str, Any],
    validation_type: str,
    validation_id: str,
    seed: int,
    x_all: Any,
    y: Any,
    train_index: Any,
    test_index: Any,
) -> dict[str, Any]:
    from sklearn.metrics import roc_auc_score
    from sklearn.utils.class_weight import compute_sample_weight

    estimator = model_from_config(config, seed)
    y_train = y.loc[train_index]
    y_test = y.loc[test_index]
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
    estimator.fit(x_all.loc[train_index], y_train, sample_weight=sample_weight)
    scores = estimator.predict_proba(x_all.loc[test_index])[:, 1]
    auc = float(roc_auc_score(y_test, scores))
    return {
        "validation_type": validation_type,
        "validation_id": validation_id,
        "seed": int(seed),
        "feature_set": config["feature_set"]["name"],
        "model_family": config["model"]["family"],
        "model_variant": config["model"]["variant"],
        "status": STATUS,
        "score_source": "predict_proba_positive_class",
        "roc_auc": auc,
        "note": (
            f"AUC >= 0.97 observed in this run; {STATUS}."
            if auc >= TARGET_AUC
            else STATUS
        ),
    }


def population_summary(values: list[float]) -> dict[str, float | bool | int]:
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return {
        "mean": mean_value,
        "std": math.sqrt(variance),
        "min": min(values),
        "max": max(values),
        "n": len(values),
        "all_auc_gte_0_97": all(value >= TARGET_AUC for value in values),
    }


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "validation_type",
        "validation_id",
        "seed",
        "feature_set",
        "model_family",
        "model_variant",
        "status",
        "score_source",
        "roc_auc",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_summary(
    path: Path,
    *,
    seed42_auc: float,
    best_repeated_auc: float,
    repeated: dict[str, Any],
    cv: dict[str, Any],
) -> None:
    lines = [
        "# AUC 0.97 Candidate Reproduction Summary",
        "",
        f"Status: {STATUS}.",
        "",
        "This summary reports observed candidate-reproduction outputs only. It is not an accepted thesis result.",
        "",
        "## Candidate",
        "",
        "- Feature set: `mass_engineered_v1`.",
        "- Model family: histogram gradient boosting.",
        "- Split: stratified, test_size = 0.2, random_seed = 42.",
        "- Metric: ROC-AUC from continuous scores only.",
        "",
        "## Results",
        "",
        f"- Seed-42 AUC: {seed42_auc:.6f}.",
        f"- Best repeated-split AUC: {best_repeated_auc:.6f}.",
        f"- Repeated-split mean/std/min/max: {repeated['mean']:.6f} / {repeated['std']:.6f} / {repeated['min']:.6f} / {repeated['max']:.6f}.",
        f"- Cross-validation mean/std/min/max: {cv['mean']:.6f} / {cv['std']:.6f} / {cv['min']:.6f} / {cv['max']:.6f}.",
        f"- AUC >= 0.97 observed on seed 42: {seed42_auc >= TARGET_AUC}.",
        f"- AUC >= 0.97 robust across all repeated splits: {repeated['all_auc_gte_0_97']}.",
        f"- AUC >= 0.97 robust across CV folds: {cv['all_auc_gte_0_97']}.",
        "",
        "All recommendations are provisional, unverified, pending review.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


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
    prepare_output_dir(output_dir)

    data = pd.read_csv(config["raw_path"])
    target = config["target"]
    if target not in data.columns:
        raise ValueError(f"Target column not found: {target}")
    positive_label, positive_label_status = resolve_positive_label(
        data[target].tolist(), config["positive_label"]
    )
    y = (data[target] == positive_label).astype(int)
    x_all = make_engineered_features(data)

    candidate_split = config["candidate_split"]
    if candidate_split["split_method"] != "stratified":
        raise ValueError("Only stratified candidate split is implemented.")
    seed42 = int(candidate_split["random_seed"])
    train_index, test_index = train_test_split(
        data.index,
        test_size=float(candidate_split["test_size"]),
        random_state=seed42,
        stratify=y,
    )
    candidate_row = run_split(
        config=config,
        validation_type="candidate_seed_42",
        validation_id="seed_42",
        seed=seed42,
        x_all=x_all,
        y=y,
        train_index=train_index,
        test_index=test_index,
    )
    seed42_auc = float(candidate_row["roc_auc"])
    if seed42_auc < TARGET_AUC:
        raise SystemExit(
            "Candidate failed hard reproduction rule: "
            f"seed-42 AUC {seed42_auc:.6f} < {TARGET_AUC:.2f}. "
            "No alternative search was run."
        )

    rows = [candidate_row]
    repeated_config = config["robustness"]["repeated_splits"]
    if repeated_config["split_method"] != "stratified":
        raise ValueError("Only stratified repeated splits are implemented.")
    for seed in repeated_config["seeds"]:
        split_train_index, split_test_index = train_test_split(
            data.index,
            test_size=float(repeated_config["test_size"]),
            random_state=int(seed),
            stratify=y,
        )
        rows.append(
            run_split(
                config=config,
                validation_type="repeated_split",
                validation_id=f"seed_{seed}",
                seed=int(seed),
                x_all=x_all,
                y=y,
                train_index=split_train_index,
                test_index=split_test_index,
            )
        )

    cv_config = config["robustness"]["cross_validation"]
    splitter = StratifiedKFold(
        n_splits=int(cv_config["n_splits"]),
        shuffle=bool(cv_config["shuffle"]),
        random_state=int(cv_config["random_seed"]),
    )
    for fold, (train_pos, test_pos) in enumerate(splitter.split(data.index, y), start=1):
        rows.append(
            run_split(
                config=config,
                validation_type="cross_validation",
                validation_id=f"fold_{fold}",
                seed=int(cv_config["random_seed"]),
                x_all=x_all,
                y=y,
                train_index=data.index[train_pos],
                test_index=data.index[test_pos],
            )
        )

    repeated_values = [
        float(row["roc_auc"]) for row in rows if row["validation_type"] == "repeated_split"
    ]
    cv_values = [
        float(row["roc_auc"]) for row in rows if row["validation_type"] == "cross_validation"
    ]
    repeated_summary = population_summary(repeated_values)
    cv_summary = population_summary(cv_values)
    best_repeated_auc = max(repeated_values)

    metrics_payload = {
        "status": STATUS,
        "run_id": config["run_id"],
        "target_auc": TARGET_AUC,
        "seed42_auc": seed42_auc,
        "best_repeated_split_auc": best_repeated_auc,
        "repeated_split_summary": repeated_summary,
        "cross_validation_summary": cv_summary,
        "auc_gte_0_97_observed_on_seed42": seed42_auc >= TARGET_AUC,
        "auc_gte_0_97_robust_across_repeated_splits": repeated_summary[
            "all_auc_gte_0_97"
        ],
        "auc_gte_0_97_robust_across_cv_folds": cv_summary["all_auc_gte_0_97"],
        "metrics": rows,
    }
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
        "feature_set": {
            "name": config["feature_set"]["name"],
            "columns": list(x_all.columns),
            "base_columns": config["feature_set"]["base_columns"],
            "derived_features": config["feature_set"]["derived_features"],
        },
        "model": {
            "family": config["model"]["family"],
            "sklearn_class": config["model"]["sklearn_class"],
            "variant": config["model"]["variant"],
            "hyperparameters": config["model"]["hyperparameters"],
        },
        "class_imbalance_strategy": config["class_imbalance_strategy"],
        "candidate_split": config["candidate_split"],
        "robustness": config["robustness"],
        "notes": [
            "Raw data was read only and not modified.",
            "Final_CLs was not used as a feature.",
            "ROC/AUC was computed from continuous scores only.",
            "No alternative model or feature search was run.",
            "Outputs are provisional, unverified, and pending review.",
        ],
    }

    with (output_dir / "auc97_candidate_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metrics_payload), handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_metrics_csv(output_dir / "auc97_candidate_metrics.csv", rows)
    write_summary(
        output_dir / "auc97_candidate_summary.md",
        seed42_auc=seed42_auc,
        best_repeated_auc=best_repeated_auc,
        repeated=repeated_summary,
        cv=cv_summary,
    )
    with (output_dir / "auc97_candidate_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metadata), handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Wrote AUC 0.97 candidate outputs to {output_dir}")
    print(f"Seed-42 ROC-AUC observed, pending review: {seed42_auc:.6f}")
    print(
        "Repeated-split mean/std/min/max: "
        f"{repeated_summary['mean']:.6f} / {repeated_summary['std']:.6f} / "
        f"{repeated_summary['min']:.6f} / {repeated_summary['max']:.6f}"
    )
    print(
        "CV mean/std/min/max: "
        f"{cv_summary['mean']:.6f} / {cv_summary['std']:.6f} / "
        f"{cv_summary['min']:.6f} / {cv_summary['max']:.6f}"
    )
    print(
        "Robust AUC >= 0.97 across repeated splits: "
        f"{repeated_summary['all_auc_gte_0_97']}"
    )
    print(f"Robust AUC >= 0.97 across CV folds: {cv_summary['all_auc_gte_0_97']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
