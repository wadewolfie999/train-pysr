#!/usr/bin/env python3
"""Single isolated PySR search attempt for Act 5.

Metric outputs are written only under sealed/ and are never printed.
Non-metric status is written to status.json.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_status(path: Path, **fields: object) -> None:
    # Non-metric only. Never include AUC / predictions / expression rankings.
    allowed = {
        "attempt_id",
        "run_id",
        "arm",
        "outer_split_id",
        "seed_bundle_id",
        "stage",
        "configuration_id",
        "state",
        "started_utc",
        "ended_utc",
        "elapsed_seconds",
        "exit_status",
        "timed_out",
        "peak_rss_bytes",
        "infrastructure_retry_of",
        "error_class",
        "error_message",
        "artifact_completeness",
        "pid",
    }
    record = {k: v for k, v in fields.items() if k in allowed}
    dump_json(path, record)


def peak_rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    value = int(usage.ru_maxrss)
    return value if platform.system() == "Darwin" else value * 1024


def classify_exception(exc: BaseException, timed_out: bool) -> str:
    if timed_out:
        return "SAFETY_TIMEOUT"
    msg = f"{type(exc).__name__}: {exc}"
    lower = msg.lower()
    # Infrastructure-only classification MUST happen before metric access.
    # These are launch/backend/fs style failures.
    infra_markers = (
        "permissionerror",
        "filenotfounderror",
        "oserror",
        "brokenpipe",
        "juliapkg",
        "juliacall",
        "failed to initialize",
        "could not find julia",
        "backend initialization",
        "no such file",
        "disk quota",
        "input/output error",
    )
    if any(m in lower for m in infra_markers):
        return "INFRASTRUCTURE"
    return "SCIENTIFIC_OR_NUMERICAL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    args = parser.parse_args()

    attempt_dir = args.attempt_dir.resolve()
    sealed = attempt_dir / "sealed"
    sealed.mkdir(parents=True, exist_ok=True)
    status_path = attempt_dir / "status.json"
    log_path = attempt_dir / "stdout-stderr.log"

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    attempt_id = payload["attempt_id"]
    started_utc = utc_now()
    started = time.monotonic()
    write_status(
        status_path,
        attempt_id=attempt_id,
        run_id=payload["run_id_eval"],
        arm=payload["arm"],
        outer_split_id=payload["outer_split_id"],
        seed_bundle_id=payload["seed_bundle_id"],
        stage=payload["stage"],
        configuration_id=payload["configuration_id"],
        state="RUNNING",
        started_utc=started_utc,
        pid=os.getpid(),
        infrastructure_retry_of=payload.get("infrastructure_retry_of"),
    )

    timed_out = False
    exit_status = "FAILED"
    error_class = None
    error_message = None
    artifact_completeness = "INCOMPLETE"

    # Capture all stdout/stderr to log; never print metrics to terminal.
    log_handle = log_path.open("w", encoding="utf-8")
    sys.stdout = log_handle  # type: ignore[assignment]
    sys.stderr = log_handle  # type: ignore[assignment]
    print(f"attempt {attempt_id} started {started_utc}")
    print(f"payload_hash_placeholder path={args.payload}")

    try:
        # Load data arrays from payload paths (pre-materialized by scheduler).
        x_search = np.load(payload["x_search_path"]).astype(np.float64, copy=False)
        y_search = np.load(payload["y_search_path"]).astype(np.float64, copy=False)
        w_search = np.load(payload["w_search_path"]).astype(np.float64, copy=False)
        x_val = np.load(payload["x_val_path"]).astype(np.float64, copy=False)
        y_val = np.load(payload["y_val_path"]).astype(np.float64, copy=False)
        feature_names = list(payload["feature_names"])

        workspace = attempt_dir / "pysr_workspace"
        tempdir = attempt_dir / "pysr_temp"
        workspace.mkdir(parents=True, exist_ok=True)
        tempdir.mkdir(parents=True, exist_ok=True)

        from pysr import PySRRegressor
        from sklearn.metrics import roc_auc_score

        model = PySRRegressor(
            niterations=int(payload["niterations"]),
            populations=int(payload["populations"]),
            population_size=int(payload["population_size"]),
            ncycles_per_iteration=int(payload["ncycles_per_iteration"]),
            maxsize=int(payload["maxsize"]),
            parsimony=float(payload["parsimony"]),
            timeout_in_seconds=float(payload["timeout_seconds"]),
            binary_operators=list(payload["binary_operators"]),
            unary_operators=list(payload["unary_operators"]),
            elementwise_loss=str(payload["elementwise_loss"]),
            parallelism="serial",
            precision=64,
            deterministic=True,
            warm_start=False,
            batching=False,
            early_stop_condition=None,
            model_selection="accuracy",
            temp_equation_file=True,
            delete_tempfiles=False,
            random_state=int(payload["random_seed"]),
            output_directory=str(workspace),
            run_id=attempt_id,
            tempdir=str(tempdir),
            verbosity=0,
            progress=False,
        )

        fit_started = time.monotonic()
        model.fit(x_search, y_search, weights=w_search, variable_names=feature_names)
        fit_elapsed = time.monotonic() - fit_started
        print(f"fit_elapsed_seconds={fit_elapsed:.3f}")

        equations = getattr(model, "equations_", None)
        if equations is None or len(equations) == 0:
            raise RuntimeError("No equations retained in hall-of-fame")

        # Persist full hall of fame without printing AUCs.
        eq_csv = attempt_dir / "equations_hall_of_fame.csv"
        equations.to_csv(eq_csv, index=False)

        considered = []
        maxsize = int(payload["maxsize"])
        allowed_vars = set(feature_names)

        for idx, row in equations.reset_index(drop=True).iterrows():
            expr_id = f"{attempt_id}-E{int(idx):04d}"
            complexity = int(row["complexity"]) if "complexity" in row else int(row.get("Complexity", -1))
            loss = float(row["loss"]) if "loss" in row else float(row.get("Loss", np.nan))
            # Canonical equation string
            if "equation" in row:
                canonical = str(row["equation"])
            elif "Equation" in row:
                canonical = str(row["Equation"])
            else:
                canonical = str(row.iloc[-1])

            eligible = True
            eligibility_reasons: list[str] = []
            if complexity > maxsize:
                eligible = False
                eligibility_reasons.append("complexity_exceeds_maxsize")

            # Predict continuous scores for this equation index.
            try:
                scores = np.asarray(model.predict(x_val, index=int(idx)), dtype=np.float64)
            except Exception as pred_exc:  # noqa: BLE001
                eligible = False
                eligibility_reasons.append(f"predict_failed:{type(pred_exc).__name__}")
                scores = None

            if scores is not None:
                if not np.all(np.isfinite(scores)):
                    eligible = False
                    eligibility_reasons.append("non_finite_validation_scores")
                    auc = None
                else:
                    # Only one class would make AUC undefined; treat as ineligible.
                    if len(np.unique(y_val)) < 2:
                        eligible = False
                        eligibility_reasons.append("validation_single_class")
                        auc = None
                    else:
                        auc = float(roc_auc_score(y_val, scores))
            else:
                auc = None

            # Variable restriction check (string-level; expressions use x1/x2/x3).
            # Reject obvious leakage tokens.
            lowered = canonical.lower()
            if "final_cls" in lowered or "exclusion" in lowered:
                eligible = False
                eligibility_reasons.append("prohibited_token_in_expression")

            pred_path = sealed / f"{expr_id}-inner-validation-predictions.npz"
            if scores is not None:
                np.savez_compressed(
                    pred_path,
                    y_true=y_val.astype(np.float64),
                    continuous_score=scores.astype(np.float64),
                )

            considered.append(
                {
                    "expression_id": expr_id,
                    "equation_index": int(idx),
                    "configuration_id": payload["configuration_id"],
                    "complexity": complexity,
                    "weighted_loss": loss,
                    "canonical_expression": canonical,
                    "eligible": eligible,
                    "eligibility_reasons": eligibility_reasons,
                    "inner_validation_auc": auc,
                    "predictions_path": str(pred_path.name) if scores is not None else None,
                    "allowed_feature_names": sorted(allowed_vars),
                }
            )

        dump_json(sealed / "considered_expressions.json", considered)
        dump_json(
            attempt_dir / "runtime-memory-exit.json",
            {
                "fit_elapsed_seconds": fit_elapsed,
                "peak_rss_bytes": peak_rss_bytes(),
                "equation_count": len(considered),
                "eligible_count": sum(1 for c in considered if c["eligible"]),
            },
        )
        exit_status = "SUCCESS"
        artifact_completeness = "COMPLETE"
        error_class = None
        error_message = None
        rc = 0
    except Exception as exc:  # noqa: BLE001
        # Safety timeout is delivered as SystemExit/Timeout from outer harness if used;
        # worker itself relies on PySR timeout_in_seconds + exceptions.
        if isinstance(exc, TimeoutError):
            timed_out = True
        error_class = classify_exception(exc, timed_out=timed_out)
        error_message = f"{type(exc).__name__}: {exc}"
        print("EXCEPTION")
        traceback.print_exc()
        dump_json(
            attempt_dir / "failure.json",
            {
                "error_class": error_class,
                "error_message": error_message,
                "timed_out": timed_out,
                "traceback": traceback.format_exc(),
            },
        )
        exit_status = "FAILED"
        artifact_completeness = "FAILURE_RECORDED"
        rc = 1
    finally:
        ended_utc = utc_now()
        elapsed = time.monotonic() - started
        write_status(
            status_path,
            attempt_id=attempt_id,
            run_id=payload["run_id_eval"],
            arm=payload["arm"],
            outer_split_id=payload["outer_split_id"],
            seed_bundle_id=payload["seed_bundle_id"],
            stage=payload["stage"],
            configuration_id=payload["configuration_id"],
            state=exit_status,
            started_utc=started_utc,
            ended_utc=ended_utc,
            elapsed_seconds=elapsed,
            exit_status=exit_status,
            timed_out=timed_out,
            peak_rss_bytes=peak_rss_bytes(),
            infrastructure_retry_of=payload.get("infrastructure_retry_of"),
            error_class=error_class,
            error_message=error_message,
            artifact_completeness=artifact_completeness,
            pid=os.getpid(),
        )
        dump_json(
            attempt_dir / "attempt_manifest.json",
            {
                "attempt_id": attempt_id,
                "payload": {k: v for k, v in payload.items() if not k.endswith("_path")},
                "started_utc": started_utc,
                "ended_utc": ended_utc,
                "exit_status": exit_status,
                "error_class": error_class,
            },
        )
        log_handle.close()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
