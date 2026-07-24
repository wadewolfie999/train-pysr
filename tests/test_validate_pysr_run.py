from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts/validate_pysr_run.py"


class IndependentMetricValidatorTests(unittest.TestCase):
    def build_run(self, run_dir: Path) -> None:
        labels = [0, 0, 1, 1]
        scores = [0.1, 0.4, 0.6, 0.9]
        frame = pd.DataFrame(
            {
                "row_index": [10, 11, 12, 13],
                "split_membership": ["test"] * 4,
                "mchi1": [100.0, 200.0, 300.0, 400.0],
                "mchipm1": [150.0, 250.0, 350.0, 450.0],
                "y_true": labels,
                "score": scores,
                "score_source": ["PySRRegressor.predict_continuous_score"] * 4,
                "positive_label": [1] * 4,
                "model_feature_mchi1": [100.0, 200.0, 300.0, 400.0],
                "model_feature_mchipm1": [150.0, 250.0, 350.0, 450.0],
            }
        )
        frame.to_csv(run_dir / "pysr_test_scores.csv", index=False)
        self.write_json(
            run_dir / "pysr_metrics.json",
            {
                "score_source": "PySRRegressor.predict_continuous_score",
                "auc_rule": "continuous_scores_only",
                "roc_auc": roc_auc_score(labels, scores),
                "average_precision": average_precision_score(labels, scores),
            },
        )
        self.write_json(
            run_dir / "pysr_run_metadata.json",
            {
                "run_id": "fixture",
                "target": "exclusion",
                "base_features": ["mchi1", "mchipm1"],
            },
        )
        self.write_json(
            run_dir / "pysr_environment.json",
            {
                "julia_backend_initialized": True,
                "julia": {
                    "threads": 1,
                    "version": "1.12.6",
                    "symbolic_regression_version": "1.11.3",
                },
            },
        )
        self.write_json(
            run_dir / "pysr_runtime_settings.json",
            {"requested_environment": {"julia_threads": 1}},
        )
        self.write_json(
            run_dir / "pysr_preprocessing.json",
            {"fit_scope": "no_test_fit", "non_finite_policy": "reject"},
        )
        self.write_json(run_dir / "pysr_git_state.json", {"head": "abc", "is_clean": True})
        self.write_json(run_dir / "pysr_artifact_manifest.json", {"artifacts": []})
        (run_dir / "pysr_equations.csv").write_text("equation\nx0\n", encoding="utf-8")
        (run_dir / "pysr_roc_curve_data.csv").write_text("fpr,tpr,threshold\n", encoding="utf-8")
        (run_dir / "pysr_model.pkl").write_bytes(b"not loaded by validator")
        (run_dir / "pysr_stdout_stderr.log").write_text("fixture\n", encoding="utf-8")

    @staticmethod
    def write_json(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

    def run_validator(self, run_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--run-dir", str(run_dir)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_recomputes_auc_and_average_precision_without_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            self.build_run(run_dir)
            result = self.run_validator(run_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["validation_status"], "passed")
            self.assertFalse(payload["fit_performed_by_validator"])
            self.assertFalse(payload["reference_model_comparison_performed"])

    def test_rejects_obsolete_reference_comparison_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            self.build_run(run_dir)
            metrics_path = run_dir / "pysr_metrics.json"
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            metrics["reference_model_auc"] = 0.99
            self.write_json(metrics_path, metrics)
            result = self.run_validator(run_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Obsolete reference-comparison metrics", result.stderr)


if __name__ == "__main__":
    unittest.main()

