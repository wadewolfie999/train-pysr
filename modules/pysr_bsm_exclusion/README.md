# PySR BSM Exclusion Module

## Module Objective

This module organizes the current thesis topic: symbolic-regression and standard machine-learning surrogate modeling for binary BSM exclusion classification.

## Dataset Reference

The first registered dataset is `masses_exclusions`. It is not the only possible dataset for this module.

Dataset metadata is maintained in `configs/datasets/masses_exclusions.yaml`. Raw data is stored at `data/raw/masses_exclusions.csv` and must remain unchanged.

## Scientific Scope

The module will later compare PySR models and standard machine-learning baselines using ROC/AUC. ROC/AUC must be computed from continuous model scores, not hard class labels.

Scientific conclusions require review by the thesis author.

## Current Assumptions

- Default features: `mchi1`, `mchipm1`.
- Target: binary `exclusion`.
- `Final_CLs` is audit-only unless explicitly approved as a feature or target.
- Dataset-specific assumptions belong in dataset registry or configuration files.

## Out-Of-Scope Items

- Training models.
- Running notebooks.
- Producing plots or empirical results.
- Changing raw data.
- Inventing physics assumptions or citation claims.

## Review Status

This module scaffold is provisional, unverified, and pending review. No empirical performance is claimed yet.
