#!/usr/bin/env python3
"""Predict outer-test continuous scores for a selected hall-of-fame equation.

Does not run a PySR search. Uses pysr.export_sympy.pysr2sympy and numpy lambdify.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sympy
from pysr.export_sympy import pysr2sympy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--equation-index", type=int, required=True)
    parser.add_argument("--x-path", type=Path, required=True)
    parser.add_argument("--feature-names", type=str, required=True)
    parser.add_argument("--out-path", type=Path, required=True)
    args = parser.parse_args()

    eq_path = args.attempt_dir / "equations_hall_of_fame.csv"
    if not eq_path.exists():
        print(f"missing equations file: {eq_path}", file=sys.stderr)
        return 2

    eqs = pd.read_csv(eq_path)
    if args.equation_index < 0 or args.equation_index >= len(eqs):
        print("equation index out of range", file=sys.stderr)
        return 2

    row = eqs.iloc[int(args.equation_index)]
    if "equation" in eqs.columns:
        expr_str = str(row["equation"])
    elif "Equation" in eqs.columns:
        expr_str = str(row["Equation"])
    else:
        expr_str = str(row.iloc[-1])

    feature_names = [n.strip() for n in args.feature_names.split(",") if n.strip()]
    x = np.load(args.x_path).astype(np.float64, copy=False)
    if x.ndim != 2 or x.shape[1] != len(feature_names):
        print(f"feature shape mismatch x={x.shape} names={feature_names}", file=sys.stderr)
        return 2

    try:
        expr = pysr2sympy(expr_str, feature_names_in=feature_names)
        symbols = [sympy.Symbol(name) for name in feature_names]
        fn = sympy.lambdify(symbols, expr, modules=["numpy"])
        cols = [x[:, i] for i in range(x.shape[1])]
        scores = np.asarray(fn(*cols), dtype=np.float64)
        if scores.ndim == 0:
            scores = np.full(x.shape[0], float(scores), dtype=np.float64)
        scores = np.asarray(scores, dtype=np.float64).reshape(-1)
        if scores.shape[0] != x.shape[0]:
            print("score length mismatch", file=sys.stderr)
            return 2
    except Exception as exc:  # noqa: BLE001
        print(f"expression evaluation failed: {exc}: {expr_str!r}", file=sys.stderr)
        return 2

    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out_path, scores.astype(np.float64))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
