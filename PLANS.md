# Plans

## Current Roadmap Phase

Roadmap Phase 7 - Reproducible Research Layer.

## Current Project Summary

This repository supports a physics and particle phenomenology thesis workflow using PySR and standard machine-learning surrogate models for binary BSM exclusion classification.

The workflow is intended to be dataset-agnostic. Dataset-specific assumptions belong in dataset registry and configuration files. Runs should be config-driven.

## Registered Datasets

- `masses_exclusions`: first registered dataset.

## Active Modules

- `pysr_bsm_exclusion`: PySR and standard ML surrogate modeling for binary BSM exclusion classification.

## Current Phase 7 Deliverable

- Robustness validation before PySR after strong baselines observed AUC > 0.97 using approved engineered mass features.

## Supervisor Priorities For `masses_exclusions`

- Perform ROC/AUC analysis of the selected PySR model.
- Compute AUC from continuous scores, not hard class labels.
- Treat AUC > 0.97 as an aspirational target, not a claim unless proven by an actual run.
- Do not impose expression simplicity as an initial hard constraint.
- Allow larger PySR expressions if they improve AUC.
- Handle class imbalance explicitly and reproducibly.
- Compare PySR against standard ML baselines.

All recommendations in this file are provisional, unverified, and pending review.

## Immediate Next Steps

- Review robustness validation for approved engineered mass features.
- Keep PySR search blocked until robustness review is complete.
- Resolve open questions for units, label semantics, validation protocol, and baseline set.
- Define the first reviewed run config for `masses_exclusions`.
- Implement dataset audit tooling after scaffold review.
- Implement config-driven training and evaluation scripts after scaffold review.

## Backlog

- Add dataset audit report generation.
- Add PySR training entry point parameterized by dataset id and config id.
- Add ROC/AUC evaluation from continuous model scores.
- Add baseline ML comparison workflow.
- Add reproducible run logging.
- Add review records for accepted runs and rejected runs.
