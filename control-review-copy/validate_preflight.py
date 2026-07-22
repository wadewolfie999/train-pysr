#!/usr/bin/env python3
"""No-training Act 5 preflight: authority, environment, data, splits, code identity."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow importing local lib package when launched from control/
CONTROL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CONTROL_DIR))

from lib import protocol  # noqa: E402
from lib.data_io import validate_datasets  # noqa: E402
from lib.hashutil import dump_json, sha256_file  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed32(label: str) -> int:
    return int.from_bytes(
        hashlib.sha256(("SRRES|ACT3|VP-1.0.0|" + label).encode("utf-8")).digest()[:4],
        byteorder="big",
        signed=False,
    )


def verify_seeds() -> dict:
    ok = True
    details = []
    for i, expected in enumerate(protocol.OUTER_SEEDS, start=1):
        got = seed32(f"outer|{i:02d}")
        match = got == expected
        ok = ok and match
        details.append({"label": f"outer|{i:02d}", "expected": expected, "got": got, "ok": match})
    for i, masters in enumerate(protocol.BUNDLE_MASTERS, start=1):
        for j, expected in enumerate(masters, start=1):
            got = seed32(f"bundle|{i:02d}|{j:02d}")
            match = got == expected
            ok = ok and match
            details.append(
                {
                    "label": f"bundle|{i:02d}|{j:02d}",
                    "expected": expected,
                    "got": got,
                    "ok": match,
                }
            )
    return {"status": "PASS" if ok else "BLOCKED", "details": details}


def verify_act4_archive(authority_dir: Path) -> dict:
    path = authority_dir / "SRRES-ACT4-A4-COMBINED-EVIDENCE.tar.gz"
    digest = sha256_file(path)
    return {
        "path": str(path),
        "sha256": digest,
        "expected": protocol.ACT4_ARCHIVE_SHA256,
        "bytes": path.stat().st_size,
        "status": "PASS" if digest == protocol.ACT4_ARCHIVE_SHA256 else "BLOCKED",
    }


def verify_repo(repo: Path) -> dict:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    porcelain = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    detached = (
        subprocess.call(["git", "symbolic-ref", "-q", "HEAD"], cwd=repo, stdout=subprocess.DEVNULL)
        != 0
    )
    clean = porcelain.strip() == ""
    status = "PASS" if head == protocol.REPO_COMMIT and clean and detached else "BLOCKED"
    return {
        "commit": head,
        "expected_commit": protocol.REPO_COMMIT,
        "clean": clean,
        "detached": detached,
        "status": status,
        "porcelain": porcelain,
    }


def verify_locks(env_root: Path, evidence_locks: Path) -> dict:
    checks = {}
    for name, expected, path in [
        (
            "requirements_lock",
            protocol.REQUIREMENTS_LOCK_SHA256,
            evidence_locks / "requirements-act4.lock",
        ),
        (
            "julia_project",
            protocol.JULIA_PROJECT_SHA256,
            env_root / "julia-project" / "Project.toml",
        ),
        (
            "julia_manifest",
            protocol.JULIA_MANIFEST_SHA256,
            env_root / "julia-project" / "Manifest.toml",
        ),
    ]:
        digest = sha256_file(path)
        checks[name] = {
            "path": str(path),
            "sha256": digest,
            "expected": expected,
            "status": "PASS" if digest == expected else "BLOCKED",
        }
    # live julia project must match evidence locks
    for name, live, evid in [
        (
            "julia_project_vs_evidence",
            env_root / "julia-project" / "Project.toml",
            evidence_locks / "Project.toml",
        ),
        (
            "julia_manifest_vs_evidence",
            env_root / "julia-project" / "Manifest.toml",
            evidence_locks / "Manifest.toml",
        ),
    ]:
        live_h = sha256_file(live)
        evid_h = sha256_file(evid)
        checks[name] = {
            "live_sha256": live_h,
            "evidence_sha256": evid_h,
            "status": "PASS" if live_h == evid_h else "BLOCKED",
        }
    status = "PASS" if all(v["status"] == "PASS" for v in checks.values()) else "BLOCKED"
    return {"status": status, "checks": checks}


def verify_python_versions() -> dict:
    versions = {"Python": platform.python_version()}
    mapping = {
        "numpy": "numpy",
        "pandas": "pandas",
        "scikit-learn": "sklearn",
        "scipy": "scipy",
        "sympy": "sympy",
        "PyYAML": "yaml",
        "matplotlib": "matplotlib",
        "juliapkg": "juliapkg",
    }
    for dist, module in mapping.items():
        importlib.import_module(module)
        versions[dist] = importlib.metadata.version(dist)
    # pysr/juliacall versions without forcing julia if possible
    versions["pysr"] = importlib.metadata.version("pysr")
    versions["juliacall"] = importlib.metadata.version("juliacall")
    mismatches = {
        k: {"got": versions[k], "expected": protocol.LOCKED_VERSIONS[k]}
        for k in protocol.LOCKED_VERSIONS
        if k not in {"Julia", "SymbolicRegression"} and versions.get(k) != protocol.LOCKED_VERSIONS[k]
    }
    return {
        "versions": versions,
        "mismatches": mismatches,
        "status": "PASS" if not mismatches else "BLOCKED",
    }


def verify_backend() -> dict:
    from juliacall import Main as jl

    julia_version = str(jl.seval("string(VERSION)"))
    symbolic_version = str(
        jl.seval("using SymbolicRegression; string(Base.pkgversion(SymbolicRegression))")
    )
    from pysr import PySRRegressor

    _cfg = PySRRegressor(
        niterations=1,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["square", "abs", "log1p"],
    )
    ok = (
        julia_version == protocol.LOCKED_VERSIONS["Julia"]
        and symbolic_version == protocol.LOCKED_VERSIONS["SymbolicRegression"]
    )
    return {
        "julia_version": julia_version,
        "symbolic_regression_version": symbolic_version,
        "pysr_configuration_only": True,
        "fit_invoked": False,
        "status": "PASS" if ok else "BLOCKED",
    }


def verify_splits(split_dir: Path, manifest_path: Path) -> dict:
    # Prefer Act4 seed-split-manifest.json; its file SHA-256 is the locked identity.
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    combined = sha256_file(manifest_path)
    ok = True
    missing = []
    for os_i in range(1, 11):
        for kind in ("train", "test"):
            p = split_dir / f"OS-{os_i:02d}-{kind}.npy"
            if not p.exists():
                missing.append(str(p))
                ok = False
        for b in range(1, 4):
            for kind in ("inner-search", "inner-validation"):
                p = split_dir / f"OS-{os_i:02d}-B{b:02d}-{kind}.npy"
                if not p.exists():
                    missing.append(str(p))
                    ok = False
    # Verify each npy hash when recorded in the manifest.
    hash_mismatches = []
    for split in manifest.get("outer_splits", []):
        for key in ("train_file", "test_file"):
            fname = split.get(key)
            expected = split.get(f"{key}_sha256")
            if fname and expected:
                path = split_dir / fname
                got = sha256_file(path)
                if got != expected:
                    hash_mismatches.append({"file": fname, "expected": expected, "got": got})
        for bundle in split.get("bundles", []):
            for key in ("inner_search_file", "inner_validation_file"):
                fname = bundle.get(key)
                expected = bundle.get(fname.replace(".npy", "_sha256") if False else None)
            mapping = [
                ("inner_search_file", "inner_search_sha256"),
                ("inner_validation_file", "inner_validation_sha256"),
            ]
            for fkey, hkey in mapping:
                fname = bundle.get(fkey)
                expected = bundle.get(hkey)
                if fname and expected:
                    path = split_dir / fname
                    got = sha256_file(path)
                    if got != expected:
                        hash_mismatches.append({"file": fname, "expected": expected, "got": got})
    return {
        "manifest_sha256": combined,
        "manifest_expected_sha256": protocol.SPLIT_MANIFEST_SHA256,
        "missing_files": missing,
        "hash_mismatches": hash_mismatches,
        "duplicate_outer_split_hashes": manifest.get("duplicate_outer_split_hashes"),
        "status": "PASS"
        if ok
        and combined == protocol.SPLIT_MANIFEST_SHA256
        and not hash_mismatches
        and not manifest.get("duplicate_outer_split_hashes")
        else "BLOCKED",
    }


def verify_authority_docs(authority_dir: Path) -> dict:
    required = [
        "PySR_AUC-Stability_Evidence_Contract_OFFICIAL.md",
        "SR-Res_Act-1_Scientific-Claim_and_Closure-Record.md",
        "SR-Res_Scientific-Act-3_Validation-Protocol-and-A1-Decision-Package.md",
        "SRRES-ACT4-A4-COMBINED-EVIDENCE.tar.gz",
    ]
    present = {}
    for name in required:
        path = authority_dir / name
        present[name] = {
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "sha256": sha256_file(path) if path.exists() else None,
        }
    status = "PASS" if all(v["exists"] for v in present.values()) else "BLOCKED"
    return {"status": status, "files": present}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--act5-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--skip-backend", action="store_true")
    args = parser.parse_args()

    act5 = args.act5_root.resolve()
    run = args.run_root.resolve()
    evidence = run / "evidence" / "04-preflight"
    evidence.mkdir(parents=True, exist_ok=True)

    authority = act5 / "authority"
    repo = run / "train-pysr"
    env = run / "environment"
    # Act4 locks live under the original act4 evidence; path via ACT4_RUN_ROOT
    act4_root = Path((act5 / "ACT4_RUN_ROOT.txt").read_text(encoding="utf-8").strip())
    evidence_locks = act4_root / "evidence" / "03-environment-locks"
    split_dir = act4_root / "evidence" / "05-splits-and-seeds"
    split_manifest = split_dir / "seed-split-manifest.json"

    report: dict = {
        "started_utc": utc_now(),
        "protocol_id": protocol.PROTOCOL_ID,
        "training_executed": False,
        "model_metrics_accessed": False,
    }

    report["authority_docs"] = verify_authority_docs(authority)
    report["act4_archive"] = verify_act4_archive(authority)
    report["repo"] = verify_repo(repo)
    report["datasets"] = validate_datasets(repo)
    report["seeds"] = verify_seeds()
    report["locks"] = verify_locks(env, evidence_locks)
    report["python_versions"] = verify_python_versions()
    report["splits"] = verify_splits(split_dir, split_manifest)
    report["system"] = {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
    }

    if args.skip_backend:
        report["backend"] = {"status": "SKIPPED", "reason": "skip-backend flag"}
    else:
        # Ensure offline julia package resolution.
        os.environ.setdefault("PYTHON_JULIAPKG_OFFLINE", "yes")
        report["backend"] = verify_backend()

    sections = [
        "authority_docs",
        "act4_archive",
        "repo",
        "datasets",
        "seeds",
        "locks",
        "python_versions",
        "splits",
        "backend",
    ]
    blocked = [
        s
        for s in sections
        if report.get(s, {}).get("status") not in {"PASS", "SKIPPED"}
    ]
    report["blocked_sections"] = blocked
    report["status"] = "PASS" if not blocked else "BLOCKED"
    report["ended_utc"] = utc_now()

    dump_json(evidence / "preflight-report.json", report)
    print(json.dumps({"status": report["status"], "blocked_sections": blocked}, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
