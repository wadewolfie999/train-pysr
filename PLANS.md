# Historical PySR Baseline Stabilization Plan

Status: **HISTORICAL — `DEPRECATED_HISTORICAL_SOURCE`**

This file preserves a pre-REBUILD technical plan and its recorded review state.
It is not current authority, does not re-ratify any Scientific Act 1–9
provision, and does not authorize fitting, metric production, search, evidence
acceptance, phase transition, verdict, closure, or LOCK. Reuse requires an exact
A1-approved REBUILD contract.

## Historical Sequence

The pre-REBUILD record described this sequence:

1. Audit the `train-pysr` repository, environment, configs, and local PySR
   artifacts.
2. Discover and classify preprocessing and PySR execution switches without
   performing a scientific fit.
3. Perform technical validation of split-first, training-only preprocessing and
   operator-domain safety.
4. Produce a human-editable baseline panel and complete configuration handoff.
5. Record operator review of the discovery evidence and proposed defaults.
6. Run one separately authorized fresh baseline fit.
7. Recompute ROC-AUC and average precision independently from saved continuous
   test scores.
8. Improve PySR through new, non-overwriting, one-dial-at-a-time runs.

The historical record states that steps 1 through 5 received technical review.
That historical review is not current evidence acceptance or execution authority.
No step in this sequence is active during REBUILD without a new exact A1
contract.

## Historical Baseline Configuration Candidate

- Dataset: `masses_exclusions`
- Raw path: `data/raw/masses_exclusions.csv`
- Base features: `mchi1`, `mchipm1`
- Target: binary `exclusion`
- Configured positive label: `1`
- Forbidden field: `Final_CLs`
- Split: stratified 80/20, seed 42
- Preprocessing: raw base features
- Class handling: balanced sample weights computed on training labels only
- Fit loss: weighted squared-error continuous-score surrogate
- Primary metric: ROC-AUC from continuous scores
- Secondary metric: average precision from continuous scores
- Binary operators: `+`, `-`, `*`
- Unary and custom operators: none
- Runtime: serial, deterministic, one Julia/JuliaCall thread
- Warm start: disabled
- Output: new run identity and non-overwriting run-local directories

These values are preserved as a historical candidate, not as a current accepted
baseline, scientific conclusion, physics interpretation, or model result.

## Historical Dial-Discovery Requirements

The recorded registry and editable panel covered raw, standard, robust,
reference-scaled, log, mass-gap, and mass-ratio preprocessing; operators, loss,
weights, selection, complexity, budget, precision, parallelism, determinism,
warm start, threads, and output policy.

The record classified availability and safety independently, blocked unsafe and
deferred choices, required acknowledgement for physics-review choices, and
enabled no unary operator by default. These are historical technical statements,
not current execution requirements.

## Reproducibility and Preservation

- Preserve the historical configs, reports, outputs, and provenance unchanged.
- Do not promote historical technical validation into scientific acceptance.
- Do not use historical results as current evidence without an explicit,
  provenance-preserving A1 handoff.
- Any future execution must use a new, non-overwriting run identity under an
  exact A1-approved REBUILD contract.

## Review-Sensitive TODOs

- TODO: Confirm physical units for `mchi1` and `mchipm1`.
- TODO: Confirm the physical meaning of `exclusion` values 0 and 1.
- TODO: Review any physical interpretation of mass gaps, mass ratios, periodic
  functions, singular functions, or reference scales before enabling them.
- TODO: Define a prospective, fair, multi-metric SR-versus-NN comparison before
  inspecting comparison outcomes.

All historical discovery results, defaults, expressions, and metrics remain
non-controlling and pending any future A1 review or re-ratification.
