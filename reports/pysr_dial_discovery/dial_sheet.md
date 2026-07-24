# PySR Dial Discovery Sheet

Status: **provisional, unverified, pending review**

## Boundary

This is a no-fit discovery record. It performs preprocessing, domain,
configuration, and installed-environment checks only. Fit calls observed:
`0`.

## Repository Baseline

- Dataset: `masses_exclusions`
- Target: `exclusion` with positive label `1`
- Baseline features: `mchi1, mchipm1`
- Excluded field: `Final_CLs`
- Split: stratified `80/20`, seed `42`
- Primary metric: ROC-AUC from continuous scores
- Secondary metric: average precision from continuous scores

## Discovery Results

- Preprocessing/domain cases passed: 48/48
- Leakage cases passed: 48/48
- All preprocessing modes rejected non-finite input: True
- Live Julia operator check: True
- Requested/observed Julia threads: 1 / 1

## Supported and Unsafe Option Table

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

## Recommended Next-Run Defaults

```yaml
{
  "preprocessing_mode": "raw",
  "feature_set": "base",
  "binary_operator_preset": "polynomial",
  "unary_operator_preset": "none",
  "custom_operator_preset": "none",
  "sample_weight_preset": "balanced",
  "loss_preset": "weighted_squared_error",
  "model_selection": "best",
  "maxsize": 40,
  "maxdepth": null,
  "parsimony": 0.0,
  "niterations": 100,
  "populations": 20,
  "population_size": 27,
  "timeout_in_seconds": 7200,
  "precision": 32,
  "parallelism": "serial",
  "deterministic": true,
  "warm_start": false,
  "runtime_threads": 1,
  "output_policy_preset": "preserved_run_local"
}
```

No unary operator is enabled by default. Derived features, periodic operators,
rational division, guarded division, and reference-based mass transforms remain
provisional and require explicit review. Unsafe and deferred choices are blocked.
