#!/usr/bin/env python3
"""Create diagnostic mass-plane plots for label and baseline-error inspection."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "provisional, unverified, pending review"
PLOT_FILES = (
    "mass_plane_labels.png",
    "mass_plane_final_cls.png",
    "mass_plane_best_approved_errors.png",
    "mass_plane_plot_metadata.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot mass-plane diagnostics.")
    parser.add_argument("--config", required=True, help="Path to strong-baseline config.")
    parser.add_argument(
        "--metrics-dir",
        help="Directory containing strong baseline outputs. Defaults to config output_dir.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing diagnostic plot files.",
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


def prepare_outputs(output_dir: Path, overwrite: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [output_dir / name for name in PLOT_FILES if (output_dir / name).exists()]
    if existing and not overwrite:
        paths = ", ".join(str(path) for path in existing)
        raise SystemExit(f"Refusing to overwrite existing diagnostic plots: {paths}")
    if overwrite:
        for path in existing:
            path.unlink()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    output_dir = Path(args.metrics_dir) if args.metrics_dir else Path(config["output_dir"])
    prepare_outputs(output_dir, args.overwrite)

    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("pandas and matplotlib are required for diagnostic plots.") from exc

    data = pd.read_csv(config["raw_path"])
    required = {"mchi1", "mchipm1", config["target"]}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing required plotting columns: {missing}")

    label_path = output_dir / "mass_plane_labels.png"
    plt.figure(figsize=(7, 6))
    scatter = plt.scatter(
        data["mchi1"],
        data["mchipm1"],
        c=data[config["target"]],
        s=8,
        alpha=0.7,
        cmap="coolwarm",
    )
    plt.xlabel("mchi1")
    plt.ylabel("mchipm1")
    plt.title("Label distribution in mass plane - provisional")
    plt.colorbar(scatter, label=config["target"])
    plt.tight_layout()
    plt.savefig(label_path, dpi=160)
    plt.close()

    final_cls_path = None
    if "Final_CLs" in data.columns:
        final_cls_path = output_dir / "mass_plane_final_cls.png"
        plt.figure(figsize=(7, 6))
        scatter = plt.scatter(
            data["mchi1"],
            data["mchipm1"],
            c=data["Final_CLs"],
            s=8,
            alpha=0.7,
            cmap="viridis",
        )
        plt.xlabel("mchi1")
        plt.ylabel("mchipm1")
        plt.title("Final_CLs diagnostic in mass plane - provisional")
        plt.colorbar(scatter, label="Final_CLs diagnostic only")
        plt.tight_layout()
        plt.savefig(final_cls_path, dpi=160)
        plt.close()

    error_plot_path = None
    metrics_path = output_dir / "strong_metrics.csv"
    predictions_path = output_dir / "strong_predictions.csv"
    if metrics_path.exists() and predictions_path.exists():
        metrics = pd.read_csv(metrics_path)
        approved = metrics[
            (metrics["status"] == "completed") & (metrics["diagnostic"].astype(str) == "False")
        ].copy()
        if not approved.empty:
            approved = approved.sort_values("roc_auc", ascending=False)
            best = approved.iloc[0]
            predictions = pd.read_csv(predictions_path)
            selected = predictions[
                (predictions["feature_set"] == best["feature_set"])
                & (predictions["model_variant"] == best["model_variant"])
            ].copy()
            if not selected.empty and selected["predicted_label_if_probability_like"].notna().any():
                selected = selected.merge(
                    data[["mchi1", "mchipm1"]],
                    left_on="row_index",
                    right_index=True,
                    how="left",
                )
                selected["is_error"] = (
                    selected["predicted_label_if_probability_like"].astype(int)
                    != selected["y_true"].astype(int)
                )
                error_plot_path = output_dir / "mass_plane_best_approved_errors.png"
                plt.figure(figsize=(7, 6))
                scatter = plt.scatter(
                    selected["mchi1"],
                    selected["mchipm1"],
                    c=selected["is_error"].astype(int),
                    s=12,
                    alpha=0.75,
                    cmap="coolwarm",
                )
                plt.xlabel("mchi1")
                plt.ylabel("mchipm1")
                plt.title(
                    "Best approved baseline threshold errors - provisional\n"
                    f"{best['feature_set']} / {best['model_variant']}"
                )
                plt.colorbar(scatter, label="1 = threshold error")
                plt.tight_layout()
                plt.savefig(error_plot_path, dpi=160)
                plt.close()

    metadata = {
        "status": STATUS,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "dataset_path": config["raw_path"],
        "output_dir": str(output_dir),
        "plots": {
            "label_distribution": str(label_path),
            "final_cls_diagnostic": str(final_cls_path) if final_cls_path else None,
            "best_approved_errors": str(error_plot_path) if error_plot_path else None,
        },
        "notes": [
            "Raw data was read only and not modified.",
            "Plots are diagnostic only and do not infer physics conclusions.",
            "Final_CLs plot is diagnostic only and not thesis-accepted evidence.",
        ],
    }
    with (output_dir / "mass_plane_plot_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Wrote mass-plane diagnostics to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
