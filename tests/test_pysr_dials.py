from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from pysr_dials import (  # noqa: E402
    build_feature_frame,
    fit_transform_preprocessor,
    load_and_resolve_config,
    load_yaml,
    one_dial_changes,
    resolve_panel,
    split_rows,
    validate_registry,
)
from discover_pysr_dials import (  # noqa: E402
    _operator_names,
    evaluate_operator_discovery,
)
from train_pysr_auc_search import (  # noqa: E402
    pysr_kwargs,
    runtime_settings_payload,
)


REGISTRY_PATH = REPO_ROOT / "configs/pysr/switch_registry.yaml"
PANEL_PATH = REPO_ROOT / "configs/runs/masses_exclusions_pysr_baseline_v1.yaml"
DATA_PATH = REPO_ROOT / "data/raw/masses_exclusions.csv"


class RegistryAndPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_yaml(REGISTRY_PATH)
        self.panel = load_yaml(PANEL_PATH)

    def test_registry_covers_required_switches(self) -> None:
        summary = validate_registry(self.registry)
        self.assertGreaterEqual(summary["classified_option_count"], 40)
        unary = self.registry["execution"]["unary_operator_presets"]
        self.assertIn("none", unary)
        self.assertIn("transcendental_candidates", unary)
        self.assertIn("periodic_candidates", unary)
        self.assertIn("singular_high_risk_candidates", unary)

    def test_baseline_resolves_to_no_unary_raw_panel(self) -> None:
        _, _, resolved = load_and_resolve_config(PANEL_PATH)
        self.assertEqual(resolved["preprocessing"]["mode"], "raw")
        self.assertEqual(resolved["model_features"], ["mchi1", "mchipm1"])
        self.assertEqual(resolved["pysr_options"]["unary_operators"], [])
        self.assertEqual(resolved["pysr_options"]["binary_operators"], ["+", "-", "*"])
        self.assertEqual(resolved["sample_weight_preset"], "balanced")
        self.assertEqual(
            resolved["output"]["output_dir"],
            "outputs/runs/masses_exclusions_pysr_baseline_v1/",
        )
        self.assertFalse(resolved["output"]["allow_overwrite"])

    def test_unsafe_choice_is_blocked(self) -> None:
        panel = copy.deepcopy(self.panel)
        panel["operators"]["unary_preset"] = "singular_high_risk_candidates"
        with self.assertRaisesRegex(ValueError, "Unsafe choice is blocked"):
            resolve_panel(panel, self.registry, config_path=PANEL_PATH)

    def test_output_must_stay_in_named_repo_run_directory(self) -> None:
        for invalid_path in ["/tmp/pysr-run", "outputs/pysr-run", "outputs/runs/../bad"]:
            panel = copy.deepcopy(self.panel)
            panel["output"]["output_dir"] = invalid_path
            with self.subTest(path=invalid_path), self.assertRaisesRegex(
                ValueError, "output.output_dir"
            ):
                resolve_panel(panel, self.registry, config_path=PANEL_PATH)

    def test_physics_review_choice_requires_acknowledgement(self) -> None:
        panel = copy.deepcopy(self.panel)
        panel["operators"]["binary_preset"] = "rational"
        with self.assertRaisesRegex(ValueError, "requires explicit review"):
            resolve_panel(panel, self.registry, config_path=PANEL_PATH)
        panel["operators"]["review_acknowledgements"] = ["operators.binary.rational"]
        _, resolved = resolve_panel(panel, self.registry, config_path=PANEL_PATH)
        self.assertIn("/", resolved["pysr_options"]["binary_operators"])

    def test_custom_square_resolves_definition_and_mapping(self) -> None:
        panel = copy.deepcopy(self.panel)
        panel["operators"]["custom_preset"] = "square"
        _, resolved = resolve_panel(panel, self.registry, config_path=PANEL_PATH)
        self.assertIn("square(x) = x * x", resolved["pysr_options"]["unary_operators"])
        self.assertEqual(resolved["custom_sympy_mappings"], ["square"])

    def test_review_gated_complexity_requires_acknowledgement(self) -> None:
        review_gated_values = {
            "complexity_of_operators": {"+": 2},
            "constraints": {"*": [1, 1]},
            "nested_constraints": {"sin": {"sin": 0}},
        }
        for name, value in review_gated_values.items():
            with self.subTest(name=name):
                panel = copy.deepcopy(self.panel)
                panel["search"]["complexity"][name] = value
                with self.assertRaisesRegex(ValueError, "requires explicit review"):
                    resolve_panel(panel, self.registry, config_path=PANEL_PATH)

                acknowledgement = f"search.complexity.{name}"
                panel["search"]["review_acknowledgements"] = [acknowledgement]
                _, resolved = resolve_panel(panel, self.registry, config_path=PANEL_PATH)
                self.assertEqual(resolved["pysr_options"][name], value)

    def test_manual_class_weights_must_be_finite(self) -> None:
        for invalid in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(invalid=invalid):
                panel = copy.deepcopy(self.panel)
                panel["training"]["sample_weight_preset"] = "manual_class_weights"
                panel["training"]["manual_class_weights"] = {0: 1.0, 1: invalid}
                panel["training"]["review_acknowledgements"] = [
                    "training.sample_weight.manual_class_weights"
                ]
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    resolve_panel(panel, self.registry, config_path=PANEL_PATH)

    def test_operator_discovery_fails_closed(self) -> None:
        all_names = _operator_names(self.registry, safe_only=False)
        live = {
            "initialized": True,
            "missing_constructor_dials": [],
            "requested_threads": 1,
            "observed_threads": 1,
            "unary": {
                name: {"compiled": True, "all_finite": True}
                for name in all_names["unary"]
            },
            "binary": {
                name: {"compiled": True, "all_finite": True}
                for name in all_names["binary"]
            },
        }
        passed = evaluate_operator_discovery(
            self.registry,
            fit_call_count=0,
            live=live,
            live_requested=True,
        )
        self.assertTrue(passed["passed"])

        live["unary"]["tanh"]["compiled"] = False
        failed_compile = evaluate_operator_discovery(
            self.registry,
            fit_call_count=0,
            live=live,
            live_requested=True,
        )
        self.assertFalse(failed_compile["passed"])
        self.assertIn("unary.tanh", failed_compile["failed_compilations"])

        live["unary"]["tanh"]["compiled"] = True
        live["unary"]["tanh"]["all_finite"] = False
        failed_domain = evaluate_operator_discovery(
            self.registry,
            fit_call_count=0,
            live=live,
            live_requested=True,
        )
        self.assertFalse(failed_domain["passed"])
        self.assertIn("unary.tanh", failed_domain["safe_domain_failures"])

        live["unary"]["tanh"]["all_finite"] = True
        del live["missing_constructor_dials"]
        malformed_live = evaluate_operator_discovery(
            self.registry,
            fit_call_count=0,
            live=live,
            live_requested=True,
        )
        self.assertFalse(malformed_live["passed"])
        self.assertFalse(malformed_live["constructor_dials_complete"])

    def test_custom_mapping_runtime_metadata_is_stable(self) -> None:
        panel = copy.deepcopy(self.panel)
        panel["operators"]["custom_preset"] = "square"
        _, resolved = resolve_panel(panel, self.registry, config_path=PANEL_PATH)
        with tempfile.TemporaryDirectory() as temporary_directory:
            kwargs = pysr_kwargs(resolved, Path(temporary_directory))
            payload = runtime_settings_payload(resolved, kwargs)
        rendered = json.dumps(payload, sort_keys=True)
        self.assertNotIn("0x", rendered)
        self.assertEqual(
            payload["extra_sympy_mappings"],
            {
                "square": {
                    "python_callable": "sympy_square",
                    "operator_definition": "square(x) = x * x",
                }
            },
        )

    def test_unsafe_output_policy_is_blocked(self) -> None:
        panel = copy.deepcopy(self.panel)
        panel["output"]["policy_preset"] = "overwrite_existing"
        with self.assertRaisesRegex(ValueError, "Unsafe choice is blocked"):
            resolve_panel(panel, self.registry, config_path=PANEL_PATH)

    def test_one_dial_diff_ignores_identity_and_output(self) -> None:
        candidate = copy.deepcopy(self.panel)
        candidate["run"]["run_id"] = "masses_exclusions_pysr_baseline_v2"
        candidate["output"]["output_dir"] = "outputs/runs/masses_exclusions_pysr_baseline_v2/"
        candidate["search"]["budget"]["niterations"] = 200
        changes = one_dial_changes(self.panel, candidate)
        self.assertEqual(changes, ["search.budget.niterations"])

    def test_one_dial_diff_ignores_required_review_metadata(self) -> None:
        candidate = copy.deepcopy(self.panel)
        candidate["run"]["run_id"] = "masses_exclusions_pysr_rational_v1"
        candidate["output"]["output_dir"] = "outputs/runs/masses_exclusions_pysr_rational_v1/"
        candidate["operators"]["binary_preset"] = "rational"
        candidate["operators"]["review_acknowledgements"] = ["operators.binary.rational"]
        changes = one_dial_changes(self.panel, candidate)
        self.assertEqual(changes, ["operators.binary_preset"])

        candidate = copy.deepcopy(self.panel)
        candidate["run"]["run_id"] = "masses_exclusions_pysr_constraints_v1"
        candidate["output"]["output_dir"] = (
            "outputs/runs/masses_exclusions_pysr_constraints_v1/"
        )
        candidate["search"]["complexity"]["constraints"] = {"*": [1, 1]}
        candidate["search"]["review_acknowledgements"] = [
            "search.complexity.constraints"
        ]
        changes = one_dial_changes(self.panel, candidate)
        self.assertEqual(changes, ["search.complexity.constraints.*"])


class PreprocessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = pd.read_csv(DATA_PATH)
        cls.registry, _, cls.resolved = load_and_resolve_config(PANEL_PATH)
        train_index, test_index, _ = split_rows(
            cls.data,
            target=cls.resolved["target"],
            positive_label=cls.resolved["positive_label"],
            test_size=cls.resolved["test_size"],
            random_seed=cls.resolved["random_seed"],
        )
        cls.raw_train = cls.data.loc[train_index]
        cls.raw_test = cls.data.loc[test_index]

    def test_all_feature_sets_and_modes_are_finite(self) -> None:
        for feature_set in self.registry["preprocessing"]["feature_sets"]:
            x_train = build_feature_frame(self.raw_train, feature_set)
            x_test = build_feature_frame(self.raw_test, feature_set)
            references = {
                name: 1.0 if "ratio" in name else 1000.0 for name in x_train.columns
            }
            for mode in self.registry["preprocessing"]["modes"]:
                with self.subTest(feature_set=feature_set, mode=mode):
                    train_out, test_out, metadata = fit_transform_preprocessor(
                        x_train,
                        x_test,
                        mode=mode,
                        reference_scales=references,
                    )
                    self.assertTrue(np.isfinite(train_out.to_numpy()).all())
                    self.assertTrue(np.isfinite(test_out.to_numpy()).all())
                    self.assertEqual(metadata["non_finite_policy"], "reject")

    def test_standard_and_robust_parameters_ignore_test_values(self) -> None:
        x_train = build_feature_frame(self.raw_train, "base")
        x_test = build_feature_frame(self.raw_test, "base")
        changed_test = x_test * 1000.0 + 99999.0
        for mode in ["standard", "robust"]:
            with self.subTest(mode=mode):
                _, _, metadata = fit_transform_preprocessor(x_train, x_test, mode=mode)
                _, _, changed_metadata = fit_transform_preprocessor(
                    x_train, changed_test, mode=mode
                )
                self.assertEqual(metadata["parameters"], changed_metadata["parameters"])
                self.assertEqual(metadata["train_index_sha256"], changed_metadata["train_index_sha256"])

    def test_nonfinite_values_are_rejected(self) -> None:
        x_train = build_feature_frame(self.raw_train, "base")
        x_test = build_feature_frame(self.raw_test, "base")
        x_test.iloc[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            fit_transform_preprocessor(x_train, x_test, mode="raw")

    def test_log_domain_is_rejected(self) -> None:
        x_train = pd.DataFrame({"x": [1.0, 2.0]}, index=[0, 1])
        x_test = pd.DataFrame({"x": [0.0]}, index=[2])
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            fit_transform_preprocessor(
                x_train,
                x_test,
                mode="log_reference",
                reference_scales={"x": 1.0},
            )

    def test_discovery_source_has_no_fit_call(self) -> None:
        source = (REPO_ROOT / "scripts/discover_pysr_dials.py").read_text(encoding="utf-8")
        self.assertNotIn(".fit(", source)


if __name__ == "__main__":
    unittest.main()
