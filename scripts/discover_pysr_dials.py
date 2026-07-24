#!/usr/bin/env python3
"""Run no-fit PySR dial, preprocessing, and operator discovery.

This command performs configuration, domain, leakage, and installed-environment
checks. It deliberately contains no call to PySRRegressor.fit.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pysr_dials import (
    STATUS,
    build_feature_frame,
    fit_transform_preprocessor,
    load_and_resolve_config,
    load_yaml,
    sha256,
    split_rows,
    to_jsonable,
    validate_registry,
    write_json,
)


FIT_CALL_COUNT = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No-fit PySR dial discovery.")
    parser.add_argument(
        "--config",
        default="configs/runs/masses_exclusions_pysr_baseline_v1.yaml",
        help="Human-editable baseline panel.",
    )
    parser.add_argument(
        "--report-dir",
        default="reports/pysr_dial_discovery",
        help="Tracked discovery report directory.",
    )
    parser.add_argument(
        "--live-operator-check",
        action="store_true",
        help="Initialize the installed offline Julia environment and compile/evaluate operators.",
    )
    parser.add_argument(
        "--desktop-doc",
        help="Optional second path for a byte-identical generated baseline Markdown document.",
    )
    return parser.parse_args()


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def probe_reference_scales(columns: list[str], probe: str) -> dict[str, float]:
    if probe == "one_input_unit":
        return {name: 1.0 for name in columns}
    if probe == "mass_1000_ratio_1":
        return {name: 1.0 if "ratio" in name else 1000.0 for name in columns}
    raise ValueError(f"Unknown reference-scale probe: {probe}")


def frame_summary(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "minimum": {name: float(frame[name].min()) for name in frame.columns},
        "maximum": {name: float(frame[name].max()) for name in frame.columns},
        "finite": bool(np.isfinite(frame.to_numpy(dtype=float)).all()),
    }


def discover_preprocessing(
    data: pd.DataFrame,
    registry: dict[str, Any],
    resolved: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    train_index, test_index, y = split_rows(
        data,
        target=resolved["target"],
        positive_label=resolved["positive_label"],
        test_size=resolved["test_size"],
        random_seed=resolved["random_seed"],
    )
    split_record = {
        "method": resolved["split_method"],
        "test_size": resolved["test_size"],
        "random_seed": resolved["random_seed"],
        "split_before_preprocessing": True,
        "train_rows": int(len(train_index)),
        "test_rows": int(len(test_index)),
        "train_class_counts": {
            str(key): int(value)
            for key, value in y.loc[train_index].value_counts().sort_index().items()
        },
        "test_class_counts": {
            str(key): int(value)
            for key, value in y.loc[test_index].value_counts().sort_index().items()
        },
    }

    modes = registry["preprocessing"]["modes"]
    feature_sets = registry["preprocessing"]["feature_sets"]
    results: list[dict[str, Any]] = []
    leakage_results: list[dict[str, Any]] = []

    raw_train = data.loc[train_index]
    raw_test = data.loc[test_index]
    perturbed_test = raw_test.copy()
    for name in ["mchi1", "mchipm1"]:
        perturbed_test[name] = perturbed_test[name].astype(float) * 10.0 + 12345.0

    for feature_set_name, feature_option in feature_sets.items():
        x_train = build_feature_frame(raw_train, feature_set_name)
        x_test = build_feature_frame(raw_test, feature_set_name)
        x_test_perturbed = build_feature_frame(perturbed_test, feature_set_name)
        for mode_name, mode_option in modes.items():
            probes = (
                ["one_input_unit", "mass_1000_ratio_1"]
                if mode_name in {"dimensionless_reference", "log_reference"}
                else ["not_applicable"]
            )
            for probe in probes:
                references = (
                    probe_reference_scales(list(x_train.columns), probe)
                    if probe != "not_applicable"
                    else {}
                )
                record: dict[str, Any] = {
                    "feature_set": feature_set_name,
                    "preprocessing_mode": mode_name,
                    "reference_probe": probe,
                    "availability": mode_option["availability"],
                    "mode_safety": mode_option["safety"],
                    "feature_set_safety": feature_option["safety"],
                    "status": "pending",
                }
                leakage_record = dict(record)
                try:
                    train_out, test_out, fitted = fit_transform_preprocessor(
                        x_train,
                        x_test,
                        mode=mode_name,
                        reference_scales=references,
                    )
                    _, perturbed_out, fitted_after_test_change = fit_transform_preprocessor(
                        x_train,
                        x_test_perturbed,
                        mode=mode_name,
                        reference_scales=references,
                    )
                    parameters_unchanged = (
                        fitted["parameters"] == fitted_after_test_change["parameters"]
                    )
                    training_identity_unchanged = (
                        fitted["train_index_sha256"]
                        == fitted_after_test_change["train_index_sha256"]
                    )
                    record.update(
                        {
                            "status": "passed",
                            "reference_scales": references,
                            "training": frame_summary(train_out),
                            "test": frame_summary(test_out),
                            "transformation_metadata": fitted,
                        }
                    )
                    leakage_record.update(
                        {
                            "status": "passed"
                            if parameters_unchanged and training_identity_unchanged
                            else "failed",
                            "parameters_unchanged_after_test_only_perturbation": parameters_unchanged,
                            "training_identity_unchanged": training_identity_unchanged,
                            "perturbed_test_remained_finite": bool(
                                np.isfinite(perturbed_out.to_numpy(dtype=float)).all()
                            ),
                        }
                    )
                except Exception as exc:  # noqa: BLE001 - discovery records exact failure.
                    record.update(
                        {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
                    )
                    leakage_record.update(
                        {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
                    )
                results.append(record)
                leakage_results.append(leakage_record)

    x_train_base = build_feature_frame(raw_train, "base")
    x_test_base = build_feature_frame(raw_test, "base")
    x_test_nonfinite = x_test_base.copy()
    x_test_nonfinite.iloc[0, 0] = np.inf
    nonfinite_rejection: dict[str, bool] = {}
    for mode_name in modes:
        references = probe_reference_scales(list(x_train_base.columns), "mass_1000_ratio_1")
        try:
            fit_transform_preprocessor(
                x_train_base,
                x_test_nonfinite,
                mode=mode_name,
                reference_scales=references,
            )
        except ValueError:
            nonfinite_rejection[mode_name] = True
        else:
            nonfinite_rejection[mode_name] = False

    preprocessing_payload = {
        "status": STATUS,
        "fit_call_count": FIT_CALL_COUNT,
        "split": split_record,
        "dataset_domain": {
            "base_training": frame_summary(x_train_base),
            "base_test": frame_summary(x_test_base),
        },
        "nonfinite_rejection": nonfinite_rejection,
        "results": results,
        "passed": all(item["status"] == "passed" for item in results)
        and all(nonfinite_rejection.values()),
    }
    leakage_payload = {
        "status": STATUS,
        "method": "Perturb test rows only, refit preprocessing on unchanged training rows, compare frozen metadata.",
        "results": leakage_results,
        "passed": all(item["status"] == "passed" for item in leakage_results),
    }
    return preprocessing_payload, leakage_payload


UNARY_NUMPY = {
    "log": np.log,
    "exp": np.exp,
    "tanh": np.tanh,
    "sin": np.sin,
    "cos": np.cos,
    "inv": lambda x: 1.0 / x,
    "sqrt": np.sqrt,
    "tan": np.tan,
    "coth": lambda x: 1.0 / np.tanh(x),
    "square": lambda x: x * x,
}

BINARY_NUMPY = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "^": lambda x, y: np.power(x, y),
    "guarded_div": lambda x, y: x / (np.abs(y) + 1.0e-12),
}


def numpy_operator_probe() -> dict[str, Any]:
    unary_values = np.asarray(
        [-2.0, -1.0e-12, 0.0, 1.0e-12, 0.5, 1.0, 10.0, 100.0, 1000.0, 1981.43446],
        dtype=float,
    )
    left = np.asarray([-2.0, -1.0, 0.0, 1.0e-12, 1.0, 10.0, 1000.0], dtype=float)
    right = np.asarray([0.5, 0.0, 0.0, 1.0e-12, -1.0, 2.0, 1000.0], dtype=float)
    unary_results = {}
    binary_results = {}
    with np.errstate(all="ignore"):
        for name, operation in UNARY_NUMPY.items():
            values = np.asarray(operation(unary_values), dtype=float)
            mask = np.isfinite(values)
            unary_results[name] = {
                "probe_count": int(len(values)),
                "finite_count": int(mask.sum()),
                "all_finite": bool(mask.all()),
                "nonfinite_input_values": unary_values[~mask].tolist(),
            }
        for name, operation in BINARY_NUMPY.items():
            values = np.asarray(operation(left, right), dtype=float)
            mask = np.isfinite(values)
            binary_results[name] = {
                "probe_count": int(len(values)),
                "finite_count": int(mask.sum()),
                "all_finite": bool(mask.all()),
                "nonfinite_pairs": [
                    [float(x), float(y)] for x, y in zip(left[~mask], right[~mask])
                ],
            }
    return {
        "synthetic_unary_inputs": unary_values.tolist(),
        "synthetic_binary_left": left.tolist(),
        "synthetic_binary_right": right.tolist(),
        "unary": unary_results,
        "binary": binary_results,
    }


JULIA_UNARY_EXPRESSIONS = {
    "log": "log(x)",
    "exp": "exp(x)",
    "tanh": "tanh(x)",
    "sin": "sin(x)",
    "cos": "cos(x)",
    "inv": "inv(x)",
    "sqrt": "sqrt(x)",
    "tan": "tan(x)",
    "coth": "coth(x)",
    "square": "x * x",
}

JULIA_BINARY_EXPRESSIONS = {
    "+": "x + y",
    "-": "x - y",
    "*": "x * y",
    "/": "x / y",
    "^": "x ^ y",
    "guarded_div": "x / (abs(y) + 1.0e-12)",
}


def live_operator_probe(requested_threads: int) -> dict[str, Any]:
    os.environ["JULIA_PKG_OFFLINE"] = "true"
    os.environ["JULIA_NUM_THREADS"] = str(requested_threads)
    os.environ["PYTHON_JULIACALL_THREADS"] = str(requested_threads)
    os.environ["PYTHON_JULIACALL_HANDLE_SIGNALS"] = "yes"

    from pysr import PySRRegressor
    from juliacall import Main as jl

    jl.seval("using Pkg")
    jl.seval("using SymbolicRegression")
    unary_values = "[-2.0, -1.0e-12, 0.0, 1.0e-12, 0.5, 1.0, 10.0, 100.0, 1000.0, 1981.43446]"
    binary_left = "[-2.0, -1.0, 0.0, 1.0e-12, 1.0, 10.0, 1000.0]"
    binary_right = "[0.5, 0.0, 0.0, 1.0e-12, -1.0, 2.0, 1000.0]"
    unary = {}
    binary = {}
    for name, expression in JULIA_UNARY_EXPRESSIONS.items():
        code = (
            "let values = "
            + unary_values
            + f", f = x -> {expression}; "
            + "map(x -> try y = f(x); isfinite(y) catch; false end, values) end"
        )
        try:
            finite = [bool(value) for value in jl.seval(code)]
            unary[name] = {
                "compiled": True,
                "finite_count": int(sum(finite)),
                "probe_count": len(finite),
                "all_finite": all(finite),
            }
        except Exception as exc:  # noqa: BLE001
            unary[name] = {"compiled": False, "error": f"{type(exc).__name__}: {exc}"}
    for name, expression in JULIA_BINARY_EXPRESSIONS.items():
        code = (
            "let left = "
            + binary_left
            + ", right = "
            + binary_right
            + f", f = (x, y) -> {expression}; "
            + "map((x, y) -> try z = f(x, y); isfinite(z) catch; false end, left, right) end"
        )
        try:
            finite = [bool(value) for value in jl.seval(code)]
            binary[name] = {
                "compiled": True,
                "finite_count": int(sum(finite)),
                "probe_count": len(finite),
                "all_finite": all(finite),
            }
        except Exception as exc:  # noqa: BLE001
            binary[name] = {"compiled": False, "error": f"{type(exc).__name__}: {exc}"}

    global FIT_CALL_COUNT
    original_fit = PySRRegressor.fit

    def prohibited_fit(*args: Any, **kwargs: Any) -> None:
        global FIT_CALL_COUNT
        FIT_CALL_COUNT += 1
        raise RuntimeError("Scientific fitting is prohibited during dial discovery")

    PySRRegressor.fit = prohibited_fit
    try:
        signature = inspect.signature(PySRRegressor)
        parameters = sorted(signature.parameters)
    finally:
        PySRRegressor.fit = original_fit

    required_constructor_dials = {
        "binary_operators",
        "unary_operators",
        "elementwise_loss",
        "model_selection",
        "maxsize",
        "maxdepth",
        "parsimony",
        "complexity_of_operators",
        "constraints",
        "nested_constraints",
        "niterations",
        "populations",
        "population_size",
        "timeout_in_seconds",
        "precision",
        "parallelism",
        "procs",
        "random_state",
        "deterministic",
        "warm_start",
        "output_directory",
        "temp_equation_file",
        "tempdir",
        "delete_tempfiles",
        "run_id",
    }
    return {
        "initialized": True,
        "offline": True,
        "julia_version": str(jl.seval("string(VERSION)")),
        "symbolic_regression_version": str(
            jl.seval(
                'string(Pkg.dependencies()[Base.UUID("8254be44-1295-4e6a-a16d-46603ac705cb")].version)'
            )
        ),
        "requested_threads": requested_threads,
        "observed_threads": int(jl.seval("Threads.nthreads()")),
        "unary": unary,
        "binary": binary,
        "pysr_constructor_parameters": parameters,
        "required_constructor_dials_present": sorted(required_constructor_dials.intersection(parameters)),
        "missing_constructor_dials": sorted(required_constructor_dials.difference(parameters)),
        "fit_call_count": FIT_CALL_COUNT,
    }


def _operator_names(registry: dict[str, Any], *, safe_only: bool) -> dict[str, set[str]]:
    execution = registry["execution"]
    names = {"unary": set(), "binary": set()}
    for kind, group_name in [
        ("unary", "unary_operator_presets"),
        ("binary", "binary_operator_presets"),
    ]:
        for option in execution[group_name].values():
            if safe_only and not (
                option["availability"] == "supported" and option["safety"] == "safe"
            ):
                continue
            names[kind].update(str(value) for value in option.get("operators", []))

    for option in execution["custom_operator_presets"].values():
        if safe_only and not (
            option["availability"] == "supported" and option["safety"] == "safe"
        ):
            continue
        for kind, field in [
            ("unary", "unary_definitions"),
            ("binary", "binary_definitions"),
        ]:
            for definition in option.get(field, []):
                names[kind].add(str(definition).split("(", 1)[0].strip())
    return names


def evaluate_operator_discovery(
    registry: dict[str, Any],
    *,
    fit_call_count: int,
    live: dict[str, Any],
    live_requested: bool,
) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "live_requested": live_requested,
        "fit_call_count_zero": fit_call_count == 0,
        "live_initialized": None,
        "constructor_dials_complete": None,
        "threads_match": None,
        "missing_operator_probes": [],
        "failed_compilations": [],
        "safe_domain_failures": [],
    }
    if not live_requested:
        checks["passed"] = checks["fit_call_count_zero"]
        return checks

    checks["live_initialized"] = live.get("initialized") is True
    checks["constructor_dials_complete"] = (
        live.get("missing_constructor_dials") == []
    )
    requested_threads = live.get("requested_threads")
    observed_threads = live.get("observed_threads")
    checks["threads_match"] = (
        isinstance(requested_threads, int)
        and isinstance(observed_threads, int)
        and observed_threads == requested_threads
    )

    all_names = _operator_names(registry, safe_only=False)
    safe_names = _operator_names(registry, safe_only=True)
    for kind in ["unary", "binary"]:
        records = live.get(kind)
        if not isinstance(records, dict):
            records = {}
        for name in sorted(all_names[kind]):
            record = records.get(name)
            if not isinstance(record, dict):
                checks["missing_operator_probes"].append(f"{kind}.{name}")
            elif record.get("compiled") is not True:
                checks["failed_compilations"].append(f"{kind}.{name}")
        for name in sorted(safe_names[kind]):
            record = records.get(name)
            if not isinstance(record, dict) or record.get("all_finite") is not True:
                checks["safe_domain_failures"].append(f"{kind}.{name}")

    checks["passed"] = all(
        [
            checks["fit_call_count_zero"],
            checks["live_initialized"],
            checks["constructor_dials_complete"],
            checks["threads_match"],
            not checks["missing_operator_probes"],
            not checks["failed_compilations"],
            not checks["safe_domain_failures"],
        ]
    )
    return checks


def registry_rows(registry: dict[str, Any]) -> list[dict[str, Any]]:
    preprocessing = registry["preprocessing"]
    execution = registry["execution"]
    groups = [
        ("preprocessing.mode", preprocessing["modes"]),
        ("preprocessing.feature_set", preprocessing["feature_sets"]),
        ("operators.binary", execution["binary_operator_presets"]),
        ("operators.unary", execution["unary_operator_presets"]),
        ("operators.custom", execution["custom_operator_presets"]),
        ("training.sample_weight", execution["sample_weight_presets"]),
        ("training.loss", execution["loss_presets"]),
        ("search.model_selection", execution["model_selection"]),
        ("search.complexity", execution["complexity_dials"]),
        ("search.budget", execution["budget_dials"]),
        ("search.precision", execution["precision"]),
        ("runtime.parallelism", execution["parallelism"]),
        ("search.deterministic", execution["deterministic"]),
        ("search.warm_start", execution["warm_start"]),
        ("output.policy", execution["output_policy_presets"]),
    ]
    rows = []
    for group_name, options in groups:
        for name, option in options.items():
            values = option.get("operators")
            if values is None:
                values = option.get("columns")
            rows.append(
                {
                    "group": group_name,
                    "option": str(name),
                    "availability": option["availability"],
                    "safety": option["safety"],
                    "default": option.get("default", False),
                    "values": values,
                    "note": option.get("risk")
                    or option.get("reason")
                    or option.get("description", ""),
                }
            )
    for name in ["runtime_threads"]:
        option = execution[name]
        rows.append(
            {
                "group": "runtime",
                "option": name,
                "availability": option["availability"],
                "safety": option["safety"],
                "default": option.get("default", False),
                "values": None,
                "note": option.get("reason", ""),
            }
        )
    return rows


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Group | Option | Availability | Safety | Default | Values / note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        values = row["values"]
        detail = ", ".join(str(value) for value in values) if isinstance(values, list) else ""
        if row["note"]:
            detail = f"{detail}; {row['note']}" if detail else str(row["note"])
        detail = detail.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{row['group']}` | `{row['option']}` | {row['availability']} | "
            f"{row['safety']} | {row['default']} | {detail} |"
        )
    return "\n".join(lines)


def render_dial_sheet(
    registry: dict[str, Any],
    resolved: dict[str, Any],
    preprocessing: dict[str, Any],
    leakage: dict[str, Any],
    operator_results: dict[str, Any],
) -> str:
    rows = registry_rows(registry)
    passed_preprocessing = sum(
        item["status"] == "passed" for item in preprocessing["results"]
    )
    total_preprocessing = len(preprocessing["results"])
    return f"""# PySR Dial Discovery Sheet

