# Plans

## Current Roadmap Phase

Roadmap Phase 2 - Repo Governance Bootstrap.

## Current Project Summary

This repository supports a physics and particle phenomenology thesis workflow using PySR and standard machine-learning surrogate models for binary BSM exclusion classification.

The workflow is intended to be dataset-agnostic. Dataset-specific assumptions belong in dataset registry and configuration files. Runs should be config-driven.

## Registered Datasets

- `masses_exclusions`: first registered dataset.

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

- Review and accept or revise the governance files.
- Add or verify the raw dataset outside this governance task.
- Define the first reviewed config for `masses_exclusions`.
- Implement dataset audit tooling.
- Implement config-driven training and evaluation scripts.

## Backlog

- Add dataset audit report generation.
- Add PySR training entry point parameterized by dataset id and config id.
- Add ROC/AUC evaluation from continuous model scores.
- Add baseline ML comparison workflow.
- Add reproducible run logging.
- Add review records for accepted runs and rejected runs.
