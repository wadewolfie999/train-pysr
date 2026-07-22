#!/usr/bin/env python3
"""Resumable Act 5 stability campaign runner implementing SRRES-VP-1.0.0.

Metric values are sealed in attempt artifacts. Progress/status files are
non-metric only. Completed attempts are never rerun.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import queue
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CONTROL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CONTROL_DIR))

from lib import protocol  # noqa: E402
from lib.data_io import (  # noqa: E402
    build_feature_matrix,
    class_weights,
    load_index_array,
    load_primary_frame,
    load_secondary_frame,
    row_ids_from_indices,
)
from lib.hashutil import (  # noqa: E402
    append_jsonl,
    dump_json,
    load_json,
    manifest_for_tree,
    sha256_file,
    sha256_text,
)
from lib.selection import advance_stage_a, select_final_expression, select_within_front  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if platform.system() == "Darwin" else value * 1024


class CampaignPaths:
    def __init__(self, act5_root: Path, run_root: Path):
        self.act5_root = act5_root
        self.run_root = run_root
        self.authority = act5_root / "authority"
        self.control = act5_root / "control"
        self.repo = run_root / "train-pysr"
        self.env = run_root / "environment"
        self.evidence = run_root / "evidence"
        self.attempts = run_root / "attempts"
        self.ledgers = run_root / "ledgers"
        self.progress = run_root / "progress"
        self.package = run_root / "package"
        self.matrices = run_root / "matrices"
        self.act4_root = Path((act5_root / "ACT4_RUN_ROOT.txt").read_text(encoding="utf-8").strip())
        self.splits = self.act4_root / "evidence" / "05-splits-and-seeds"
        self.split_manifest = self.splits / "seed-split-manifest.json"
        self.primary_archive_dir = act5_root / "evidence-primary"
        self.backup_archive_dir = act5_root / "evidence-backup"


def env_for_worker(paths: CampaignPaths, guard_log: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONUNBUFFERED": "1",
            "JULIA_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHON_JULIACALL_HANDLE_SIGNALS": "yes",
            "PYTHON_JULIACALL_THREADS": "1",
            "PYTHON_JULIAPKG_EXE": str(paths.env / "julia-1.10.3" / "bin" / "julia"),
            "PYTHON_JULIAPKG_PROJECT": str(paths.env / "julia-project"),
            "PYTHON_JULIAPKG_OFFLINE": "yes",
            "JULIA_DEPOT_PATH": str(paths.env / "julia-depot"),
            "PATH": str(paths.env / "julia-1.10.3" / "bin") + os.pathsep + env.get("PATH", ""),
            "PYTHONPATH": str(paths.control / "network_guard"),
            "SRRES_NETWORK_GUARD_LOG": str(guard_log),
            # Prevent matplotlib cache writes under home if possible
            "MPLCONFIGDIR": str(paths.env / "matplotlib-cache"),
            "HOME": str(paths.run_root / "worker-home"),
        }
    )
    return env


def write_progress(paths: CampaignPaths, record: dict[str, Any]) -> None:
    """Non-metric progress only."""
    banned = ("auc", "prediction", "score", "expression", "loss", "rank")
    for key in list(record.keys()):
        lk = key.lower()
        if any(b in lk for b in banned):
            raise RuntimeError(f"metric-like key forbidden in progress: {key}")
    path = paths.progress / "campaign-status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    current = {}
    if path.exists():
        current = load_json(path)
    current.update(record)
    current["updated_utc"] = utc_now()
    dump_json(path, current)
    append_jsonl(paths.progress / "campaign-status.jsonl", current)


def ledger_append(paths: CampaignPaths, record: dict[str, Any]) -> None:
    append_jsonl(paths.ledgers / "attempt-ledger.jsonl", record)


def load_completed_attempts(paths: CampaignPaths) -> dict[str, dict[str, Any]]:
    ledger = paths.ledgers / "attempt-ledger.jsonl"
    done: dict[str, dict[str, Any]] = {}
    if not ledger.exists():
        return done
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        aid = rec["attempt_id"]
        # later terminal records overwrite
        if rec.get("state") in {"SUCCESS", "FAILED", "SKIPPED_ALREADY_COMPLETE"}:
            done[aid] = rec
    return done


def evaluation_ids() -> list[dict[str, str]]:
    rows = []
    for os_id in protocol.OUTER_IDS:
        for b_id in protocol.BUNDLE_IDS:
            for arm in protocol.ARMS:
                rows.append(
                    {
                        "run_id_eval": f"{os_id}-{b_id}-{arm}",
                        "outer_split_id": os_id,
                        "seed_bundle_id": b_id,
                        "arm": arm,
                    }
                )
    return rows


def load_component_seed(manifest: dict, outer_split_id: str, bundle_id: str, component: str) -> int:
    for split in manifest["outer_splits"]:
        if split["split_id"] != outer_split_id:
            # support alternate key
            if split.get("outer_split_id") != outer_split_id and split.get("id") != outer_split_id:
                # try pattern OS-01 from index
                continue
        for bundle in split["bundles"]:
            if bundle["bundle_id"] == bundle_id:
                return int(bundle["component_seeds"][component])
    # Fallback: walk by index
    os_idx = int(outer_split_id.split("-")[1]) - 1
    b_idx = int(bundle_id[1:]) - 1
    split = manifest["outer_splits"][os_idx]
    bundle = split["bundles"][b_idx]
    return int(bundle["component_seeds"][component])


def ensure_split_ids(manifest: dict) -> dict:
    """Normalize outer_splits entries to have split_id."""
    for i, split in enumerate(manifest["outer_splits"], start=1):
        split.setdefault("split_id", f"OS-{i:02d}")
    return manifest


def materialize_eval_matrices(paths: CampaignPaths, eval_row: dict[str, str], frames: dict[str, pd.DataFrame]) -> dict[str, Path]:
    arm = eval_row["arm"]
    os_id = eval_row["outer_split_id"]
    b_id = eval_row["seed_bundle_id"]
    out = paths.matrices / eval_row["run_id_eval"]
    out.mkdir(parents=True, exist_ok=True)
    marker = out / "READY.json"
    if marker.exists():
        return {k: out / v for k, v in load_json(marker)["files"].items()}

    df = frames["PRIMARY"] if arm == "PRIMARY" else frames["SECONDARY"]
    x_all, y_all, names = build_feature_matrix(df, arm)
    search_idx = load_index_array(paths.splits / f"{os_id}-{b_id}-inner-search.npy")
    val_idx = load_index_array(paths.splits / f"{os_id}-{b_id}-inner-validation.npy")
    test_idx = load_index_array(paths.splits / f"{os_id}-test.npy")

    x_search, y_search = x_all[search_idx], y_all[search_idx]
    x_val, y_val = x_all[val_idx], y_all[val_idx]
    x_test, y_test = x_all[test_idx], y_all[test_idx]
    w_search = class_weights(y_search)

    files = {
        "x_search": "x_search.npy",
        "y_search": "y_search.npy",
        "w_search": "w_search.npy",
        "x_val": "x_val.npy",
        "y_val": "y_val.npy",
        "x_test": "x_test.npy",
        "y_test": "y_test.npy",
        "search_idx": "search_idx.npy",
        "val_idx": "val_idx.npy",
        "test_idx": "test_idx.npy",
    }
    np.save(out / "x_search.npy", x_search)
    np.save(out / "y_search.npy", y_search)
    np.save(out / "w_search.npy", w_search)
    np.save(out / "x_val.npy", x_val)
    np.save(out / "y_val.npy", y_val)
    np.save(out / "x_test.npy", x_test)
    np.save(out / "y_test.npy", y_test)
    np.save(out / "search_idx.npy", search_idx)
    np.save(out / "val_idx.npy", val_idx)
    np.save(out / "test_idx.npy", test_idx)
    dump_json(
        out / "feature_names.json",
        {"feature_names": names, "arm": arm, "n_search": int(len(search_idx)), "n_val": int(len(val_idx)), "n_test": int(len(test_idx))},
    )
    dump_json(marker, {"files": files, "feature_names": names})
    return {k: out / v for k, v in files.items()}


def attempt_id_for(eval_id: str, stage: str, config_id: str, try_index: int) -> str:
    return f"{eval_id}-{stage}-{config_id}-T{try_index:02d}"


def run_search_attempt(
    paths: CampaignPaths,
    python: Path,
    payload: dict[str, Any],
    completed: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    attempt_id = payload["attempt_id"]
    attempt_dir = paths.attempts / attempt_id
    status_path = attempt_dir / "status.json"

    if attempt_id in completed and completed[attempt_id].get("state") == "SUCCESS":
        return {"attempt_id": attempt_id, "state": "SKIPPED_ALREADY_COMPLETE", "attempt_dir": str(attempt_dir)}
    if status_path.exists():
        st = load_json(status_path)
        if st.get("state") == "SUCCESS":
            return {"attempt_id": attempt_id, "state": "SKIPPED_ALREADY_COMPLETE", "attempt_dir": str(attempt_dir)}

    attempt_dir.mkdir(parents=True, exist_ok=True)
    payload_path = attempt_dir / "payload.json"
    dump_json(payload_path, payload)
    guard_log = attempt_dir / "network-guard.jsonl"
    env = env_for_worker(paths, guard_log)
    cmd = [
        str(python),
        str(paths.control / "search_worker.py"),
        "--attempt-dir",
        str(attempt_dir),
        "--payload",
        str(payload_path),
    ]
    (attempt_dir / "command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    started = utc_now()
    timeout = int(payload["timeout_seconds"]) + 300  # harness grace above scientific timeout
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(paths.run_root),
            env=env,
            timeout=timeout,
            check=False,
        )
        rc = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        rc = 124
        timed_out = True

    status = load_json(status_path) if status_path.exists() else {
        "attempt_id": attempt_id,
        "state": "FAILED",
        "exit_status": "FAILED",
        "timed_out": timed_out,
        "error_class": "INFRASTRUCTURE" if timed_out else "SCIENTIFIC_OR_NUMERICAL",
        "error_message": "missing status.json after worker",
    }
    if timed_out:
        status["timed_out"] = True
        status["state"] = "FAILED"
        status["error_class"] = "SAFETY_TIMEOUT"
        dump_json(status_path, status)

    record = {
        "timestamp_utc": utc_now(),
        "attempt_id": attempt_id,
        "run_id_eval": payload["run_id_eval"],
        "arm": payload["arm"],
        "outer_split_id": payload["outer_split_id"],
        "seed_bundle_id": payload["seed_bundle_id"],
        "stage": payload["stage"],
        "configuration_id": payload["configuration_id"],
        "state": status.get("state", "FAILED"),
        "exit_status": status.get("exit_status"),
        "error_class": status.get("error_class"),
        "timed_out": status.get("timed_out", False),
        "elapsed_seconds": status.get("elapsed_seconds"),
        "peak_rss_bytes": status.get("peak_rss_bytes"),
        "infrastructure_retry_of": payload.get("infrastructure_retry_of"),
        "worker_returncode": rc,
        "attempt_dir": str(attempt_dir),
        "started_utc": started,
        "ended_utc": utc_now(),
    }
    ledger_append(paths, record)
    return record


def maybe_infrastructure_retry(
    paths: CampaignPaths,
    python: Path,
    payload: dict[str, Any],
    first_result: dict[str, Any],
    completed: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if first_result.get("state") == "SUCCESS":
        return first_result
    # Only one infrastructure retry, classified before metric access.
    # Read failure classification from worker failure.json / status.
    attempt_dir = Path(first_result["attempt_dir"])
    status = load_json(attempt_dir / "status.json") if (attempt_dir / "status.json").exists() else {}
    error_class = status.get("error_class") or first_result.get("error_class")
    if error_class != "INFRASTRUCTURE":
        return first_result
    # Already a retry?
    if payload.get("try_index", 1) >= 2 or payload.get("infrastructure_retry_of"):
        return first_result

    retry_payload = dict(payload)
    retry_payload["try_index"] = 2
    retry_payload["attempt_id"] = attempt_id_for(
        payload["run_id_eval"], payload["stage"], payload["configuration_id"], 2
    )
    retry_payload["infrastructure_retry_of"] = payload["attempt_id"]
    return run_search_attempt(paths, python, retry_payload, completed)


def load_considered(attempt_dir: Path) -> list[dict[str, Any]]:
    path = attempt_dir / "sealed" / "considered_expressions.json"
    if not path.exists():
        return []
    return load_json(path)


def stage_a_representative(attempt_dir: Path) -> dict[str, Any] | None:
    considered = load_considered(attempt_dir)
    if not considered:
        return None
    return select_within_front(considered)


def process_evaluation(
    paths: CampaignPaths,
    python: Path,
    eval_row: dict[str, str],
    matrices: dict[str, Path],
    feature_names: list[str],
    manifest: dict,
    completed: dict[str, dict[str, Any]],
    max_workers: int,
    stop_event: threading.Event,
) -> dict[str, Any]:
    eval_id = eval_row["run_id_eval"]
    eval_dir = paths.evidence / "06-attempts" / eval_id
    eval_dir.mkdir(parents=True, exist_ok=True)
    result_path = eval_dir / "evaluation-result.json"
    if result_path.exists():
        prev = load_json(result_path)
        if prev.get("state") in {"COMPLETE", "FAILED_NO_VALID_STAGE_A", "FAILED_NO_VALID_STAGE_B"}:
            return prev

    write_progress(
        paths,
        {
            "active_evaluation": eval_id,
            "phase": "STAGE_A",
            "state": "RUNNING",
        },
    )

    # Stage A payloads
    stage_a_results: dict[str, dict[str, Any]] = {}
    payloads = []
    for cfg in protocol.CANDIDATE_CONFIGS:
        cid = cfg["id"]
        seed = load_component_seed(manifest, eval_row["outer_split_id"], eval_row["seed_bundle_id"], f"screen-{cid}")
        payload = {
            "attempt_id": attempt_id_for(eval_id, "A", cid, 1),
            "run_id_eval": eval_id,
            "arm": eval_row["arm"],
            "outer_split_id": eval_row["outer_split_id"],
            "seed_bundle_id": eval_row["seed_bundle_id"],
            "stage": "A",
            "configuration_id": cid,
            "try_index": 1,
            "random_seed": seed,
            "maxsize": cfg["maxsize"],
            "parsimony": cfg["parsimony"],
            "niterations": protocol.STAGE_A["niterations"],
            "populations": protocol.STAGE_A["populations"],
            "population_size": protocol.STAGE_A["population_size"],
            "ncycles_per_iteration": protocol.STAGE_A["ncycles_per_iteration"],
            "timeout_seconds": protocol.STAGE_A["timeout_seconds"],
            "binary_operators": protocol.BINARY_OPERATORS,
            "unary_operators": protocol.UNARY_OPERATORS,
            "elementwise_loss": protocol.ELEMENTWISE_LOSS,
            "feature_names": feature_names,
            "x_search_path": str(matrices["x_search"]),
            "y_search_path": str(matrices["y_search"]),
            "w_search_path": str(matrices["w_search"]),
            "x_val_path": str(matrices["x_val"]),
            "y_val_path": str(matrices["y_val"]),
            "infrastructure_retry_of": None,
        }
        payloads.append(payload)

    # Run Stage A with bounded concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_search_attempt, paths, python, p, completed): p for p in payloads
        }
        for fut in as_completed(futures):
            if stop_event.is_set():
                break
            p = futures[fut]
            first = fut.result()
            final = maybe_infrastructure_retry(paths, python, p, first, completed)
            stage_a_results[p["configuration_id"]] = final
            write_progress(
                paths,
                {
                    "active_evaluation": eval_id,
                    "phase": "STAGE_A",
                    "last_completed_attempt": final.get("attempt_id"),
                    "last_attempt_state": final.get("state"),
                    "state": "RUNNING",
                },
            )

    reps = []
    for cfg in protocol.CANDIDATE_CONFIGS:
        cid = cfg["id"]
        res = stage_a_results.get(cid, {})
        if res.get("state") in {"SUCCESS", "SKIPPED_ALREADY_COMPLETE"}:
            rep = stage_a_representative(Path(res["attempt_dir"]))
        else:
            rep = None
        reps.append(rep)

    advancement = advance_stage_a(reps)
    dump_json(eval_dir / "stage-a-advancement.json", {
        "valid_configuration_count": advancement["valid_configuration_count"],
        "advanced_configuration_ids": advancement["advanced_configuration_ids"],
        "bundle_failed_no_valid_stage_a": advancement["bundle_failed_no_valid_stage_a"],
        # Do not include AUC values in non-sealed advancement summary for monitor surfaces.
        "rule": advancement["rule"],
    })
    # Seal full advancement with metrics for evidence only
    dump_json(eval_dir / "sealed" / "stage-a-advancement-full.json", advancement)

    if advancement["bundle_failed_no_valid_stage_a"]:
        out = {
            "run_id_eval": eval_id,
            "state": "FAILED_NO_VALID_STAGE_A",
            "advanced_configuration_ids": [],
            "completed_utc": utc_now(),
        }
        dump_json(result_path, out)
        return out

    write_progress(paths, {"active_evaluation": eval_id, "phase": "STAGE_B", "state": "RUNNING"})

    stage_b_results: dict[str, dict[str, Any]] = {}
    b_payloads = []
    for cid in advancement["advanced_configuration_ids"]:
        cfg = next(c for c in protocol.CANDIDATE_CONFIGS if c["id"] == cid)
        seed = load_component_seed(manifest, eval_row["outer_split_id"], eval_row["seed_bundle_id"], f"full-{cid}")
        payload = {
            "attempt_id": attempt_id_for(eval_id, "B", cid, 1),
            "run_id_eval": eval_id,
            "arm": eval_row["arm"],
            "outer_split_id": eval_row["outer_split_id"],
            "seed_bundle_id": eval_row["seed_bundle_id"],
            "stage": "B",
            "configuration_id": cid,
            "try_index": 1,
            "random_seed": seed,
            "maxsize": cfg["maxsize"],
            "parsimony": cfg["parsimony"],
            "niterations": protocol.STAGE_B["niterations"],
            "populations": protocol.STAGE_B["populations"],
            "population_size": protocol.STAGE_B["population_size"],
            "ncycles_per_iteration": protocol.STAGE_B["ncycles_per_iteration"],
            "timeout_seconds": protocol.STAGE_B["timeout_seconds"],
            "binary_operators": protocol.BINARY_OPERATORS,
            "unary_operators": protocol.UNARY_OPERATORS,
            "elementwise_loss": protocol.ELEMENTWISE_LOSS,
            "feature_names": feature_names,
            "x_search_path": str(matrices["x_search"]),
            "y_search_path": str(matrices["y_search"]),
            "w_search_path": str(matrices["w_search"]),
            "x_val_path": str(matrices["x_val"]),
            "y_val_path": str(matrices["y_val"]),
            "infrastructure_retry_of": None,
        }
        b_payloads.append(payload)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_search_attempt, paths, python, p, completed): p for p in b_payloads
        }
        for fut in as_completed(futures):
            p = futures[fut]
            first = fut.result()
            final = maybe_infrastructure_retry(paths, python, p, first, completed)
            stage_b_results[p["configuration_id"]] = final
            write_progress(
                paths,
                {
                    "active_evaluation": eval_id,
                    "phase": "STAGE_B",
                    "last_completed_attempt": final.get("attempt_id"),
                    "last_attempt_state": final.get("state"),
                    "state": "RUNNING",
                },
            )

    # Collect Stage B expressions
    all_b_exprs: list[dict[str, Any]] = []
    for cid, res in stage_b_results.items():
        if res.get("state") in {"SUCCESS", "SKIPPED_ALREADY_COMPLETE"}:
            all_b_exprs.extend(load_considered(Path(res["attempt_dir"])))

    selected = select_final_expression(all_b_exprs)
    if selected is None:
        out = {
            "run_id_eval": eval_id,
            "state": "FAILED_NO_VALID_STAGE_B",
            "advanced_configuration_ids": advancement["advanced_configuration_ids"],
            "completed_utc": utc_now(),
        }
        dump_json(result_path, out)
        return out

    # Outer-test evaluation once
    from sklearn.metrics import roc_auc_score

    # Reload model predictions by re-predicting via sympy/pysr is heavy; instead
    # re-run predict using stored equation index from the successful Stage-B attempt.
    # We re-fit is prohibited; use saved model if present, else re-evaluate with sympy.
    # Prefer: re-invoke worker-side stored equations via numpy sympy-free path:
    # load the stage-B attempt equations and use pysr model pickle if available.
    sel_cfg = selected["configuration_id"]
    b_attempt_dir = Path(stage_b_results[sel_cfg]["attempt_dir"])
    # Reconstruct continuous scores by fitting is NOT allowed. Use model.predict if model exists.
    # PySR stores equations; we re-load via a short prediction helper that does not re-search.
    outer_scores, outer_ok, outer_err = outer_predict_from_attempt(
        paths, python, b_attempt_dir, selected, matrices, feature_names, eval_id
    )

    sealed_sel = eval_dir / "sealed"
    sealed_sel.mkdir(parents=True, exist_ok=True)
    dump_json(sealed_sel / "selected_expression.json", selected)

    outer_record: dict[str, Any] = {
        "run_id_eval": eval_id,
        "selected_expression_id": selected["expression_id"],
        "configuration_id": selected["configuration_id"],
        "outer_ok": outer_ok,
    }
    if outer_ok:
        y_test = np.load(matrices["y_test"]).astype(np.float64)
        test_idx = np.load(matrices["test_idx"]).astype(np.int64)
        auc = float(roc_auc_score(y_test, outer_scores))
        pred_path = sealed_sel / "outer-test-predictions.npz"
        np.savez_compressed(
            pred_path,
            row_id=np.array(row_ids_from_indices(test_idx)),
            y_true=y_test,
            continuous_score=outer_scores.astype(np.float64),
        )
        dump_json(
            sealed_sel / "outer-test-metrics.json",
            {
                "outer_test_auc": auc,
                "n_test": int(len(y_test)),
                "finite": bool(np.all(np.isfinite(outer_scores))),
            },
        )
        outer_record["outer_test_auc_present"] = True
    else:
        outer_record["outer_test_auc_present"] = False
        outer_record["outer_error"] = outer_err
        dump_json(sealed_sel / "outer-test-failure.json", {"error": outer_err})

    out = {
        "run_id_eval": eval_id,
        "arm": eval_row["arm"],
        "outer_split_id": eval_row["outer_split_id"],
        "seed_bundle_id": eval_row["seed_bundle_id"],
        "state": "COMPLETE" if outer_ok else "FAILED_OUTER_TEST",
        "advanced_configuration_ids": advancement["advanced_configuration_ids"],
        "selected_expression_id": selected["expression_id"],
        "selected_configuration_id": selected["configuration_id"],
        "outer_test_auc_present": outer_record.get("outer_test_auc_present", False),
        "completed_utc": utc_now(),
    }
    dump_json(result_path, out)
    # Registry row without printing AUC
    append_jsonl(
        paths.evidence / "07-registries" / f"{eval_row['arm'].lower()}-result-registry.jsonl",
        {
            "run_id_eval": eval_id,
            "arm": eval_row["arm"],
            "outer_split_id": eval_row["outer_split_id"],
            "seed_bundle_id": eval_row["seed_bundle_id"],
            "state": out["state"],
            "selected_expression_id": out.get("selected_expression_id"),
            "selected_configuration_id": out.get("selected_configuration_id"),
            "outer_test_auc_present": out.get("outer_test_auc_present"),
            "completed_utc": out["completed_utc"],
        },
    )
    return out


def outer_predict_from_attempt(
    paths: CampaignPaths,
    python: Path,
    attempt_dir: Path,
    selected: dict[str, Any],
    matrices: dict[str, Path],
    feature_names: list[str],
    eval_id: str,
) -> tuple[np.ndarray | None, bool, str | None]:
    """Predict outer-test scores for a selected Stage-B equation without re-search.

    Uses a short helper process that loads hall-of-fame and re-fits is forbidden;
    instead reconstructs expression via sympy from equation string when possible,
    falling back to re-running model.predict requires the fitted model object.

    Practical approach for PySR 1.5.10: re-load equations CSV and use
    pysr.export_sympy / lambdify for continuous scores.
    """
    helper = paths.control / "outer_predict_helper.py"
    out_npz = paths.matrices / eval_id / "outer_scores.npy"
    cmd = [
        str(python),
        str(helper),
        "--attempt-dir",
        str(attempt_dir),
        "--equation-index",
        str(selected["equation_index"]),
        "--x-path",
        str(matrices["x_test"]),
        "--feature-names",
        ",".join(feature_names),
        "--out-path",
        str(out_npz),
    ]
    guard_log = attempt_dir / "outer-predict-network-guard.jsonl"
    env = env_for_worker(paths, guard_log)
    # Outer predict may need sympy only; network still denied.
    try:
        proc = subprocess.run(cmd, env=env, cwd=str(paths.run_root), timeout=600, check=False, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None, False, "outer_predict_timeout"
    if proc.returncode != 0 or not out_npz.exists():
        return None, False, f"outer_predict_failed rc={proc.returncode} stderr={proc.stderr[-2000:]}"
    scores = np.load(out_npz).astype(np.float64)
    if not np.all(np.isfinite(scores)):
        return None, False, "non_finite_outer_scores"
    return scores, True, None


def build_paired_registry(paths: CampaignPaths) -> None:
    primary = paths.evidence / "07-registries" / "primary-result-registry.jsonl"
    secondary = paths.evidence / "07-registries" / "secondary-result-registry.jsonl"
    pmap = {}
    smap = {}
    if primary.exists():
        for line in primary.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            key = (r["outer_split_id"], r["seed_bundle_id"])
            pmap[key] = r
    if secondary.exists():
        for line in secondary.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            key = (r["outer_split_id"], r["seed_bundle_id"])
            smap[key] = r
    out = paths.evidence / "07-registries" / "paired-run-registry.jsonl"
    if out.exists():
        out.unlink()
    for os_id in protocol.OUTER_IDS:
        for b in protocol.BUNDLE_IDS:
            key = (os_id, b)
            append_jsonl(
                out,
                {
                    "outer_split_id": os_id,
                    "seed_bundle_id": b,
                    "primary_run_id": f"{os_id}-{b}-PRIMARY",
                    "secondary_run_id": f"{os_id}-{b}-SECONDARY",
                    "primary_state": (pmap.get(key) or {}).get("state"),
                    "secondary_state": (smap.get(key) or {}).get("state"),
                    "primary_outer_test_auc_present": (pmap.get(key) or {}).get("outer_test_auc_present"),
                    "secondary_outer_test_auc_present": (smap.get(key) or {}).get("outer_test_auc_present"),
                },
            )


def compute_bootstrap_package(paths: CampaignPaths) -> Path:
    """Create Act 6 adjudication-input package WITHOUT scientific verdict."""
    from numpy.random import Generator, PCG64

    primary_aucs = []
    secondary_aucs = []
    for os_id in protocol.OUTER_IDS:
        for b in protocol.BUNDLE_IDS:
            for arm, bucket in (("PRIMARY", primary_aucs), ("SECONDARY", secondary_aucs)):
                eval_id = f"{os_id}-{b}-{arm}"
                metrics = paths.evidence / "06-attempts" / eval_id / "sealed" / "outer-test-metrics.json"
                if metrics.exists():
                    bucket.append(
                        {
                            "outer_split_id": os_id,
                            "seed_bundle_id": b,
                            "auc": load_json(metrics)["outer_test_auc"],
                        }
                    )

    def hierarchical_median_boot(values_by_split: dict[str, list[float]], seed: int, paired: bool = False):
        # values_by_split: OS-id -> list of 3 AUCs
        rng = Generator(PCG64(seed))
        splits = sorted(values_by_split.keys())
        medians = []
        for _ in range(protocol.BOOTSTRAP_REPLICATES):
            sampled_splits = rng.choice(splits, size=len(splits), replace=True)
            pool = []
            for s in sampled_splits:
                vals = values_by_split[s]
                pool.extend(list(rng.choice(vals, size=3, replace=True)))
            medians.append(float(np.median(pool)))
        return np.asarray(medians, dtype=np.float64)

    def by_split(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
        out: dict[str, list[float]] = {os_id: [] for os_id in protocol.OUTER_IDS}
        for r in rows:
            out[r["outer_split_id"]].append(float(r["auc"]))
        return out

    pkg_dir = paths.evidence / "11-act6-adjudication-input"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    primary_values = [r["auc"] for r in primary_aucs]
    secondary_values = [r["auc"] for r in secondary_aucs]

    summary: dict[str, Any] = {
        "protocol_id": protocol.PROTOCOL_ID,
        "scientific_verdict": None,
        "adjudication_authorized": False,
        "note": "Inputs only. Act 6 remains unauthorized. No pass/fail declared.",
        "primary_complete_count": len(primary_values),
        "secondary_complete_count": len(secondary_values),
        "expected_per_arm": 30,
    }

    if len(primary_values) == 30:
        arr = np.asarray(primary_values, dtype=np.float64)
        k = int(np.sum(arr > 0.970000))
        summary["primary"] = {
            "K_count_auc_gt_0p97": k,
            "success_proportion": k / 30.0,
            "median": float(np.median(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "q1": float(np.quantile(arr, 0.25, method="linear")),
            "q3": float(np.quantile(arr, 0.75, method="linear")),
            "individual_aucs": primary_aucs,
        }
        boot = hierarchical_median_boot(by_split(primary_aucs), protocol.BOOTSTRAP_PRIMARY_SEED)
        summary["primary"]["bootstrap_one_sided_95_lower"] = float(np.quantile(boot, 0.05, method="linear"))
        summary["primary"]["bootstrap_replicates"] = protocol.BOOTSTRAP_REPLICATES
        summary["primary"]["bootstrap_seed"] = protocol.BOOTSTRAP_PRIMARY_SEED
    else:
        summary["primary"] = {"status": "INCOMPLETE", "n": len(primary_values)}

    if len(secondary_values) == 30 and len(primary_values) == 30:
        # Paired deltas by (OS,B)
        pmap = {(r["outer_split_id"], r["seed_bundle_id"]): r["auc"] for r in primary_aucs}
        smap = {(r["outer_split_id"], r["seed_bundle_id"]): r["auc"] for r in secondary_aucs}
        deltas = []
        for os_id in protocol.OUTER_IDS:
            for b in protocol.BUNDLE_IDS:
                deltas.append(
                    {
                        "outer_split_id": os_id,
                        "seed_bundle_id": b,
                        "delta": smap[(os_id, b)] - pmap[(os_id, b)],
                    }
                )
        dvals = np.asarray([d["delta"] for d in deltas], dtype=np.float64)
        # hierarchical bootstrap on deltas grouped by split
        d_by = {os_id: [] for os_id in protocol.OUTER_IDS}
        for d in deltas:
            d_by[d["outer_split_id"]].append(d["delta"])
        boot = hierarchical_median_boot(d_by, protocol.BOOTSTRAP_DELTA_SEED)
        summary["secondary"] = {
            "median_auc": float(np.median([r["auc"] for r in secondary_aucs])),
            "individual_aucs": secondary_aucs,
            "paired_deltas": deltas,
            "paired_delta_median": float(np.median(dvals)),
            "paired_delta_bootstrap_ci_95": [
                float(np.quantile(boot, 0.025, method="linear")),
                float(np.quantile(boot, 0.975, method="linear")),
            ],
            "bootstrap_seed": protocol.BOOTSTRAP_DELTA_SEED,
        }
    else:
        summary["secondary"] = {
            "status": "INCOMPLETE",
            "n": len(secondary_values),
        }

    dump_json(pkg_dir / "adjudication-input-summary.json", summary)
    # Do not declare pass/fail thresholds evaluation
    dump_json(
        pkg_dir / "README.json",
        {
            "status": "ACT6_INPUT_ONLY",
            "scientific_verdict": None,
            "message": "No scientific pass/fail decision is included.",
        },
    )
    return pkg_dir


def freeze_control_hashes(paths: CampaignPaths) -> Path:
    rows = manifest_for_tree(paths.control)
    out = paths.evidence / "02-support-code" / "control-source-hashes.sha256"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{r['sha256']}  {r['path']}" for r in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dump_json(paths.evidence / "02-support-code" / "control-source-manifest.json", {"files": rows})
    return out


def package_final_archive(paths: CampaignPaths) -> dict[str, Any]:
    build_paired_registry(paths)
    adj = compute_bootstrap_package(paths)

    # Full artifact manifest of evidence tree + attempts + ledgers + progress
    package_root = paths.package / "SRRES-ACT5-A4-EVIDENCE"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True)

    # Copy evidence, attempts, ledgers, progress, control hashes, authority
    for name, src in [
        ("evidence", paths.evidence),
        ("attempts", paths.attempts),
        ("ledgers", paths.ledgers),
        ("progress", paths.progress),
        ("authority", paths.authority),
        ("control", paths.control),
    ]:
        dst = package_root / name
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # Drop sealed metrics from progress (already non-metric). Remove worker matrices (large, reconstructible from splits)?
    # Keep matrices only if needed; they are derived from frozen splits+data. Include for completeness of scores provenance.
    if (paths.matrices).exists():
        shutil.copytree(paths.matrices, package_root / "matrices", dirs_exist_ok=True)

    rows = manifest_for_tree(package_root)
    dump_json(package_root / "full-artifact-manifest.json", {"artifact_count": len(rows), "artifacts": rows})
    # sidecar sha256 list
    man_lines = [f"{r['sha256']}  {r['path']}" for r in rows]
    (package_root / "full-artifact-manifest.sha256").write_text("\n".join(man_lines) + "\n", encoding="utf-8")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    primary_dir = paths.primary_archive_dir / stamp
    backup_dir = paths.backup_archive_dir / stamp
    primary_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    def make_tar(dest: Path) -> None:
        with tarfile.open(dest, "w:gz", compresslevel=9) as tar:
            tar.add(package_root, arcname="SRRES-ACT5-A4-EVIDENCE")

    primary_tar = primary_dir / "SRRES-ACT5-A4-EVIDENCE.tar.gz"
    backup_tar = backup_dir / "SRRES-ACT5-A4-EVIDENCE.tar.gz"
    make_tar(primary_tar)
    shutil.copy2(primary_tar, backup_tar)
    h1 = sha256_file(primary_tar)
    h2 = sha256_file(backup_tar)
    (primary_tar.with_suffix(primary_tar.suffix + ".sha256")).write_text(f"{h1}  {primary_tar.name}\n", encoding="utf-8")
    (backup_tar.with_suffix(backup_tar.suffix + ".sha256")).write_text(f"{h2}  {backup_tar.name}\n", encoding="utf-8")

    adj_manifest = manifest_for_tree(adj)
    dump_json(adj / "package-manifest.json", {"files": adj_manifest})
    adj_hash = sha256_text(json.dumps(adj_manifest, sort_keys=True))

    result = {
        "primary_archive": str(primary_tar),
        "backup_archive": str(backup_tar),
        "primary_sha256": h1,
        "backup_sha256": h2,
        "primary_bytes": primary_tar.stat().st_size,
        "backup_bytes": backup_tar.stat().st_size,
        "archives_match": h1 == h2 and primary_tar.stat().st_size == backup_tar.stat().st_size,
        "artifact_manifest": str(package_root / "full-artifact-manifest.sha256"),
        "artifact_manifest_sha256": sha256_file(package_root / "full-artifact-manifest.sha256"),
        "act6_package": str(adj),
        "act6_package_content_sha256": adj_hash,
    }
    dump_json(paths.package / "final-package-record.json", result)
    return result


def completeness_counts(paths: CampaignPaths) -> dict[str, Any]:
    counts = {
        "evaluations_expected": 60,
        "by_state": {},
        "by_arm": {"PRIMARY": {}, "SECONDARY": {}},
        "attempts_total": 0,
        "attempts_success": 0,
        "attempts_failed": 0,
        "infrastructure_retries": 0,
    }
    for eval_row in evaluation_ids():
        result_path = paths.evidence / "06-attempts" / eval_row["run_id_eval"] / "evaluation-result.json"
        state = "PENDING"
        if result_path.exists():
            state = load_json(result_path).get("state", "UNKNOWN")
        counts["by_state"][state] = counts["by_state"].get(state, 0) + 1
        arm = eval_row["arm"]
        counts["by_arm"][arm][state] = counts["by_arm"][arm].get(state, 0) + 1

    ledger = paths.ledgers / "attempt-ledger.jsonl"
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            counts["attempts_total"] += 1
            if rec.get("state") == "SUCCESS":
                counts["attempts_success"] += 1
            if rec.get("state") == "FAILED":
                counts["attempts_failed"] += 1
            if rec.get("infrastructure_retry_of"):
                counts["infrastructure_retries"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--act5-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--max-concurrent", type=int, default=protocol.DEFAULT_MAX_CONCURRENT_SEARCHES)
    parser.add_argument("--package-only", action="store_true")
    args = parser.parse_args()

    paths = CampaignPaths(args.act5_root.resolve(), args.run_root.resolve())
    for d in [paths.attempts, paths.ledgers, paths.progress, paths.package, paths.matrices, paths.evidence]:
        d.mkdir(parents=True, exist_ok=True)
    (paths.run_root / "worker-home").mkdir(parents=True, exist_ok=True)

    python = paths.env / "python" / "bin" / "python"
    if not python.exists():
        print("BLOCKED: python interpreter missing", file=sys.stderr)
        return 2

    stop_event = threading.Event()

    def _handle_sigterm(signum, frame):  # noqa: ARG001
        stop_event.set()
        write_progress(paths, {"state": "STOPPING", "reason": f"signal_{signum}"})

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    write_progress(
        paths,
        {
            "state": "STARTING",
            "max_concurrent_searches": args.max_concurrent,
            "protocol_id": protocol.PROTOCOL_ID,
            "scientific_compute": "LOCAL_ONLY",
            "pid": os.getpid(),
        },
    )

    if args.package_only:
        result = package_final_archive(paths)
        dump_json(paths.package / "completeness-counts.json", completeness_counts(paths))
        print(json.dumps({"status": "PACKAGED", "archives_match": result["archives_match"]}, indent=2))
        return 0 if result["archives_match"] else 2

    # Freeze control hashes before any fit if not already frozen.
    freeze_marker = paths.evidence / "02-support-code" / "FROZEN.json"
    if not freeze_marker.exists():
        freeze_control_hashes(paths)
        dump_json(
            freeze_marker,
            {
                "frozen_utc": utc_now(),
                "note": "Control sources frozen before claim-bearing fits",
            },
        )

    # Load data and split manifest
    frames = {
        "PRIMARY": load_primary_frame(paths.repo),
        "SECONDARY": load_secondary_frame(paths.repo),
    }
    manifest = ensure_split_ids(load_json(paths.split_manifest))
    completed = load_completed_attempts(paths)

    dump_json(
        paths.evidence / "01-system-and-executables" / "concurrency-schedule.json",
        {
            "max_concurrent_searches": args.max_concurrent,
            "threads_per_search": 1,
            "blas_threads": 1,
            "cpu_count": os.cpu_count(),
            "machine": platform.machine(),
            "platform": platform.platform(),
            "frozen_before_fits": True,
        },
    )

    evals = evaluation_ids()
    # Deterministic order: PRIMARY first for each OS/B, then SECONDARY (or interleaved OS,B,arm)
    for i, eval_row in enumerate(evals, start=1):
        if stop_event.is_set():
            write_progress(paths, {"state": "STOPPED", "reason": "signal"})
            return 130
        write_progress(
            paths,
            {
                "state": "RUNNING",
                "evaluations_started": i,
                "evaluations_total": len(evals),
                "active_evaluation": eval_row["run_id_eval"],
            },
        )
        matrices = materialize_eval_matrices(paths, eval_row, frames)
        feature_names = load_json(paths.matrices / eval_row["run_id_eval"] / "feature_names.json")["feature_names"]
        # Refresh completed map periodically
        completed = load_completed_attempts(paths)
        try:
            process_evaluation(
                paths,
                python,
                eval_row,
                matrices,
                feature_names,
                manifest,
                completed,
                args.max_concurrent,
                stop_event,
            )
        except Exception as exc:  # noqa: BLE001
            # Integrity-class failures should stop campaign
            msg = f"{type(exc).__name__}: {exc}"
            integrity_markers = ("authority", "environment", "split", "hash", "leakage", "provenance", "BLOCKED")
            if any(m.lower() in msg.lower() for m in integrity_markers):
                write_progress(paths, {"state": "BLOCKED", "reason": msg})
                dump_json(paths.ledgers / "campaign-block.json", {"reason": msg, "utc": utc_now()})
                return 2
            # Ordinary scientific failures are handled inside process_evaluation.
            dump_json(
                paths.evidence / "09-deviations-and-failures" / f"{eval_row['run_id_eval']}-runner-exception.json",
                {"error": msg, "utc": utc_now()},
            )
            continue

    write_progress(paths, {"state": "PACKAGING", "active_evaluation": None})
    package_result = package_final_archive(paths)
    counts = completeness_counts(paths)
    dump_json(paths.package / "completeness-counts.json", counts)
    write_progress(
        paths,
        {
            "state": "COMPLETE",
            "archives_match": package_result["archives_match"],
            "primary_archive": package_result["primary_archive"],
            "backup_archive": package_result["backup_archive"],
        },
    )
    # Final summary intentionally omits AUCs.
    print(
        json.dumps(
            {
                "status": "COMPLETE" if package_result["archives_match"] else "BLOCKED",
                "completeness": counts,
                "primary_sha256": package_result["primary_sha256"],
                "backup_sha256": package_result["backup_sha256"],
            },
            indent=2,
        )
    )
    return 0 if package_result["archives_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
