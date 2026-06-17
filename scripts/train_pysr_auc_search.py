#!/usr/bin/env python3
"""Run a reviewed PySR continuous-score search for binary ROC/AUC evaluation.

This script fits PySR with explicit squared-error loss on binary 0/1 targets as
a symbolic continuous-score surrogate. It does not directly optimize AUC. ROC
and AUC are computed after fitting from continuous PySR predictions only.

Outputs are provisional, unverified, and pending thesis-author review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import pickle
import platform
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


STATUS = "provisional, unverified, pending review"
EXPECTED_FEATURES = ["mchi1", "mchipm1"]
FORBIDDEN_COLUMNS = {"Final_CLs"}
OUTPUT_FILES = (
    "pysr_metrics.json",
    "pysr_equations.csv",
    "pysr_run_metadata.json",
    "pysr_environment.json",
    "pysr_git_state.json",
    "pysr_runtime_settings.json",
    "pysr_test_scores.csv",
    "pysr_roc_curve_data.csv",
    "pysr_roc_curve.png",
    "pysr_model.pkl",
    "pysr_stdout_stderr.log",
    "pysr_artifact_manifest.json",
)


class Tee:
    """Write PySR output to both the console and the run log."""

    def __init__(self, *streams: Any) -> None:
        self.streams = streams

    def write(self, text: str) -> int:
        for stream in self.streams:
            stream.write(text)
            stream.flush()
        return len(text)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train/evaluate a PySR score search.")
    parser.add_argument("--config", required=True, help="Path to PySR run YAML config.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config, data, split, output policy, and Git policy without training.",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Initialize the PySR juliacall backend and report environment details.",
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
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return str(value)


def package_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def run_git(args: list[str]) -> tuple[int, str, str]:
    if not shutil.which("git"):
        return 127, "", "git not found"
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def git_state() -> dict[str, Any]:
    head_code, head, head_err = run_git(["rev-parse", "HEAD"])
    status_code, status, status_err = run_git(["status", "--short", "--untracked-files=all"])
    diff_code, diff, diff_err = run_git(["diff", "--stat"])
    return {
        "head": head if head_code == 0 else None,
        "head_error": head_err if head_code else None,
        "status_short": status.splitlines() if status else [],
        "status_error": status_err if status_code else None,
        "diff_stat": diff,
        "diff_error": diff_err if diff_code else None,
        "is_clean": status_code == 0 and status == "",
    }


def collect_environment(*, initialize_backend: bool) -> dict[str, Any]:
    env = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
        },
        "packages": {
            "pysr": package_version("pysr"),
            "juliacall": package_version("juliacall"),
            "juliapkg": package_version("juliapkg"),
            "scikit-learn": package_version("scikit-learn"),
            "numpy": package_version("numpy"),
            "pandas": package_version("pandas"),
            "PyYAML": package_version("PyYAML"),
            "matplotlib": package_version("matplotlib"),
        },
        "environment_variables": {
            key: os.environ.get(key)
            for key in [
                "JULIA_NUM_THREADS",
                "JULIA_DEPOT_PATH",
                "PYTHON_JULIACALL_EXE",
                "PYTHON_JULIACALL_HANDLE_SIGNALS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "PYTHONUNBUFFERED",
            ]
        },
        "julia_backend_initialized": False,
        "julia": {},
    }
    if not initialize_backend:
        return env

    try:
        from juliacall import Main as jl

        jl.seval("using Pkg")
        jl.seval("using SymbolicRegression")
        env["julia_backend_initialized"] = True
        env["julia"] = {
            "version": str(jl.seval("string(VERSION)")),
            "threads": int(jl.seval("Threads.nthreads()")),
            "cpu_threads": int(jl.seval("Sys.CPU_THREADS")),
            "active_project": str(jl.seval("Base.active_project()")),
            "depot_path": [str(item) for item in jl.seval("DEPOT_PATH")],
            "load_path": [str(item) for item in jl.seval("LOAD_PATH")],
            "symbolic_regression_version": str(
                jl.seval(
                    'string(Pkg.dependencies()[Base.UUID("8254be44-1295-4e6a-a16d-46603ac705cb")].version)'
                )
            ),
        }
    except Exception as exc:  # noqa: BLE001 - report backend failure clearly.
        env["julia_backend_error"] = f"{type(exc).__name__}: {exc}"
        raise
    return env


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
            "run_policy",
            "runtime",
            "reference",
            "pysr_options",
        ],
    )
    if config["task_type"] != "pysr_symbolic_score_search":
        raise ValueError(f"Unexpected task_type: {config['task_type']}")
    if list(config["features"]) != EXPECTED_FEATURES:
        raise ValueError(f"PySR v1 must use approved features only: {EXPECTED_FEATURES}")
    if FORBIDDEN_COLUMNS.intersection(config["features"] + [config["target"]]):
        raise ValueError("Final_CLs must not be used as a feature or target.")
    if config["auc_rule"] != "continuous_scores_only":
        raise ValueError("AUC rule must be continuous_scores_only.")
    if config["split_method"] != "stratified":
        raise ValueError("Only stratified split is implemented.")
    expected_objective = "squared_error_symbolic_score_surrogate_with_roc_auc_evaluation"
    if config["objective"] != expected_objective:
        raise ValueError(f"PySR objective must be {expected_objective!r}.")
    if config["run_policy"].get("allow_overwrite") is not False:
        raise ValueError("Run policy must set allow_overwrite: false.")
    if config["runtime"].get("python_juliacall_handle_signals") != "yes":
        raise ValueError('Runtime must set python_juliacall_handle_signals: "yes".')
    options = config["pysr_options"]
    if "elementwise_loss" not in options:
        raise ValueError("PySR options must explicitly define squared-error elementwise_loss.")
    expected_loss = "loss(prediction, target, weight) = weight * (prediction - target)^2"
    if options["elementwise_loss"] != expected_loss:
        raise ValueError(f"elementwise_loss must be {expected_loss!r}.")
    if options.get("temp_equation_file") is not False:
        raise ValueError("PySR 1.5.10 output_directory runs require temp_equation_file: false.")


def prepare_output_dir(output_dir: Path, dry_run: bool, check_env: bool) -> None:
    if dry_run or check_env:
        if output_dir.exists() and any(output_dir.iterdir()):
            raise SystemExit(f"Output directory already contains files: {output_dir}")
        return
    if output_dir.exists():
        existing = list(output_dir.iterdir())
        if existing:
            raise SystemExit(f"Refusing to overwrite existing output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)


def check_git_policy(config: dict[str, Any], state: dict[str, Any], *, dry_run: bool) -> None:
    require_clean = bool(config["run_policy"].get("require_clean_worktree", False))
    if require_clean and not dry_run and not state["is_clean"]:
        detail = "\n".join(state["status_short"])
        raise SystemExit(f"Refusing training run: clean Git worktree is required.\n{detail}")


def apply_runtime_environment(config: dict[str, Any]) -> None:
    runtime = config.get("runtime", {})
    mapping = {
        "julia_num_threads": "JULIA_NUM_THREADS",
        "python_juliacall_handle_signals": "PYTHON_JULIACALL_HANDLE_SIGNALS",
        "omp_num_threads": "OMP_NUM_THREADS",
        "mkl_num_threads": "MKL_NUM_THREADS",
        "openblas_num_threads": "OPENBLAS_NUM_THREADS",
    }
    for config_key, env_key in mapping.items():
        value = runtime.get(config_key)
        if value is not None and os.environ.get(env_key) is None:
            os.environ[env_key] = str(value)
    if runtime.get("pythonunbuffered") is True and os.environ.get("PYTHONUNBUFFERED") is None:
        os.environ["PYTHONUNBUFFERED"] = "1"


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


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


def write_scores_csv(
    path: Path,
    *,
    row_indices: Any,
    x_test: Any,
    y_test: Any,
    scores: Any,
    positive_label: Any,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "row_index",
            "split_membership",
            "mchi1",
            "mchipm1",
            "y_true",
            "score",
            "score_source",
            "positive_label",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row_index, (_, feature_row), y_value, score in zip(
            row_indices,
            x_test.iterrows(),
            y_test.tolist(),
            scores,
        ):
            writer.writerow(
                {
                    "row_index": int(row_index),
                    "split_membership": "test",
                    "mchi1": float(feature_row["mchi1"]),
                    "mchipm1": float(feature_row["mchipm1"]),
                    "y_true": int(y_value),
                    "score": float(score),
                    "score_source": "PySRRegressor.predict_continuous_score",
                    "positive_label": to_jsonable(positive_label),
                }
            )


def maybe_write_roc_plot(path: Path, fpr: Any, tpr: Any, auc: float) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    plt.plot(fpr, tpr, label=f"PySR continuous score AUC = {auc:.4f}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("PySR ROC curve - provisional, pending review")
    plt.legend(fontsize="small")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(output_dir: Path) -> None:
    rows = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "pysr_artifact_manifest.json":
            rows.append(
                {
                    "path": str(path.relative_to(output_dir)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    write_json(
        output_dir / "pysr_artifact_manifest.json",
        {"status": STATUS, "artifact_count": len(rows), "artifacts": rows},
    )


def pysr_kwargs(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    options = dict(config["pysr_options"])
    workspace = output_dir / "pysr_workspace"
    tempdir = output_dir / "pysr_temp"
    workspace.mkdir(parents=True, exist_ok=False)
    tempdir.mkdir(parents=True, exist_ok=False)
    return {
        "niterations": int(options["niterations"]),
        "maxsize": int(options["maxsize"]),
        "populations": int(options["populations"]),
        "population_size": int(options.get("population_size", 27)),
        "parsimony": float(options["parsimony"]),
        "timeout_in_seconds": float(options["timeout_in_seconds"]),
        "parallelism": options.get("parallelism", "serial"),
        "precision": int(options.get("precision", 32)),
        "deterministic": bool(options.get("deterministic", True)),
        "warm_start": bool(options.get("warm_start", False)),
        "temp_equation_file": bool(options.get("temp_equation_file", True)),
        "delete_tempfiles": bool(options.get("delete_tempfiles", False)),
        "model_selection": options.get("model_selection", "best"),
        "elementwise_loss": options["elementwise_loss"],
        "binary_operators": list(options.get("binary_operators", ["+", "-", "*", "/"])),
        "unary_operators": list(options.get("unary_operators", [])),
        "random_state": int(config["random_seed"]),
        "output_directory": str(workspace),
        "run_id": config["run_id"],
        "tempdir": str(tempdir),
        "verbosity": int(options.get("verbosity", 1)),
        "progress": bool(options.get("progress", False)),
    }


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    validate_config(config)
    apply_runtime_environment(config)

    raw_path = Path(config["raw_path"])
    dataset_config = Path(config["dataset_config"])
    output_dir = Path(config["output_dir"])
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if not dataset_config.exists():
        raise FileNotFoundError(dataset_config)

    git = git_state()
    check_git_policy(config, git, dry_run=args.dry_run or args.check_env)
    prepare_output_dir(output_dir, args.dry_run, args.check_env)

    environment = collect_environment(initialize_backend=args.check_env)
    if args.check_env:
        print(json.dumps(to_jsonable(environment), indent=2, sort_keys=True))
        return 0

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
    if FORBIDDEN_COLUMNS.intersection(features):
        raise ValueError("Final_CLs must not be used as a feature.")

    x = data[features]
    y_original = data[target]
    positive_label, positive_label_status = resolve_positive_label(
        y_original.tolist(), config["positive_label"]
    )
    y = (y_original == positive_label).astype(int)
    train_index, test_index = train_test_split(
        data.index,
        test_size=float(config["test_size"]),
        random_state=int(config["random_seed"]),
        stratify=y,
    )
    x_train = x.loc[train_index]
    x_test = x.loc[test_index]
    y_train = y.loc[train_index]
    y_test = y.loc[test_index]
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)

    if args.dry_run:
        print("Dry run passed. No PySR training was launched.")
        print(f"Run id: {config['run_id']}")
        print(f"Dataset: {raw_path}")
        print(f"Features: {features}")
        print(f"Target: {target}")
        print(f"Output dir: {output_dir}")
        print(f"Train rows: {len(x_train)}")
        print(f"Test rows: {len(x_test)}")
        print(f"Positive label status: {positive_label_status}")
        print(f"Git clean: {git['is_clean']}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "pysr_stdout_stderr.log"
    write_json(output_dir / "pysr_git_state.json", {"status": STATUS, **git})
    kwargs = pysr_kwargs(config, output_dir)
    write_json(output_dir / "pysr_runtime_settings.json", {"status": STATUS, **kwargs})

    with log_path.open("w", encoding="utf-8") as log_handle:
        log_handle.write(f"PySR run started at {datetime.now(timezone.utc).isoformat()}\n")
        log_handle.write(f"Command: {' '.join(sys.argv)}\n")
        log_handle.flush()
        with redirect_stdout(Tee(sys.stdout, log_handle)), redirect_stderr(
            Tee(sys.stderr, log_handle)
        ):
            from pysr import PySRRegressor

            environment = collect_environment(initialize_backend=True)
            write_json(output_dir / "pysr_environment.json", environment)
            model = PySRRegressor(**kwargs)
            model.fit(x_train.to_numpy(), y_train.to_numpy(), weights=sample_weight)
            scores = model.predict(x_test.to_numpy())

    auc = float(roc_auc_score(y_test, scores))
    average_precision = float(average_precision_score(y_test, scores))
    fpr, tpr, thresholds = roc_curve(y_test, scores)
    reference_auc = float(config["reference"]["fixed_split_hist_gradient_boosting_auc"])

    metrics = {
        "status": STATUS,
        "run_id": config["run_id"],
        "dataset_id": config["dataset_id"],
        "score_source": "PySRRegressor.predict_continuous_score",
        "fit_objective": config["objective"],
        "loss": config["pysr_options"]["elementwise_loss"],
        "roc_auc": auc,
        "average_precision": average_precision,
        "reference_fixed_split_hist_gradient_boosting_auc": reference_auc,
        "auc_minus_reference": auc - reference_auc,
        "auc_rule": config["auc_rule"],
        "note": STATUS,
    }
    metadata_payload = {
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
        "class_counts_binary": {
            "train": {str(k): int(v) for k, v in y_train.value_counts().sort_index().items()},
            "test": {str(k): int(v) for k, v in y_test.value_counts().sort_index().items()},
        },
        "sample_weight": "compute_sample_weight(class_weight='balanced', y=y_train)",
        "pysr_options": config["pysr_options"],
        "fit_objective_note": (
            "PySR fits weighted squared-error symbolic continuous scores to binary 0/1 targets. "
            "ROC-AUC is evaluated afterward from continuous scores and is not directly optimized."
        ),
        "git_head": git["head"],
        "git_is_clean": git["is_clean"],
        "notes": [
            "Raw data was read only and not modified.",
            "Final_CLs was excluded from features and target.",
            "ROC/AUC was computed from continuous scores only.",
            "Outputs are provisional, unverified, and pending review.",
        ],
    }
    write_json(output_dir / "pysr_metrics.json", metrics)
    write_json(output_dir / "pysr_run_metadata.json", metadata_payload)
    write_scores_csv(
        output_dir / "pysr_test_scores.csv",
        row_indices=test_index,
        x_test=x_test,
        y_test=y_test,
        scores=scores,
        positive_label=positive_label,
    )
    write_roc_csv(output_dir / "pysr_roc_curve_data.csv", fpr, tpr, thresholds)

    equations = getattr(model, "equations_", None)
    if equations is not None:
        equations.to_csv(output_dir / "pysr_equations.csv", index=False)
    else:
        with (output_dir / "pysr_equations.csv").open("w", encoding="utf-8") as handle:
            handle.write("note\nNo equations_ attribute found on PySR model.\n")

    with (output_dir / "pysr_model.pkl").open("wb") as handle:
        pickle.dump(model, handle)
    maybe_write_roc_plot(output_dir / "pysr_roc_curve.png", fpr, tpr, auc)
    write_manifest(output_dir)

    print(f"Wrote PySR outputs to {output_dir}")
    print(f"Observed ROC-AUC in this run, pending review: {auc:.6f}")
    print(f"Reference fixed-split HistGradientBoosting AUC: {reference_auc:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