Status: **{STATUS}**

## Boundary

This is a no-fit discovery record. It performs preprocessing, domain,
configuration, and installed-environment checks only. Fit calls observed:
`{operator_results['fit_call_count']}`.

## Repository Baseline

- Dataset: `{resolved['dataset_id']}`
- Target: `{resolved['target']}` with positive label `{resolved['positive_label']}`
- Baseline features: `{', '.join(resolved['model_features'])}`
- Excluded field: `Final_CLs`
- Split: stratified `{int((1.0 - resolved['test_size']) * 100)}/{int(resolved['test_size'] * 100)}`, seed `{resolved['random_seed']}`
- Primary metric: ROC-AUC from continuous scores
- Secondary metric: average precision from continuous scores

## Discovery Results

- Preprocessing/domain cases passed: {passed_preprocessing}/{total_preprocessing}
- Leakage cases passed: {sum(item['status'] == 'passed' for item in leakage['results'])}/{len(leakage['results'])}
- All preprocessing modes rejected non-finite input: {all(preprocessing['nonfinite_rejection'].values())}
- Live Julia operator check: {operator_results['live']['initialized']}
- Requested/observed Julia threads: {operator_results['live'].get('requested_threads')} / {operator_results['live'].get('observed_threads')}

## Supported and Unsafe Option Table

