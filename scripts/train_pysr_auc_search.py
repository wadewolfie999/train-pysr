#!/usr/bin/env python3
"""Run a reviewed PySR continuous-score search for binary ROC/AUC evaluation.

Default usage should start with --dry-run. Full training requires PySR and an
explicit user command. Outputs are provisional, unverified, and pending review.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "provisional, unverified, pending review"
OUTPUT_FILES = (
    "pysr_metrics.json",
    "pysr_equations.csv",
    "pysr_run_metadata.json",
    "pysr_roc_curve_data.csv",
    "pysr_roc_curve.png",
    "pysr_model.pkl",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train/evaluate a PySR AUC search.")
    parser.add_argument("--config", required=True, help="Path to PySR run YAML config.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and paths without importing PySR or training.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing PySR outputs in the configured output dir.",
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


def prepare_output_dir(output_dir: Path, overwrite: bool, dry_run: bool) -> None:
    if dry_run:
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [output_dir / name for name in OUTPUT_FILES if (output_dir / name).exists()]
    if existing and not overwrite:
        paths = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing PySR outputs: {paths}")
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


def validate_config(config: dict[str, Any]) -> None:
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
            "objective",
            "expression_simplicity",
            "output_dir",
            "review_status",
            "pysr_options",
        ],
    )
    if config["task_type"] != "pysr_symbolic_score_search":
        raise ValueError(f"Unexpected task_type: {config['task_type']}")
    if config["auc_rule"] != "continuous_scores_only":
        raise ValueError("AUC rule must be continuous_scores_only.")
    if config["split_method"] != "stratified":
        raise ValueError("Only stratified split is implemented.")
    if config["objective"] != "maximize_roc_auc":
        raise ValueError("PySR search config objective must be maximize_roc_auc.")


def write_roc_csv(path: Path, fpr: Any, tpr: Any, thresholds: Any) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["fpr", "tpr", "threshold"])
        writer.writeheader()
        for fpr_value, tpr_value, threshold_value in zip(fpr, tpr, thresholds):
            writer.writerow(
                {
                    "fpr": float(fpr_value),
                    "tpr": float(tpr_value),
                    "threshold": float(threshold_value),
                }
            )


def maybe_write_roc_plot(path: Path, fpr: Any, tpr: Any) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    plt.plot(fpr, tpr, label="PySR continuous score")
    plt.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("PySR ROC curve - provisional, pending review")
    plt.legend(fontsize="small")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return True


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    validate_config(config)

    raw_path = Path(config["raw_path"])
    dataset_config = Path(config["dataset_config"])
    output_dir = Path(config["output_dir"])
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if not dataset_config.exists():
        raise FileNotFoundError(dataset_config)
    prepare_output_dir(output_dir, args.overwrite, args.dry_run)

    try:
        import pandas as pd
        from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
        from sklearn.model_selection import train_test_split
        from sklearn.utils.class_weight import compute_sample_weight
    except ImportError as exc:
        raise SystemExit("pandas and scikit-learn are required for PySR evaluation.") from exc

    data = pd.read_csv(raw_path)
    features = list(config["features"])
    target = config["target"]
    missing_columns = [column for column in features + [target] if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Configured columns not found in dataset: {missing_columns}")

    x = data[features]
    y_original = data[target]
    positive_label, positive_label_status = resolve_positive_label(
        y_original.tolist(), config["positive_label"]
    )
    y = (y_original == positive_label).astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=float(config["test_size"]),
        random_state=int(config["random_seed"]),
        stratify=y,
    )
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)

    if args.dry_run:
        print("Dry run passed. No PySR training was launched.")
        print(f"Run id: {config['run_id']}")
        print(f"Dataset: {raw_path}")
        print(f"Features: {features}")
        print(f"Target: {target}")
        print(f"Output dir: {output_dir}")
        print(f"Positive label status: {positive_label_status}")
        return 0

    try:
        from pysr import PySRRegressor
    except ImportError as exc:
        raise SystemExit(
            "PySR is unavailable. Install pysr and run explicitly after review."
        ) from exc

    options = dict(config["pysr_options"])
    model = PySRRegressor(
        niterations=int(options["niterations"]),
        maxsize=int(options["maxsize"]),
        populations=int(options["populations"]),
        parsimony=float(options["parsimony"]),
        binary_operators=list(options.get("binary_operators", ["+", "-", "*", "/"])),
        unary_operators=list(options.get("unary_operators", [])),
        random_state=int(config["random_seed"]),
        model_selection="best",
    )
    model.fit(x_train.to_numpy(), y_train.to_numpy(), weights=sample_weight)
    scores = model.predict(x_test.to_numpy())
    auc = roc_auc_score(y_test, scores)
    average_precision = average_precision_score(y_test, scores)
    fpr, tpr, thresholds = roc_curve(y_test, scores)

    metrics = {
        "status": STATUS,
        "run_id": config["run_id"],
        "dataset_id": config["dataset_id"],
        "score_source": "PySRRegressor.predict_continuous_score",
        "roc_auc": float(auc),
        "average_precision": float(average_precision),
        "auc_rule": config["auc_rule"],
        "note": (
            "AUC > 0.97 observed in this run; pending review."
            if auc > 0.97
            else STATUS
        ),
    }
    metadata = {
        "status": STATUS,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "config_path": str(config_path),
        "dataset_path": str(raw_path),
        "dataset_config": str(dataset_config),
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
        "sample_weight": "compute_sample_weight(class_weight='balanced', y=y_train)",
        "pysr_options": options,
        "objective_note": (
            "PySR trains symbolic continuous scores and this script evaluates "
            "validation ROC/AUC from those scores."
        ),
        "code_version_or_commit": git_commit(),
        "notes": [
            "Raw data was read only and not modified.",
            "ROC/AUC was computed from continuous scores only.",
            "Outputs are provisional, unverified, and pending review.",
        ],
    }

    with (output_dir / "pysr_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metrics), handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_roc_csv(output_dir / "pysr_roc_curve_data.csv", fpr, tpr, thresholds)
    with (output_dir / "pysr_run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(metadata), handle, indent=2, sort_keys=True)
        handle.write("\n")

    equations = getattr(model, "equations_", None)
    if equations is not None:
        equations.to_csv(output_dir / "pysr_equations.csv", index=False)
    else:
        with (output_dir / "pysr_equations.csv").open("w", encoding="utf-8") as handle:
            handle.write("note\nNo equations_ attribute found on PySR model.\n")

    with (output_dir / "pysr_model.pkl").open("wb") as handle:
        pickle.dump(model, handle)
    maybe_write_roc_plot(output_dir / "pysr_roc_curve.png", fpr, tpr)

    print(f"Wrote PySR outputs to {output_dir}")
    print(f"Observed ROC-AUC in this run, pending review: {auc:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
