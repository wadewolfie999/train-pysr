#!/usr/bin/env python3
"""Small, non-claim-bearing PySR learning run.

This is a learning entry point, not a reproduction, validation, stability
study, or thesis-evidence workflow.
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import json
import platform
import random
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


# Edit these constants deliberately before a learning run.
RUN_LABEL = "LEARNING RUN — NON-CLAIM-BEARING"
RUN_ID = "masses_exclusions_pysr_learning_v4.4.4"
DATASET_PATH = Path("data/raw/masses_exclusions.csv")
OUTPUT_DIR = Path("outputs/learning_runs") / RUN_ID

FEATURES = ["mchi1", "mchipm1"]
TARGET = "exclusion"
POSITIVE_CLASS = 1
TEST_SIZE = 0.20

PYTHON_RANDOM_SEED = 46
SPLIT_RANDOM_SEED = 46
PYSR_RANDOM_SEED = 46

BINARY_OPERATORS: list[str] = ["+", "-", "*", "/"]

UNARY_OPERATORS: list[str] = [
    "neg",
    "sign",
    "inv",
    "square",
    "cube",
    "sqrt",
    "abs",
    "relu",
    "exp",
    "log",
    "log1p",
    "sin",
    "cosh",
    "tanh",
]
ELEMENTWISE_LOSS = "loss(prediction, target, weight) = weight * (prediction - target)^2"

# Small settings intended for learning the end-to-end path.
NITERATIONS = 60
MAXSIZE = 200
POPULATIONS = 2
POPULATION_SIZE = 20
TIMEOUT_IN_SECONDS = 300
PARSIMONY = 0.0001

# Log-friendly evaluation progress settings; these do not change the PySR search.
PREDICTION_BATCH_SIZE = 512
HEARTBEAT_INTERVAL_SECONDS = 30
PROGRESS_BAR_WIDTH = 30


def write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def installed_package_version(distribution_name: str) -> str:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def runtime_versions_payload() -> dict[str, object]:
    try:
        from juliacall import Main as julia_main

        julia_version = str(julia_main.VERSION)
    except Exception as exc:
        julia_version = f"unavailable ({type(exc).__name__}: {exc})"

    return {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "julia": {"version": julia_version},
        "packages": {
            "pysr": installed_package_version("pysr"),
            "juliacall": installed_package_version("juliacall"),
            "numpy": installed_package_version("numpy"),
            "pandas": installed_package_version("pandas"),
            "scikit-learn": installed_package_version("scikit-learn"),
        },
    }


def print_metadata(payload: dict[str, object]) -> None:
    print("===== RUN METADATA BEGIN =====", flush=True)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), flush=True)
    print("===== RUN METADATA END =====", flush=True)


def format_duration(seconds: float) -> str:
    rounded_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(rounded_seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


@contextlib.contextmanager
def elapsed_heartbeat(label: str):
    started_at = time.monotonic()
    stop_event = threading.Event()

    def report_elapsed_time() -> None:
        while not stop_event.wait(HEARTBEAT_INTERVAL_SECONDS):
            elapsed = time.monotonic() - started_at
            print(
                f"{label}: still running; elapsed {format_duration(elapsed)}",
                flush=True,
            )

    print(f"{label}: started", flush=True)
    reporter = threading.Thread(target=report_elapsed_time, daemon=True)
    reporter.start()
    try:
        yield
    except BaseException:
        stop_event.set()
        reporter.join()
        elapsed = time.monotonic() - started_at
        print(f"{label}: stopped after {format_duration(elapsed)}", flush=True)
        raise
    else:
        stop_event.set()
        reporter.join()
        elapsed = time.monotonic() - started_at
        print(f"{label}: finished in {format_duration(elapsed)}", flush=True)


def print_prediction_progress(*, completed: int, total: int, started_at: float) -> None:
    fraction = completed / total
    filled = min(PROGRESS_BAR_WIDTH, int(PROGRESS_BAR_WIDTH * fraction))
    bar = "#" * filled + "-" * (PROGRESS_BAR_WIDTH - filled)
    elapsed = time.monotonic() - started_at
    if completed:
        estimated_total = elapsed / fraction
        remaining = max(0.0, estimated_total - elapsed)
        eta_text = format_duration(remaining)
    else:
        eta_text = "unknown"
    print(
        "Held-out prediction: "
        f"[{bar}] {completed}/{total} ({fraction:6.2%}) "
        f"elapsed {format_duration(elapsed)} ETA {eta_text}",
        flush=True,
    )


def predict_with_progress(model, x_test):
    import numpy as np

    total_rows = len(x_test)
    if total_rows == 0:
        raise ValueError("Held-out prediction requires at least one test row.")

    started_at = time.monotonic()
    print_prediction_progress(completed=0, total=total_rows, started_at=started_at)
    score_batches = []
    for start in range(0, total_rows, PREDICTION_BATCH_SIZE):
        stop = min(start + PREDICTION_BATCH_SIZE, total_rows)
        batch_scores = np.asarray(
            model.predict(x_test.iloc[start:stop]), dtype=float
        ).reshape(-1)
        if len(batch_scores) != stop - start:
            raise ValueError(
                "PySR returned an unexpected number of held-out scores: "
                f"expected {stop - start}, found {len(batch_scores)}."
            )
        score_batches.append(batch_scores)
        print_prediction_progress(completed=stop, total=total_rows, started_at=started_at)

    return np.concatenate(score_batches)


def load_and_validate_dataset():
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("pandas is required for this learning run.") from exc

    if not DATASET_PATH.exists():
        raise FileNotFoundError(DATASET_PATH)

    data = pd.read_csv(DATASET_PATH)
    required_columns = FEATURES + [TARGET]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required dataset columns: {missing_columns}")
    if "Final_CLs" in FEATURES or TARGET == "Final_CLs":
        raise ValueError("Final_CLs is audit-only and cannot be used here.")
    if data[required_columns].isna().any().any():
        raise ValueError("Features and target must not contain missing values.")
    target_values = set(data[TARGET].unique().tolist())
    if target_values != {0, 1}:
        raise ValueError(f"Expected binary target values {{0, 1}}, found {sorted(target_values)}")
    if POSITIVE_CLASS not in target_values:
        raise ValueError(f"Positive class {POSITIVE_CLASS!r} is not present in {TARGET!r}.")
    for feature in FEATURES:
        if not pd.api.types.is_numeric_dtype(data[feature]):
            raise TypeError(f"Feature must be numeric: {feature}")
    return data


def metadata_payload(*, fit_status: str, **extra: object) -> dict[str, object]:
    return {
        "status": RUN_LABEL,
        "run_id": RUN_ID,
        "dataset_path": str(DATASET_PATH),
        "output_dir": str(OUTPUT_DIR),
        "features": FEATURES,
        "target": TARGET,
        "positive_class": POSITIVE_CLASS,
        "test_size": TEST_SIZE,
        "python_random_seed": PYTHON_RANDOM_SEED,
        "split_random_seed": SPLIT_RANDOM_SEED,
        "pysr_random_seed": PYSR_RANDOM_SEED,
        "binary_operators": BINARY_OPERATORS,
        "unary_operators": UNARY_OPERATORS,
        "elementwise_loss": ELEMENTWISE_LOSS,
        "search_settings": {
            "niterations": NITERATIONS,
            "maxsize": MAXSIZE,
            "populations": POPULATIONS,
            "population_size": POPULATION_SIZE,
            "timeout_in_seconds": TIMEOUT_IN_SECONDS,
            "parsimony": PARSIMONY,
            "model_selection": "best",
            "parallelism": "serial",
        },
        "evaluation_progress_settings": {
            "prediction_batch_size": PREDICTION_BATCH_SIZE,
            "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
            "progress_bar_width": PROGRESS_BAR_WIDTH,
        },
        "fit_status": fit_status,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def record_failure(output_dir: Path, error: BaseException) -> None:
    try:
        write_json(
            output_dir / "run_metadata.json",
            metadata_payload(
                fit_status="failed_or_interrupted_learning_run",
                error_type=type(error).__name__,
                error_message=str(error),
            ),
        )
    except BaseException:
        # Preserve the original failure if failure recording itself fails.
        pass


def main() -> int:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing learning run: {OUTPUT_DIR}")

    import numpy as np
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.utils.class_weight import compute_sample_weight

    random.seed(PYTHON_RANDOM_SEED)
    np.random.seed(PYTHON_RANDOM_SEED)

    data = load_and_validate_dataset()
    x = data[FEATURES]
    y = (data[TARGET] == POSITIVE_CLASS).astype(int)

    train_index, test_index = train_test_split(
        data.index,
        test_size=TEST_SIZE,
        random_state=SPLIT_RANDOM_SEED,
        stratify=y,
        shuffle=True,
    )
    if set(train_index).intersection(test_index):
        raise RuntimeError("Train and test rows overlap.")
    if len(set(train_index).union(test_index)) != len(data.index):
        raise RuntimeError("Train/test split does not cover every input row exactly once.")

    x_train = x.loc[train_index]
    x_test = x.loc[test_index]
    y_train = y.loc[train_index]
    y_test = y.loc[test_index]
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)

    OUTPUT_DIR.mkdir(parents=True)
    try:
        pysr_workspace = OUTPUT_DIR / "pysr_workspace"
        pysr_workspace.mkdir()
        try:
            from pysr import PySRRegressor
        except ImportError as exc:
            raise SystemExit("PySR is required for this learning run.") from exc

        runtime_versions = runtime_versions_payload()
        initial_metadata = metadata_payload(
            fit_status="about_to_start",
            train_rows=len(x_train),
            test_rows=len(x_test),
            sample_weight="balanced training weights",
            runtime_versions=runtime_versions,
        )
        write_json(OUTPUT_DIR / "run_metadata.json", initial_metadata)
        print_metadata(initial_metadata)

        # Main learning sequence: construct, fit on train rows, then score held-out rows.
        model = PySRRegressor(
            niterations=NITERATIONS,
            maxsize=MAXSIZE,
            populations=POPULATIONS,
            population_size=POPULATION_SIZE,
            timeout_in_seconds=TIMEOUT_IN_SECONDS,
            parsimony=PARSIMONY,
            parallelism="serial",
            precision=32,
            deterministic=True,
            warm_start=False,
            model_selection="best",
            elementwise_loss=ELEMENTWISE_LOSS,
            binary_operators=BINARY_OPERATORS,
            unary_operators=UNARY_OPERATORS,
            random_state=PYSR_RANDOM_SEED,
            output_directory=str(pysr_workspace),
            run_id=RUN_ID,
            temp_equation_file=False,
            delete_tempfiles=False,
            verbosity=1,
            progress=True,
        )
        fit_started_at = time.monotonic()
        with elapsed_heartbeat("PySR search and result finalization"):
            model.fit(x_train, y_train.to_numpy(), weights=sample_weight)
        fit_elapsed_seconds = time.monotonic() - fit_started_at

        selection_started_at = time.monotonic()
        with elapsed_heartbeat("Selected-expression selection"):
            selected_expression = str(model.get_best()["sympy_format"])
        selection_elapsed_seconds = time.monotonic() - selection_started_at

        prediction_started_at = time.monotonic()
        scores = predict_with_progress(model, x_test)
        prediction_elapsed_seconds = time.monotonic() - prediction_started_at
        if not np.isfinite(scores).all():
            raise ValueError("PySR produced a non-finite held-out score.")

        scores_are_constant = bool(np.unique(scores).size < 2)
        auc_started_at = time.monotonic()
        print("Held-out ROC-AUC calculation: started", flush=True)
        roc_auc = float(roc_auc_score(y_test, scores))
        auc_elapsed_seconds = time.monotonic() - auc_started_at
        print(
            "Held-out ROC-AUC calculation: "
            f"finished in {auc_elapsed_seconds:.3f} seconds; value {roc_auc:.6f}",
            flush=True,
        )
        equations = getattr(model, "equations_", None)
        if equations is not None:
            equations_output = equations.copy()
            equations_output.insert(0, "run_label", RUN_LABEL)
            equations_output.to_csv(OUTPUT_DIR / "equations.csv", index=False)
        (OUTPUT_DIR / "selected_expression.txt").write_text(
            f"{RUN_LABEL}\nselected_expression: {selected_expression}\n",
            encoding="utf-8",
        )

        score_rows = x_test.copy()
        score_rows.insert(0, "row_index", x_test.index)
        score_rows["y_true"] = y_test.to_numpy()
        score_rows["continuous_score"] = scores
        score_rows["score_source"] = "PySRRegressor.predict"
        score_rows["run_label"] = RUN_LABEL
        score_rows.to_csv(OUTPUT_DIR / "held_out_scores.csv", index=False)

        write_json(
            OUTPUT_DIR / "metrics.json",
            {
                "status": RUN_LABEL,
                "roc_auc": roc_auc,
                "scores_are_constant": scores_are_constant,
                "score_source": "continuous PySR predictions",
                "metric_note": "Descriptive learning-run output only; not a claim or evidence.",
                "selected_expression": selected_expression,
            },
        )
        write_json(
            OUTPUT_DIR / "run_metadata.json",
            metadata_payload(
                fit_status="completed_learning_run",
                train_rows=len(x_train),
                test_rows=len(x_test),
                sample_weight="balanced training weights",
                runtime_versions=runtime_versions,
                stage_timings_seconds={
                    "pysr_search_and_result_finalization": fit_elapsed_seconds,
                    "selected_expression_selection": selection_elapsed_seconds,
                    "held_out_prediction": prediction_elapsed_seconds,
                    "held_out_roc_auc": auc_elapsed_seconds,
                },
                selected_expression=selected_expression,
                scores_are_constant=scores_are_constant,
                roc_auc=roc_auc,
            ),
        )

        print(RUN_LABEL)
        print(f"Selected expression: {selected_expression}")
        print(f"Held-out ROC-AUC from continuous scores: {roc_auc:.6f}")
        print(f"Outputs: {OUTPUT_DIR}")
        return 0
    except BaseException as exc:
        record_failure(OUTPUT_DIR, exc)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
