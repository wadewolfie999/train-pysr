# PySR Baseline Stabilization Plan

This file is a repository-local synchronization of the current A1-authorized
technical direction. It does not independently approve scientific conclusions,
physics interpretations, phase gates, or model results. Human review remains
required.

## Current Authorized Sequence

1. Audit the current `train-pysr` repository, environment, configs, and local
   PySR artifacts.
2. Discover and classify preprocessing and PySR execution switches without
   performing a scientific fit.
3. Validate split-first, training-only preprocessing and operator-domain safety.
4. Produce a human-editable baseline panel and complete configuration handoff.
5. Record operator acceptance of the discovery evidence and proposed defaults.
6. Run one separately authorized fresh baseline fit.
7. Recompute ROC-AUC and average precision independently from saved continuous
   test scores.
8. Improve PySR through new, non-overwriting, one-dial-at-a-time runs.

Steps 1 through 5 were accepted and integrated by the operator. This acceptance
establishes technical readiness only: step 6 remains separately unauthorized,
and the repository must still stop before any call to `PySRRegressor.fit`.

## Baseline Configuration Candidate

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

These defaults are accepted as the technical baseline configuration. This does
not accept a scientific conclusion, physics interpretation, or model result.

## Dial Discovery Requirements

The registry and editable panel must cover raw, standard, robust,
reference-scaled, log, mass-gap, and mass-ratio preprocessing; operators, loss,
weights, selection, complexity, budget, precision, parallelism, determinism,
warm start, threads, and output policy.

Every option records availability and safety independently. Unsafe and deferred
choices are blocked. Physics-review choices require an explicit acknowledgement.
No unary operator is enabled by default.

## Reproducibility and Integrity

- Split rows before deriving or fitting any transformation.
- Fit transformation statistics on training rows only and freeze them for test
  rows.
- Reject non-finite inputs and outputs.
- Save exact transformation metadata, config identity, dataset identity, seed,
  features, target, operators, loss, runtime settings, and output paths.
- Never overwrite raw data, existing run artifacts, or previous run directories.
- Independently validate saved labels and continuous scores after a future fit;
  this validation is not a second fit.

## Review-Sensitive TODOs

- TODO: Confirm physical units for `mchi1` and `mchipm1`.
- TODO: Confirm the physical meaning of `exclusion` values 0 and 1.
- TODO: Review any physical interpretation of mass gaps, mass ratios, periodic
  functions, singular functions, or reference scales before enabling them.
- TODO: Obtain separate A1 authorization before launching the fresh baseline fit.

All discovery results, defaults, future expressions, and future metrics remain
provisional, unverified, and pending human review.