{markdown_table(rows)}

## Recommended Next-Run Defaults

```yaml
{json.dumps(to_jsonable(registry['recommended_baseline']), indent=2)}
```

No unary operator is enabled by default. Derived features, periodic operators,
rational division, guarded division, and reference-based mass transforms remain
provisional and require explicit review. Unsafe and deferred choices are blocked.
"""


def render_baseline_document(
    registry: dict[str, Any],
    resolved: dict[str, Any],
    environment: dict[str, Any],
) -> str:
    options = resolved["pysr_options"]
    preprocessing_rows = []
    for name, option in registry["preprocessing"]["modes"].items():
        preprocessing_rows.append(
            f"| `{name}` | {option['availability']} | {option['safety']} | {option.get('description', '')} |"
        )
    rows = registry_rows(registry)
    return f"""# PySR Baseline Configuration

Status: **{STATUS}**

This document is a technical handoff for human review. It is not a scientific
acceptance, physics interpretation, or authorization to start a fit.

## Environment and Panel

- PySR: `{environment.get('pysr')}`
- SymbolicRegression.jl: `{environment.get('symbolic_regression')}`
- Julia: `{environment.get('julia')}`
- Editable panel: `configs/runs/masses_exclusions_pysr_baseline_v1.yaml`
- Switch registry: `configs/pysr/switch_registry.yaml`

