# PySR Baseline Configuration

Status: **provisional, unverified, pending review**

This document is a technical handoff for human review. It is not a scientific
acceptance, physics interpretation, or authorization to start a fit.

## Environment and Panel

- PySR: `1.5.10`
- SymbolicRegression.jl: `1.11.3`
- Julia: `1.12.6`
- Editable panel: `configs/runs/masses_exclusions_pysr_baseline_v1.yaml`
- Switch registry: `configs/pysr/switch_registry.yaml`

Validate before Julia initialization:

```bash
python scripts/train_pysr_auc_search.py --config configs/runs/masses_exclusions_pysr_baseline_v1.yaml --dry-run
```

## Dataset, Target, Split, and Metrics

- Dataset id/path: `masses_exclusions` / `data/raw/masses_exclusions.csv`
- Input features: `mchi1, mchipm1`
- Target and positive label: `exclusion` / `1`
- Forbidden field: `Final_CLs`
- Split: `stratified`, test size `0.2`, seed `42`
- Weighting: `balanced`, fitted/applied to training rows only
- Fit loss: `loss(prediction, target, weight) = weight * (prediction - target)^2`
- Primary metric: ROC-AUC from saved continuous test scores
- Secondary metric: average precision from saved continuous test scores
- Integrity rule: recompute metrics independently from `pysr_test_scores.csv`; no reference model comparison

TODO: Confirm the physical meaning of labels 0 and 1 and the mass units with the thesis author/supervisor.

## Selected Preprocessing and Feature Policy

- Baseline feature set: `base`
- Baseline preprocessing: `raw`
- Configured reference scales (inactive for raw mode): `{"mass_gap": 1000.0, "mass_ratio": 1.0, "mchi1": 1000.0, "mchipm1": 1000.0}`
- Every fitted transform splits first and fits only on training rows.
- Frozen transformation metadata is saved and non-finite values are rejected.
- Available derived sets: base, base plus gap, base plus ratio, gap only, ratio only, and gap plus ratio.
- Reference-scale probes use explicit values and are not physical scale claims.

| Mode | Availability | Safety | Meaning |
| --- | --- | --- | --- |
| `raw` | supported | safe | Preserve input values exactly. |
| `standard` | supported | safe | Subtract the training mean and divide by the training population standard deviation. |
| `robust` | supported | safe | Subtract the training median and divide by the training interquartile range. |
| `dimensionless_reference` | supported | requires_physics_review | Divide every feature by a positive, explicitly recorded reference scale. |
| `log1p` | supported | requires_physics_review | Apply natural log(1 + x) after requiring non-negative inputs. |
| `log_reference` | supported | requires_physics_review | Apply natural log(x/reference) after requiring positive inputs and scales. |

## Operators and Search Budget

- Binary preset/operators: `polynomial` / `+, -, *`
- Unary preset/operators: `none` / `none`
- Custom preset: `none`
- Model selection: `best`
- Maximum expression size/depth: `40` / `None`
- Parsimony: `0.0`
- Iterations/populations/population size: `100` / `20` / `27`
- Timeout: `7200.0` seconds
- Precision: `32`

No unary operator is enabled by default.

## Runtime, Warm Start, and Output Policy

- Parallelism: `serial`
- Deterministic: `True` with random seed `42`
- Julia/JuliaCall threads: `1`; the observed count must match
- OMP/MKL/OpenBLAS threads: `1` / `1` / `1`
- Warm start: `False`
- Run id: `masses_exclusions_pysr_baseline_v1`
- Non-overwriting output: `outputs/runs/masses_exclusions_pysr_baseline_v1/`
- Output policy preset: `preserved_run_local`
- Workspace/temp directories are run-local.
- `temp_equation_file=false`; `delete_tempfiles=false`.

The discovery pass does not create the run output directory and does not call a fit.

## Complete Dial Table

