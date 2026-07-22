"""Dataset and frozen-split loading for Act 5."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import protocol
from .hashutil import sha256_file


def load_primary_frame(repo: Path) -> pd.DataFrame:
    path = repo / protocol.DATASET_PRIMARY["relative_path"]
    df = pd.read_csv(path)
    return df


def load_secondary_frame(repo: Path) -> pd.DataFrame:
    path = repo / protocol.DATASET_SECONDARY["relative_path"]
    df = pd.read_csv(path)
    return df


def validate_datasets(repo: Path) -> dict[str, Any]:
    primary_path = repo / protocol.DATASET_PRIMARY["relative_path"]
    secondary_path = repo / protocol.DATASET_SECONDARY["relative_path"]
    p = pd.read_csv(primary_path)
    s = pd.read_csv(secondary_path)
    result: dict[str, Any] = {"status": "PASS", "checks": []}

    def check(name: str, cond: bool, detail: Any = None) -> None:
        result["checks"].append({"name": name, "ok": bool(cond), "detail": detail})
        if not cond:
            result["status"] = "BLOCKED"

    check("primary_sha256", sha256_file(primary_path) == protocol.DATASET_PRIMARY["sha256"])
    check("secondary_sha256", sha256_file(secondary_path) == protocol.DATASET_SECONDARY["sha256"])
    check("primary_bytes", primary_path.stat().st_size == protocol.DATASET_PRIMARY["bytes"])
    check("secondary_bytes", secondary_path.stat().st_size == protocol.DATASET_SECONDARY["bytes"])
    check("primary_rows", len(p) == protocol.DATASET_PRIMARY["rows"])
    check("secondary_rows", len(s) == protocol.DATASET_SECONDARY["rows"])
    check("primary_columns", list(p.columns) == protocol.DATASET_PRIMARY["columns"])
    check("secondary_columns", list(s.columns) == protocol.DATASET_SECONDARY["columns"])
    check("primary_class_counts", p["exclusion"].value_counts().to_dict() == {0: 2263, 1: 10017})
    check("secondary_class_counts", s["exclusion"].value_counts().to_dict() == {0: 2263, 1: 10017})
    check("primary_missing", int(p.isna().sum().sum()) == 0)
    check("secondary_missing", int(s.isna().sum().sum()) == 0)
    check("primary_inf", int(np.isinf(p.select_dtypes(include=[np.number])).sum().sum()) == 0)
    check("secondary_inf", int(np.isinf(s.select_dtypes(include=[np.number])).sum().sum()) == 0)
    check("primary_dup_rows", int(p.duplicated().sum()) == 0)
    check("secondary_dup_rows", int(s.duplicated().sum()) == 0)
    check(
        "primary_dup_features",
        int(p[["mchi1", "mchipm1"]].duplicated().sum()) == 0,
    )
    check(
        "secondary_dup_features",
        int(s[["mchi1", "mchipm1", "mhiggs"]].duplicated().sum()) == 0,
    )
    check("primary_cls_truth", bool(((p["Final_CLs"] < 0.05) == (p["exclusion"] == 0)).all()))
    check("secondary_cls_truth", bool(((s["Final_CLs"] < 0.05) == (s["exclusion"] == 0)).all()))
    common = ["mchi1", "mchipm1", "Final_CLs", "exclusion"]
    check("common_row_identity", p[common].equals(s[common]))
    return result


def build_feature_matrix(df: pd.DataFrame, arm: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    y = df[protocol.TARGET].to_numpy(dtype=np.float64)
    if arm == "PRIMARY":
        x = np.column_stack(
            [
                df["mchi1"].to_numpy(dtype=np.float64) / protocol.SCALE,
                df["mchipm1"].to_numpy(dtype=np.float64) / protocol.SCALE,
            ]
        )
        names = list(protocol.DATASET_PRIMARY["feature_names"])
    elif arm == "SECONDARY":
        x = np.column_stack(
            [
                df["mchi1"].to_numpy(dtype=np.float64) / protocol.SCALE,
                df["mchipm1"].to_numpy(dtype=np.float64) / protocol.SCALE,
                df["mhiggs"].to_numpy(dtype=np.float64) / protocol.SCALE,
            ]
        )
        names = list(protocol.DATASET_SECONDARY["feature_names"])
    else:
        raise ValueError(f"unknown arm {arm}")
    if protocol.PROHIBITED_FEATURE in names:
        raise RuntimeError("Final_CLs leaked into feature names")
    return x, y, names


def class_weights(y_search: np.ndarray) -> np.ndarray:
    """w(c) = n / (2 * n_c) computed only on inner-search labels."""
    y = y_search.astype(np.int64)
    n = float(len(y))
    weights = np.empty(len(y), dtype=np.float64)
    for c in (0, 1):
        n_c = float(np.sum(y == c))
        if n_c <= 0:
            raise RuntimeError(f"class {c} absent from inner-search partition")
        weights[y == c] = n / (2.0 * n_c)
    return weights


def load_index_array(path: Path) -> np.ndarray:
    arr = np.load(path)
    if arr.ndim != 1:
        raise ValueError(f"index array must be 1-D: {path}")
    return arr.astype(np.int64, copy=False)


def row_ids_from_indices(indices: np.ndarray) -> list[str]:
    return [f"pmssm-{int(i):05d}" for i in indices]
