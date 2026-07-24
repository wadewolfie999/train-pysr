#!/usr/bin/env python3
"""Shared PySR dial registry, panel validation, and preprocessing support.

This module contains no model-fitting entry point. Scientific interpretations
remain provisional, unverified, and pending thesis-author review.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


STATUS = "provisional, unverified, pending review"
BASE_FEATURES = ["mchi1", "mchipm1"]
FORBIDDEN_COLUMNS = {"Final_CLs"}
CLASSIFICATION_AVAILABILITY = {"supported", "deferred"}
CLASSIFICATION_SAFETY = {
    "safe",
    "unsafe",
    "requires_physics_review",
    "deferred",
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency failure is explicit.
        raise SystemExit("PyYAML is required.") from exc

    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


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
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return str(value)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_indices(indices: Iterable[Any]) -> str:
    text = "\n".join(str(int(value)) for value in indices)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at {key!r}")
    return value


def _validate_classification(option: dict[str, Any], path: str) -> None:
    availability = option.get("availability")
    safety = option.get("safety")
    if availability not in CLASSIFICATION_AVAILABILITY:
        raise ValueError(f"Invalid availability at {path}: {availability!r}")
    if safety not in CLASSIFICATION_SAFETY:
        raise ValueError(f"Invalid safety at {path}: {safety!r}")


def validate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != 1:
        raise ValueError("Switch registry schema_version must be 1")

    preprocessing = _require_mapping(registry, "preprocessing")
    execution = _require_mapping(registry, "execution")
    option_groups = [
        ("preprocessing.modes", _require_mapping(preprocessing, "modes")),
        ("preprocessing.feature_sets", _require_mapping(preprocessing, "feature_sets")),
        (
            "execution.binary_operator_presets",
            _require_mapping(execution, "binary_operator_presets"),
        ),
        (
            "execution.unary_operator_presets",
            _require_mapping(execution, "unary_operator_presets"),
        ),
        (
            "execution.custom_operator_presets",
            _require_mapping(execution, "custom_operator_presets"),
        ),
        (
            "execution.sample_weight_presets",
            _require_mapping(execution, "sample_weight_presets"),
        ),
        ("execution.loss_presets", _require_mapping(execution, "loss_presets")),
        ("execution.model_selection", _require_mapping(execution, "model_selection")),
        ("execution.complexity_dials", _require_mapping(execution, "complexity_dials")),
        ("execution.budget_dials", _require_mapping(execution, "budget_dials")),
        ("execution.precision", _require_mapping(execution, "precision")),
        ("execution.parallelism", _require_mapping(execution, "parallelism")),
        ("execution.deterministic", _require_mapping(execution, "deterministic")),
        ("execution.warm_start", _require_mapping(execution, "warm_start")),
        (
            "execution.output_policy_presets",
            _require_mapping(execution, "output_policy_presets"),
        ),
    ]
    option_count = 0
    for group_path, group in option_groups:
        if not group:
            raise ValueError(f"Registry group is empty: {group_path}")
        for name, option in group.items():
            if not isinstance(option, dict):
                raise ValueError(f"Expected option mapping: {group_path}.{name}")
            _validate_classification(option, f"{group_path}.{name}")
            option_count += 1

    for singleton in ["runtime_threads"]:
        option = _require_mapping(execution, singleton)
        _validate_classification(option, f"execution.{singleton}")
        option_count += 1

    modes = set(preprocessing["modes"])
    required_modes = {
        "raw",
        "standard",
        "robust",
        "dimensionless_reference",
        "log1p",
        "log_reference",
    }
    if not required_modes.issubset(modes):
        raise ValueError(f"Missing preprocessing modes: {sorted(required_modes - modes)}")

    unary_values: set[str] = set()
    for option in execution["unary_operator_presets"].values():
        unary_values.update(str(value) for value in option.get("operators", []))
    required_unary = {"log", "exp", "tanh", "sin", "cos", "inv", "sqrt", "tan", "coth"}
    if not required_unary.issubset(unary_values):
        raise ValueError(f"Missing unary candidates: {sorted(required_unary - unary_values)}")

    return {
        "registry_id": registry.get("registry_id"),
        "schema_version": registry["schema_version"],
        "classified_option_count": option_count,
        "status": STATUS,
    }


def _registry_option(
    group: dict[str, Any],
    choice: Any,
    path: str,
    acknowledgements: set[str],
) -> dict[str, Any]:
    key = str(choice).lower() if isinstance(choice, bool) else str(choice)
    option = group.get(key)
    if not isinstance(option, dict):
        raise ValueError(f"Unknown choice for {path}: {choice!r}")
    availability = option["availability"]
    safety = option["safety"]
    if availability == "deferred" or safety == "deferred":
        raise ValueError(f"Deferred choice is not executable: {path}.{key}")
    if safety == "unsafe":
        raise ValueError(f"Unsafe choice is blocked: {path}.{key}")
    acknowledgement_id = f"{path}.{key}"
    if safety == "requires_physics_review" and acknowledgement_id not in acknowledgements:
        raise ValueError(
            f"Choice requires explicit review acknowledgement {acknowledgement_id!r}"
        )
    return option


def _legacy_to_panel(config: dict[str, Any]) -> dict[str, Any]:
    """Translate preserved flat PySR configs into the v1 panel shape."""

    options = dict(config.get("pysr_options", {}))
    binary = list(options.get("binary_operators", ["+", "-", "*"]))
    binary_lookup = {
        ("+", "-"): "additive",
        ("+", "-", "*"): "polynomial",
        ("+", "-", "*", "/"): "rational",
        ("+", "-", "*", "^"): "power",
    }
    binary_preset = binary_lookup.get(tuple(binary))
    if binary_preset is None:
        raise ValueError(f"Legacy binary operator set has no registered preset: {binary}")
    unary = list(options.get("unary_operators", []))
    unary_lookup = {
        (): "none",
        ("tanh",): "tanh_only",
        ("log",): "log_only",
        ("exp",): "exp_only",
        ("log", "exp", "tanh"): "transcendental_candidates",
        ("sin", "cos"): "periodic_candidates",
        ("inv", "sqrt", "tan", "coth"): "singular_high_risk_candidates",
    }
    unary_preset = unary_lookup.get(tuple(unary))
    if unary_preset is None:
        raise ValueError(f"Legacy unary operator set has no registered preset: {unary}")

    runtime = config.get("runtime", {})
    output_dir = str(config.get("output_dir", ""))
    acknowledgements = []
    if binary_preset == "rational":
        acknowledgements.append("operators.binary.rational")

    return {
        "schema_version": 1,
        "registry": "configs/pysr/switch_registry.yaml",
        "run": {
            "run_id": config["run_id"],
            "task_type": config.get("task_type", "pysr_symbolic_score_search"),
            "review_status": config.get("review_status", "provisional"),
        },
        "dataset": {
            "dataset_id": config["dataset_id"],
            "dataset_config": config["dataset_config"],
            "raw_path": config["raw_path"],
            "target": config["target"],
            "positive_label": 1
            if config.get("positive_label") == "requires_review"
            else config.get("positive_label"),
            "forbidden_columns": ["Final_CLs"],
        },
        "split": {
            "method": config.get("split_method", "stratified"),
            "test_size": config.get("test_size", 0.2),
            "random_seed": config.get("random_seed", 42),
        },
        "preprocessing": {
            "feature_set": "base",
            "mode": "raw",
            "reference_scales": {"mchi1": 1000.0, "mchipm1": 1000.0},
            "review_acknowledgements": [],
        },
        "training": {
            "sample_weight_preset": "balanced",
            "manual_class_weights": None,
            "loss_preset": "weighted_squared_error",
        },
        "metrics": {
            "primary": "roc_auc",
            "secondary": "average_precision",
            "score_source": "continuous_pysr_prediction",
        },
        "operators": {
            "binary_preset": binary_preset,
            "unary_preset": unary_preset,
            "custom_preset": "none",
            "review_acknowledgements": acknowledgements,
        },
        "search": {
            "model_selection": options.get("model_selection", "best"),
            "review_acknowledgements": [],
            "complexity": {
                "maxsize": options.get("maxsize", 30),
                "maxdepth": options.get("maxdepth"),
                "parsimony": options.get("parsimony", 0.0),
                "complexity_of_operators": options.get("complexity_of_operators"),
                "constraints": options.get("constraints"),
                "nested_constraints": options.get("nested_constraints"),
            },
            "budget": {
                "niterations": options.get("niterations", 100),
                "populations": options.get("populations", 20),
                "population_size": options.get("population_size", 27),
                "timeout_in_seconds": options.get("timeout_in_seconds", 7200),
            },
            "precision": options.get("precision", 32),
            "deterministic": options.get("deterministic", True),
            "warm_start": options.get("warm_start", False),
        },
        "runtime": {
            "parallelism": options.get("parallelism", "serial"),
            "procs": options.get("procs"),
            "julia_threads": runtime.get("julia_num_threads", 1),
            "omp_threads": runtime.get("omp_num_threads", 1),
            "mkl_threads": runtime.get("mkl_num_threads", 1),
            "openblas_threads": runtime.get("openblas_num_threads", 1),
            "python_juliacall_handle_signals": runtime.get(
                "python_juliacall_handle_signals", "yes"
            ),
            "python_unbuffered": runtime.get("pythonunbuffered", True),
        },
        "output": {
            "output_dir": output_dir,
            "policy_preset": "cleaned_run_local"
            if options.get("delete_tempfiles", False)
            else "preserved_run_local",
            "require_clean_worktree": config.get("run_policy", {}).get(
                "require_clean_worktree", False
            ),
            "record_git_diff_status": config.get("run_policy", {}).get(
                "record_git_diff_status", True
            ),
        },
        "experiment": {
            "parent_config": None,
            "changed_dial": "legacy",
            "one_dial_policy": False,
        },
    }


def resolve_panel(
    raw_config: dict[str, Any],
    registry: dict[str, Any],
    *,
    config_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_registry(registry)
    panel = raw_config if raw_config.get("schema_version") == 1 else _legacy_to_panel(raw_config)

    run = _require_mapping(panel, "run")
    dataset = _require_mapping(panel, "dataset")
    split = _require_mapping(panel, "split")
    preprocessing = _require_mapping(panel, "preprocessing")
    training = _require_mapping(panel, "training")
    metrics = _require_mapping(panel, "metrics")
    operators = _require_mapping(panel, "operators")
    search = _require_mapping(panel, "search")
    runtime = _require_mapping(panel, "runtime")
    output = _require_mapping(panel, "output")

    if run.get("task_type") != "pysr_symbolic_score_search":
        raise ValueError("task_type must be pysr_symbolic_score_search")
    if dataset.get("dataset_id") != "masses_exclusions":
        raise ValueError("The v1 panel is bounded to dataset masses_exclusions")
    if dataset.get("target") != "exclusion":
        raise ValueError("The v1 target must be exclusion")
    if dataset.get("positive_label") != 1:
        raise ValueError("The authorized baseline positive label is 1")
    forbidden = set(dataset.get("forbidden_columns", []))
    if not FORBIDDEN_COLUMNS.issubset(forbidden):
        raise ValueError("Final_CLs must be explicitly forbidden")
    if split.get("method") != "stratified":
        raise ValueError("Only the authorized stratified split is supported")
    test_size = float(split.get("test_size"))
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1")

    preprocessing_registry = registry["preprocessing"]
    preprocessing_acks = set(preprocessing.get("review_acknowledgements", []))
    mode_name = str(preprocessing.get("mode"))
    feature_set_name = str(preprocessing.get("feature_set"))
    _registry_option(
        preprocessing_registry["modes"],
        mode_name,
        "preprocessing.mode",
        preprocessing_acks,
    )
    feature_option = _registry_option(
        preprocessing_registry["feature_sets"],
        feature_set_name,
        "preprocessing.feature_set",
        preprocessing_acks,
    )
    model_features = list(feature_option["columns"])
    if FORBIDDEN_COLUMNS.intersection(model_features + [dataset["target"]]):
        raise ValueError("Final_CLs must not be used as a feature or target")

    reference_scales = preprocessing.get("reference_scales", {})
    if not isinstance(reference_scales, dict):
        raise ValueError("preprocessing.reference_scales must be a mapping")
    if mode_name in {"dimensionless_reference", "log_reference"}:
        missing_scales = [name for name in model_features if name not in reference_scales]
        if missing_scales:
            raise ValueError(f"Missing reference scales for {missing_scales}")
        invalid_scales = [
            name
            for name in model_features
            if not math.isfinite(float(reference_scales[name]))
            or float(reference_scales[name]) <= 0.0
        ]
        if invalid_scales:
            raise ValueError(f"Reference scales must be finite and positive: {invalid_scales}")

    execution = registry["execution"]
    operator_acks = set(operators.get("review_acknowledgements", []))
    binary_name = str(operators.get("binary_preset"))
    unary_name = str(operators.get("unary_preset"))
    custom_name = str(operators.get("custom_preset"))
    binary_option = _registry_option(
        execution["binary_operator_presets"],
        binary_name,
        "operators.binary",
        operator_acks,
    )
    unary_option = _registry_option(
        execution["unary_operator_presets"],
        unary_name,
        "operators.unary",
        operator_acks,
    )
    custom_option = _registry_option(
        execution["custom_operator_presets"],
        custom_name,
        "operators.custom",
        operator_acks,
    )

    sample_weight_name = str(training.get("sample_weight_preset"))
    loss_name = str(training.get("loss_preset"))
    training_acks = set(training.get("review_acknowledgements", []))
    weight_option = _registry_option(
        execution["sample_weight_presets"],
        sample_weight_name,
        "training.sample_weight",
        training_acks,
    )
    loss_option = _registry_option(
        execution["loss_presets"], loss_name, "training.loss", training_acks
    )
    has_weights = sample_weight_name != "none"
    if bool(loss_option.get("requires_sample_weights")) != has_weights:
        raise ValueError(
            f"Loss {loss_name!r} and sample weight preset {sample_weight_name!r} are incompatible"
        )
    manual_class_weights = training.get("manual_class_weights")
    if sample_weight_name == "manual_class_weights":
        if not isinstance(manual_class_weights, dict) or set(manual_class_weights) != {0, 1}:
            raise ValueError("manual_class_weights must map integer labels 0 and 1")
        invalid_weights = [
            label
            for label, value in manual_class_weights.items()
            if not math.isfinite(float(value)) or float(value) <= 0.0
        ]
        if invalid_weights:
            raise ValueError(
                "Manual class weights must be finite and positive for labels "
                f"{sorted(invalid_weights)}"
            )

    if metrics != {
        "primary": "roc_auc",
        "secondary": "average_precision",
        "score_source": "continuous_pysr_prediction",
    }:
        raise ValueError("Metrics must be ROC-AUC primary, average precision secondary, continuous scores")

    model_selection = str(search.get("model_selection"))
    _registry_option(
        execution["model_selection"], model_selection, "search.model_selection", set()
    )
    complexity = _require_mapping(search, "complexity")
    budget = _require_mapping(search, "budget")
    search_acks = set(search.get("review_acknowledgements", []))
    for name, dial_registry in execution["complexity_dials"].items():
        value = complexity.get(name)
        if value is not None:
            _registry_option(
                execution["complexity_dials"],
                name,
                "search.complexity",
                search_acks,
            )
            if "minimum" in dial_registry and float(value) < float(
                dial_registry["minimum"]
            ):
                raise ValueError(f"search.complexity.{name} is below its minimum")
    for name, dial_registry in execution["budget_dials"].items():
        value = budget.get(name)
        if value is None or float(value) < float(dial_registry["minimum"]):
            raise ValueError(f"search.budget.{name} is missing or below its minimum")

    precision = int(search.get("precision"))
    _registry_option(execution["precision"], precision, "search.precision", set())
    deterministic = bool(search.get("deterministic"))
    _registry_option(
        execution["deterministic"], deterministic, "search.deterministic", set()
    )
    warm_start = bool(search.get("warm_start"))
    _registry_option(execution["warm_start"], warm_start, "search.warm_start", set())
    parallelism = str(runtime.get("parallelism"))
    _registry_option(execution["parallelism"], parallelism, "runtime.parallelism", set())
    if deterministic and parallelism != "serial":
        raise ValueError("deterministic=true requires runtime.parallelism=serial")
    julia_threads = int(runtime.get("julia_threads"))
    if julia_threads < int(execution["runtime_threads"]["minimum"]):
        raise ValueError("runtime.julia_threads is below its minimum")
    if runtime.get("python_juliacall_handle_signals") != "yes":
        raise ValueError('runtime.python_juliacall_handle_signals must be "yes"')

    output_policy_name = str(output.get("policy_preset"))
    output_policy = _registry_option(
        execution["output_policy_presets"],
        output_policy_name,
        "output.policy",
        set(),
    )
    output_settings = output_policy.get("settings")
    if not isinstance(output_settings, dict):
        raise ValueError(f"Output policy {output_policy_name!r} has no executable settings")
    if not str(output.get("output_dir", "")).strip():
        raise ValueError("output.output_dir must be set")
    output_path = Path(str(output["output_dir"]))
    if output_path.is_absolute() or ".." in output_path.parts:
        raise ValueError("output.output_dir must be a non-traversing repository-relative path")
    if output_path.parts[:2] != ("outputs", "runs") or len(output_path.parts) < 3:
        raise ValueError("output.output_dir must be a named run directory under outputs/runs/")
    resolved_output = dict(output)
    resolved_output.update(output_settings)
    if resolved_output.get("allow_overwrite") is not False:
        raise ValueError("Resolved output policy must forbid overwrite")
    if resolved_output.get("temp_equation_file") is not False:
        raise ValueError("Resolved output policy must set temp_equation_file=false")

    pysr_options = {
        "niterations": int(budget["niterations"]),
        "maxsize": int(complexity["maxsize"]),
        "maxdepth": None if complexity.get("maxdepth") is None else int(complexity["maxdepth"]),
        "populations": int(budget["populations"]),
        "population_size": int(budget["population_size"]),
        "parsimony": float(complexity["parsimony"]),
        "timeout_in_seconds": float(budget["timeout_in_seconds"]),
        "parallelism": parallelism,
        "procs": runtime.get("procs"),
        "precision": precision,
        "deterministic": deterministic,
        "warm_start": warm_start,
        "temp_equation_file": bool(resolved_output["temp_equation_file"]),
        "delete_tempfiles": bool(resolved_output["delete_tempfiles"]),
        "model_selection": model_selection,
        "elementwise_loss": loss_option["elementwise_loss"],
        "binary_operators": list(binary_option.get("operators", []))
        + list(custom_option.get("binary_definitions", [])),
        "unary_operators": list(unary_option.get("operators", []))
        + list(custom_option.get("unary_definitions", [])),
        "complexity_of_operators": complexity.get("complexity_of_operators"),
        "constraints": complexity.get("constraints"),
        "nested_constraints": complexity.get("nested_constraints"),
    }

    resolved = {
        "schema_version": 1,
        "config_path": str(config_path) if config_path else None,
        "registry_path": panel.get("registry", "configs/pysr/switch_registry.yaml"),
        "run_id": str(run["run_id"]),
        "task_type": run["task_type"],
        "review_status": run.get("review_status"),
        "dataset_id": dataset["dataset_id"],
        "dataset_config": str(dataset["dataset_config"]),
        "raw_path": str(dataset["raw_path"]),
        "target": dataset["target"],
        "positive_label": dataset["positive_label"],
        "forbidden_columns": sorted(forbidden),
        "base_features": list(BASE_FEATURES),
        "model_features": model_features,
        "split_method": split["method"],
        "test_size": test_size,
        "random_seed": int(split["random_seed"]),
        "preprocessing": {
            "feature_set": feature_set_name,
            "mode": mode_name,
            "reference_scales": {
                str(key): float(value) for key, value in reference_scales.items()
            },
        },
        "sample_weight_preset": sample_weight_name,
        "manual_class_weights": manual_class_weights,
        "loss_preset": loss_name,
        "metrics": dict(metrics),
        "operator_presets": {
            "binary": binary_name,
            "unary": unary_name,
            "custom": custom_name,
        },
        "custom_sympy_mappings": list(custom_option.get("sympy_mappings", [])),
        "pysr_options": pysr_options,
        "runtime": dict(runtime),
        "output": resolved_output,
        "experiment": dict(panel.get("experiment", {})),
        "legacy_config_translated": raw_config.get("schema_version") != 1,
        "status": STATUS,
    }
    return panel, resolved


def load_and_resolve_config(config_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    raw_config = load_yaml(config_path)
    registry_path = Path(raw_config.get("registry", "configs/pysr/switch_registry.yaml"))
    registry = load_yaml(registry_path)
    panel, resolved = resolve_panel(raw_config, registry, config_path=config_path)
    validate_one_dial_policy(panel, config_path=config_path)
    return registry, panel, resolved


def split_rows(
    data: Any,
    *,
    target: str,
    positive_label: Any,
    test_size: float,
    random_seed: int,
) -> tuple[Any, Any, Any]:
    try:
        from sklearn.model_selection import train_test_split
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("scikit-learn is required.") from exc

    y = (data[target] == positive_label).astype(int)
    train_index, test_index = train_test_split(
        data.index,
        test_size=float(test_size),
        random_state=int(random_seed),
        stratify=y,
    )
    return train_index, test_index, y


def build_feature_frame(raw_rows: Any, feature_set: str) -> Any:
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("numpy and pandas are required.") from exc

    missing = [name for name in BASE_FEATURES if name not in raw_rows.columns]
    if missing:
        raise ValueError(f"Missing base feature columns: {missing}")
    base = raw_rows[BASE_FEATURES].astype(float).copy()
    if not np.isfinite(base.to_numpy()).all():
        raise ValueError("Base feature values contain non-finite values")
    if (base["mchi1"] == 0.0).any() and feature_set in {
        "base_plus_ratio",
        "ratio_only",
        "gap_plus_ratio",
    }:
        raise ValueError("mass_ratio is undefined because mchi1 contains zero")

    gap = base["mchipm1"] - base["mchi1"]
    ratio = base["mchipm1"] / base["mchi1"]
    feature_frames = {
        "base": base,
        "base_plus_gap": base.assign(mass_gap=gap),
        "base_plus_ratio": base.assign(mass_ratio=ratio),
        "gap_only": pd.DataFrame({"mass_gap": gap}, index=base.index),
        "ratio_only": pd.DataFrame({"mass_ratio": ratio}, index=base.index),
        "gap_plus_ratio": pd.DataFrame(
            {"mass_gap": gap, "mass_ratio": ratio}, index=base.index
        ),
    }
    if feature_set not in feature_frames:
        raise ValueError(f"Unknown feature set: {feature_set}")
    result = feature_frames[feature_set]
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError(f"Feature set {feature_set} produced non-finite values")
    return result


def fit_transform_preprocessor(
    x_train: Any,
    x_test: Any,
    *,
    mode: str,
    reference_scales: dict[str, float] | None = None,
) -> tuple[Any, Any, dict[str, Any]]:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("numpy is required.") from exc

    if list(x_train.columns) != list(x_test.columns):
        raise ValueError("Training and test feature columns differ")
    if not np.isfinite(x_train.to_numpy(dtype=float)).all():
        raise ValueError("Training features contain non-finite values")
    if not np.isfinite(x_test.to_numpy(dtype=float)).all():
        raise ValueError("Test features contain non-finite values")

    columns = list(x_train.columns)
    parameters: dict[str, Any] = {}
    formulas: dict[str, str] = {}
    reference_scales = reference_scales or {}

    if mode == "raw":
        train_out = x_train.astype(float).copy()
        test_out = x_test.astype(float).copy()
        formulas = {name: name for name in columns}
    elif mode == "standard":
        means = x_train.mean(axis=0)
        scales = x_train.std(axis=0, ddof=0)
        zero_scale = [name for name in columns if float(scales[name]) == 0.0]
        if zero_scale:
            raise ValueError(f"Standard scaling has zero training scale: {zero_scale}")
        train_out = (x_train - means) / scales
        test_out = (x_test - means) / scales
        parameters = {
            "mean": {name: float(means[name]) for name in columns},
            "scale": {name: float(scales[name]) for name in columns},
        }
        formulas = {name: f"({name} - train_mean[{name}]) / train_std[{name}]" for name in columns}
    elif mode == "robust":
        medians = x_train.median(axis=0)
        q25 = x_train.quantile(0.25, axis=0)
        q75 = x_train.quantile(0.75, axis=0)
        scales = q75 - q25
        zero_scale = [name for name in columns if float(scales[name]) == 0.0]
        if zero_scale:
            raise ValueError(f"Robust scaling has zero training IQR: {zero_scale}")
        train_out = (x_train - medians) / scales
        test_out = (x_test - medians) / scales
        parameters = {
            "median": {name: float(medians[name]) for name in columns},
            "q25": {name: float(q25[name]) for name in columns},
            "q75": {name: float(q75[name]) for name in columns},
            "iqr": {name: float(scales[name]) for name in columns},
        }
        formulas = {name: f"({name} - train_median[{name}]) / train_iqr[{name}]" for name in columns}
    elif mode in {"dimensionless_reference", "log_reference"}:
        missing = [name for name in columns if name not in reference_scales]
        if missing:
            raise ValueError(f"Missing reference scales: {missing}")
        refs = {name: float(reference_scales[name]) for name in columns}
        invalid = [name for name, value in refs.items() if value <= 0 or not math.isfinite(value)]
        if invalid:
            raise ValueError(f"Reference scales must be finite and positive: {invalid}")
        ref_series = x_train.iloc[0].copy()
        for name in columns:
            ref_series[name] = refs[name]
        if mode == "dimensionless_reference":
            train_out = x_train / ref_series
            test_out = x_test / ref_series
            formulas = {name: f"{name} / reference[{name}]" for name in columns}
        else:
            if (x_train <= 0).any().any() or (x_test <= 0).any().any():
                raise ValueError("log_reference requires strictly positive inputs")
            train_out = np.log(x_train / ref_series)
            test_out = np.log(x_test / ref_series)
            formulas = {name: f"log({name} / reference[{name}])" for name in columns}
        parameters = {"reference_scales": refs}
    elif mode == "log1p":
        if (x_train < 0).any().any() or (x_test < 0).any().any():
            raise ValueError("log1p requires non-negative inputs")
        train_out = np.log1p(x_train)
        test_out = np.log1p(x_test)
        formulas = {name: f"log(1 + {name})" for name in columns}
    else:
        raise ValueError(f"Unknown preprocessing mode: {mode}")

    if not np.isfinite(train_out.to_numpy(dtype=float)).all():
        raise ValueError(f"Preprocessing mode {mode} produced non-finite training values")
    if not np.isfinite(test_out.to_numpy(dtype=float)).all():
        raise ValueError(f"Preprocessing mode {mode} produced non-finite test values")

    metadata = {
        "status": STATUS,
        "mode": mode,
        "fit_scope": "training_rows_only" if mode in {"standard", "robust"} else "no_test_fit",
        "columns": columns,
        "parameters": parameters,
        "formulas": formulas,
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "train_index_sha256": hash_indices(x_train.index),
        "test_index_sha256": hash_indices(x_test.index),
        "non_finite_policy": "reject",
    }
    return train_out, test_out, metadata


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(item, path))
        return result
    return {prefix: value}


def one_dial_changes(parent: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    ignored = {
        "run.run_id",
        "output.output_dir",
        "experiment.parent_config",
        "experiment.changed_dial",
        "experiment.one_dial_policy",
        "preprocessing.review_acknowledgements",
        "operators.review_acknowledgements",
        "training.review_acknowledgements",
        "search.review_acknowledgements",
    }
    parent_flat = _flatten(parent)
    candidate_flat = _flatten(candidate)
    paths = sorted(set(parent_flat) | set(candidate_flat))
    return [
        path
        for path in paths
        if path not in ignored and parent_flat.get(path) != candidate_flat.get(path)
    ]


def validate_one_dial_policy(panel: dict[str, Any], *, config_path: Path) -> None:
    experiment = panel.get("experiment", {})
    if not isinstance(experiment, dict) or not experiment.get("one_dial_policy"):
        return
    parent_path_value = experiment.get("parent_config")
    if parent_path_value is None:
        if experiment.get("changed_dial") != "baseline":
            raise ValueError("A parentless one-dial config must identify changed_dial: baseline")
        return
    parent_path = Path(str(parent_path_value))
    if not parent_path.exists():
        raise ValueError(f"Parent config does not exist: {parent_path}")
    parent = load_yaml(parent_path)
    changes = one_dial_changes(parent, panel)
    if len(changes) != 1:
        raise ValueError(f"One-dial policy expected one changed setting, observed {changes}")
    if experiment.get("changed_dial") != changes[0]:
        raise ValueError(
            f"experiment.changed_dial must be {changes[0]!r}, got {experiment.get('changed_dial')!r}"
        )