Validate before Julia initialization:

```bash
python scripts/train_pysr_auc_search.py --config configs/runs/masses_exclusions_pysr_baseline_v1.yaml --dry-run
```

## Dataset, Target, Split, and Metrics

- Dataset id/path: `{resolved['dataset_id']}` / `{resolved['raw_path']}`
- Input features: `{', '.join(resolved['model_features'])}`
- Target and positive label: `{resolved['target']}` / `{resolved['positive_label']}`
- Forbidden field: `Final_CLs`
- Split: `{resolved['split_method']}`, test size `{resolved['test_size']}`, seed `{resolved['random_seed']}`
- Weighting: `{resolved['sample_weight_preset']}`, fitted/applied to training rows only
- Fit loss: `{options['elementwise_loss']}`
- Primary metric: ROC-AUC from saved continuous test scores
- Secondary metric: average precision from saved continuous test scores
- Integrity rule: recompute metrics independently from `pysr_test_scores.csv`; no reference model comparison

TODO: Confirm the physical meaning of labels 0 and 1 and the mass units with the thesis author/supervisor.

## Selected Preprocessing and Feature Policy

- Baseline feature set: `{resolved['preprocessing']['feature_set']}`
- Baseline preprocessing: `{resolved['preprocessing']['mode']}`
- Configured reference scales (inactive for raw mode): `{json.dumps(resolved['preprocessing']['reference_scales'], sort_keys=True)}`
- Every fitted transform splits first and fits only on training rows.
- Frozen transformation metadata is saved and non-finite values are rejected.
- Available derived sets: base, base plus gap, base plus ratio, gap only, ratio only, and gap plus ratio.
- Reference-scale probes use explicit values and are not physical scale claims.

