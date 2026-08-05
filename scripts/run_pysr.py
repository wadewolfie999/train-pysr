#!/usr/bin/env python3
"""Small, non-claim-bearing PySR learning run.

This is a learning entry point, not a reproduction, validation, stability
study, or thesis-evidence workflow.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path


# Edit these constants deliberately before a learning run.
RUN_LABEL = "LEARNING RUN — NON-CLAIM-BEARING"
RUN_ID = "masses_exclusions_pysr_learning_v4.1.0"
DATASET_PATH = Path("data/raw/masses_exclusions.csv")
OUTPUT_DIR = Path("outputs/learning_runs") / RUN_ID

FEATURES = ["mchi1", "mchipm1"]
TARGET = "exclusion"
POSITIVE_CLASS = 1
TEST_SIZE = 0.30

PYTHON_RANDOM_SEED = 42
SPLIT_RANDOM_SEED = 42
PYSR_RANDOM_SEED = 42

BINARY_OPERATORS = ["+", "-", "*", "/"]
UNARY_OPERATORS: list[str] = []
ELEMENTWISE_LOSS = "loss(prediction, target, weight) = weight * (prediction - target)^2"

# Small settings intended for learning the end-to-end path.
NITERATIONS = 300
MAXSIZE = 40
POPULATIONS = 2
POPULATION_SIZE = 20
TIMEOUT_IN_SECONDS = 300
PARSIMONY = 0.001


def write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


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
        write_json(
            OUTPUT_DIR / "run_metadata.json",
            metadata_payload(
                fit_status="about_to_start",
                train_rows=len(x_train),
                test_rows=len(x_test),
                sample_weight="balanced training weights",
            ),
        )

        try:
            from pysr import PySRRegressor
        except ImportError as exc:
            raise SystemExit("PySR is required for this learning run.") from exc

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
        model.fit(x_train, y_train.to_numpy(), weights=sample_weight)

        selected_expression = str(model.sympy())
        scores = np.asarray(model.predict(x_test), dtype=float)
        if not np.isfinite(scores).all():
            raise ValueError("PySR produced a non-finite held-out score.")

        scores_are_constant = bool(np.unique(scores).size < 2)
        roc_auc = float(roc_auc_score(y_test, scores))
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