| Group | Option | Availability | Safety | Default | Values / note |
| --- | --- | --- | --- | --- | --- |
| `preprocessing.mode` | `raw` | supported | safe | True | Preserve input values exactly. |
| `preprocessing.mode` | `standard` | supported | safe | False | Subtract the training mean and divide by the training population standard deviation. |
| `preprocessing.mode` | `robust` | supported | safe | False | Subtract the training median and divide by the training interquartile range. |
| `preprocessing.mode` | `dimensionless_reference` | supported | requires_physics_review | False | Divide every feature by a positive, explicitly recorded reference scale. |
| `preprocessing.mode` | `log1p` | supported | requires_physics_review | False | Apply natural log(1 + x) after requiring non-negative inputs. |
| `preprocessing.mode` | `log_reference` | supported | requires_physics_review | False | Apply natural log(x/reference) after requiring positive inputs and scales. |
| `preprocessing.feature_set` | `base` | supported | safe | True | mchi1, mchipm1 |
| `preprocessing.feature_set` | `base_plus_gap` | supported | requires_physics_review | False | mchi1, mchipm1, mass_gap |
| `preprocessing.feature_set` | `base_plus_ratio` | supported | requires_physics_review | False | mchi1, mchipm1, mass_ratio |
| `preprocessing.feature_set` | `gap_only` | supported | requires_physics_review | False | mass_gap |
| `preprocessing.feature_set` | `ratio_only` | supported | requires_physics_review | False | mass_ratio |
| `preprocessing.feature_set` | `gap_plus_ratio` | supported | requires_physics_review | False | mass_gap, mass_ratio |
| `operators.binary` | `additive` | supported | safe | False | +, - |
| `operators.binary` | `polynomial` | supported | safe | True | +, -, * |
| `operators.binary` | `rational` | supported | requires_physics_review | False | +, -, *, /; Evolved denominators can be zero or numerically small. |
| `operators.binary` | `power` | supported | unsafe | False | +, -, *, ^; General powers can leave the real finite domain. |
| `operators.unary` | `none` | supported | safe | True |  |
| `operators.unary` | `transcendental_candidates` | supported | unsafe | False | log, exp, tanh; log has a restricted domain and exp overflows on the observed raw mass range. |
| `operators.unary` | `tanh_only` | supported | safe | False | tanh |
| `operators.unary` | `log_only` | supported | requires_physics_review | False | log |
| `operators.unary` | `exp_only` | supported | unsafe | False | exp |
| `operators.unary` | `periodic_candidates` | supported | requires_physics_review | False | sin, cos; Periodicity has no reviewed physical interpretation for these features. |
| `operators.unary` | `singular_high_risk_candidates` | supported | unsafe | False | inv, sqrt, tan, coth; Contains singularities or restricted real domains. |
| `operators.custom` | `none` | supported | safe | True |  |
| `operators.custom` | `square` | supported | safe | False |  |
| `operators.custom` | `guarded_division` | supported | requires_physics_review | False | The fixed epsilon has unresolved dimensional meaning. |
| `training.sample_weight` | `none` | supported | safe | False |  |
| `training.sample_weight` | `balanced` | supported | safe | True |  |
| `training.sample_weight` | `manual_class_weights` | supported | requires_physics_review | False |  |
| `training.loss` | `weighted_squared_error` | supported | safe | True |  |
| `training.loss` | `unweighted_squared_error` | supported | safe | False |  |
| `training.loss` | `weighted_absolute_error` | supported | safe | False |  |
| `training.loss` | `unweighted_absolute_error` | supported | safe | False |  |
| `training.loss` | `direct_auc` | deferred | deferred | False | ROC-AUC is not an elementwise PySR loss in the current workflow. |
| `training.loss` | `binary_cross_entropy` | deferred | requires_physics_review | False | A reviewed score-to-probability link and stable loss definition are not available. |
| `search.model_selection` | `best` | supported | safe | True |  |
| `search.model_selection` | `accuracy` | supported | safe | False |  |
| `search.model_selection` | `score` | supported | safe | False |  |
| `search.complexity` | `maxsize` | supported | safe | 40 |  |
| `search.complexity` | `maxdepth` | supported | safe | None |  |
| `search.complexity` | `parsimony` | supported | safe | 0.0 |  |
| `search.complexity` | `complexity_of_operators` | supported | requires_physics_review | None |  |
| `search.complexity` | `constraints` | supported | requires_physics_review | None |  |
| `search.complexity` | `nested_constraints` | supported | requires_physics_review | None |  |
| `search.budget` | `niterations` | supported | safe | 100 |  |
| `search.budget` | `populations` | supported | safe | 20 |  |
| `search.budget` | `population_size` | supported | safe | 27 |  |
| `search.budget` | `timeout_in_seconds` | supported | safe | 7200 |  |
| `search.precision` | `16` | supported | unsafe | False | Reduced dynamic range is unsuitable for the first baseline. |
| `search.precision` | `32` | supported | safe | True |  |
| `search.precision` | `64` | supported | safe | False |  |
| `runtime.parallelism` | `serial` | supported | safe | True |  |
| `runtime.parallelism` | `multithreading` | supported | deferred | False | Scheduling and determinism cannot be validated without a separately authorized live fit. |
| `runtime.parallelism` | `multiprocessing` | supported | deferred | False | Process lifecycle and artifact isolation need a separately authorized live test. |
| `search.deterministic` | `true` | supported | safe | True |  |
| `search.deterministic` | `false` | supported | safe | False |  |
| `search.warm_start` | `false` | supported | safe | True |  |
| `search.warm_start` | `true` | supported | unsafe | False | A fresh baseline must not inherit a prior search state. |
| `output.policy` | `preserved_run_local` | supported | safe | True | Preserve run-local workspace and temporary files for review. |
| `output.policy` | `cleaned_run_local` | supported | safe | False | Keep final run artifacts but allow PySR to delete run-local temporary files. |
| `output.policy` | `external_temp` | deferred | deferred | False | External temporary paths would weaken the repo-local evidence boundary. |
| `output.policy` | `overwrite_existing` | supported | unsafe | False | Existing run evidence must never be overwritten. |
| `runtime` | `runtime_threads` | supported | safe | 1 |  |

## One-Dial Improvement Runs

Copy the baseline panel, assign a new run id and output directory, set
`experiment.parent_config` to the baseline or prior run config, and change one
registered dial. Validation ignores identity/output changes but rejects more
than one scientific/runtime dial change.

All future expressions, metrics, recommendations, and physics interpretations
remain provisional, unverified, and pending human review.