| Mode | Availability | Safety | Meaning |
| --- | --- | --- | --- |
{chr(10).join(preprocessing_rows)}

## Operators and Search Budget

- Binary preset/operators: `{resolved['operator_presets']['binary']}` / `{', '.join(options['binary_operators'])}`
- Unary preset/operators: `{resolved['operator_presets']['unary']}` / `{', '.join(options['unary_operators']) or 'none'}`
- Custom preset: `{resolved['operator_presets']['custom']}`
- Model selection: `{options['model_selection']}`
- Maximum expression size/depth: `{options['maxsize']}` / `{options['maxdepth']}`
- Parsimony: `{options['parsimony']}`
- Iterations/populations/population size: `{options['niterations']}` / `{options['populations']}` / `{options['population_size']}`
- Timeout: `{options['timeout_in_seconds']}` seconds
- Precision: `{options['precision']}`

No unary operator is enabled by default.

## Runtime, Warm Start, and Output Policy

- Parallelism: `{options['parallelism']}`
- Deterministic: `{options['deterministic']}` with random seed `{resolved['random_seed']}`
- Julia/JuliaCall threads: `{resolved['runtime']['julia_threads']}`; the observed count must match
- OMP/MKL/OpenBLAS threads: `{resolved['runtime']['omp_threads']}` / `{resolved['runtime']['mkl_threads']}` / `{resolved['runtime']['openblas_threads']}`
- Warm start: `{options['warm_start']}`
- Run id: `{resolved['run_id']}`
- Non-overwriting output: `{resolved['output']['output_dir']}`
- Output policy preset: `{resolved['output']['policy_preset']}`
- Workspace/temp directories are run-local.
- `temp_equation_file=false`; `delete_tempfiles={str(options['delete_tempfiles']).lower()}`.

The discovery pass does not create the run output directory and does not call a fit.

## Complete Dial Table

{markdown_table(rows)}

## One-Dial Improvement Runs

Copy the baseline panel, assign a new run id and output directory, set
`experiment.parent_config` to the baseline or prior run config, and change one
registered dial. Validation ignores identity/output changes but rejects more
than one scientific/runtime dial change.

All future expressions, metrics, recommendations, and physics interpretations
remain provisional, unverified, and pending human review.
"""


def repository_context() -> dict[str, Any]:
    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"ERROR: {result.stderr.strip()}"
        return result.stdout.strip()

    implementation_surfaces = [
        "scripts/train_pysr_auc_search.py",
        "scripts/validate_pysr_run.py",
        "scripts/discover_pysr_dials.py",
        "scripts/pysr_dials.py",
        "configs/pysr/switch_registry.yaml",
        "configs/runs/masses_exclusions_pysr_baseline_v1.yaml",
    ]
    artifact_dirs = []
    runs_root = Path("outputs/runs")
    for run_dir in sorted(runs_root.glob("masses_exclusions_pysr_*")):
        if not run_dir.is_dir():
            continue
        files = [path for path in run_dir.rglob("*") if path.is_file()]
        historical_core = {
            "pysr_metrics.json",
            "pysr_test_scores.csv",
            "pysr_model.pkl",
            "pysr_environment.json",
        }
        artifact_dirs.append(
            {
                "path": str(run_dir),
                "file_count": len(files),
                "historical_core_complete": all(
                    (run_dir / filename).exists() for filename in historical_core
                ),
                "preservation_policy": "inspect_only_do_not_overwrite",
            }
        )
    status = git("status", "--short", "--untracked-files=all")
    return {
        "repository_root": git("rev-parse", "--show-toplevel"),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "status_short": status.splitlines() if status else [],
        "implementation_surfaces": implementation_surfaces,
        "implementation_sha256": {
            path: sha256(Path(path)) for path in implementation_surfaces
        },
        "pysr_artifact_directories": artifact_dirs,
        "external_historical_workspace_required": False,
        "external_historical_workspace_accessed": False,
    }


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    report_dir = Path(args.report_dir)
    registry, panel, resolved = load_and_resolve_config(config_path)
    registry_validation = validate_registry(registry)

    raw_path = Path(resolved["raw_path"])
    data = pd.read_csv(raw_path)
    required_columns = {"mchi1", "mchipm1", "Final_CLs", resolved["target"]}
    missing = sorted(required_columns - set(data.columns))
    if missing:
        raise SystemExit(f"Dataset is missing columns: {missing}")

    preprocessing, leakage = discover_preprocessing(data, registry, resolved)
    numpy_results = numpy_operator_probe()
    if args.live_operator_check:
        live = live_operator_probe(int(resolved["runtime"]["julia_threads"]))
    else:
        live = {
            "initialized": False,
            "reason": "--live-operator-check not requested",
            "fit_call_count": FIT_CALL_COUNT,
        }
    aggregate_checks = evaluate_operator_discovery(
        registry,
        fit_call_count=FIT_CALL_COUNT,
        live=live,
        live_requested=args.live_operator_check,
    )
    operator_results = {
        "status": STATUS,
        "fit_call_count": FIT_CALL_COUNT,
        "numpy_synthetic": numpy_results,
        "live": live,
        "aggregate_checks": aggregate_checks,
        "passed": aggregate_checks["passed"],
    }

    environment = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "pysr": package_version("pysr"),
        "juliacall": package_version("juliacall"),
        "numpy": package_version("numpy"),
        "pandas": package_version("pandas"),
        "scikit_learn": package_version("scikit-learn"),
        "julia": live.get("julia_version"),
        "symbolic_regression": live.get("symbolic_regression_version"),
    }
    context = {
        "status": STATUS,
        "no_fit": True,
        "fit_call_count": FIT_CALL_COUNT,
        "command": " ".join(sys.argv),
        "config": str(config_path),
        "config_sha256": sha256(config_path),
        "registry": resolved["registry_path"],
        "registry_validation": registry_validation,
        "dataset": str(raw_path),
        "dataset_sha256": sha256(raw_path),
        "environment": environment,
        "repository": repository_context(),
        "resolved_baseline": resolved,
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir / "discovery_context.json", context)
    write_json(report_dir / "switch_registry_snapshot.json", registry)
    write_json(report_dir / "preprocessing_safety_results.json", preprocessing)
    write_json(report_dir / "preprocessing_leakage_results.json", leakage)
    write_json(report_dir / "synthetic_domain_safety_results.json", operator_results)

    dial_sheet = render_dial_sheet(registry, resolved, preprocessing, leakage, operator_results)
    (report_dir / "dial_sheet.md").write_text(dial_sheet, encoding="utf-8")
    all_rows = registry_rows(registry)
    safe_rows = [
        row
        for row in all_rows
        if row["availability"] == "supported" and row["safety"] == "safe"
    ]
    unsafe_rows = [
        row
        for row in all_rows
        if row["safety"] in {"unsafe", "deferred", "requires_physics_review"}
        or row["availability"] == "deferred"
    ]
    supported_unsafe = (
        f"# Supported, Review-Gated, Unsafe, and Deferred PySR Options\n\nStatus: **{STATUS}**\n\n"
        + "## Supported and Safe\n\n"
        + markdown_table(safe_rows)
        + "\n\n## Review-Gated, Unsafe, or Deferred\n\n"
        + markdown_table(unsafe_rows)
        + "\n"
    )
    (report_dir / "supported_unsafe_options.md").write_text(
        supported_unsafe, encoding="utf-8"
    )
    baseline_document = render_baseline_document(registry, resolved, environment)
    canonical_document = report_dir / "PySR_BASELINE_CONFIGURATION.md"
    canonical_document.write_text(baseline_document, encoding="utf-8")
    if args.desktop_doc:
        desktop_path = Path(args.desktop_doc)
        desktop_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(canonical_document, desktop_path)

    failures = []
    if not preprocessing["passed"]:
        failures.append("preprocessing safety")
    if not leakage["passed"]:
        failures.append("preprocessing leakage")
    if not operator_results["passed"]:
        failures.append("operator/runtime discovery")
    if FIT_CALL_COUNT != 0:
        failures.append("no-fit guard")
    if failures:
        raise SystemExit(f"Discovery failed: {', '.join(failures)}")

    print(f"No-fit discovery passed; wrote reports to {report_dir}")
    print(f"Preprocessing cases: {len(preprocessing['results'])}")
    print(f"Leakage cases: {len(leakage['results'])}")
    print(f"Fit calls: {FIT_CALL_COUNT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
