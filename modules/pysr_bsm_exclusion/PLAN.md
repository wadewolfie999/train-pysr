# PySR Exclusion Baseline Plan

Status: **HISTORICAL PLAN — NON-CONTROLLING DURING REBUILD**

This plan preserves pre-REBUILD technical intent. Its inputs, work items,
metrics, and TODOs are not current execution requirements or accepted evidence.

## Objective

Stabilize a reviewed, reproducible PySR continuous-score workflow for the
`masses_exclusions` binary exclusion dataset. PySR remains the first backend in
the broader IDM symbolic-regression framework.

## Historical Inputs

- Dataset config: `configs/datasets/masses_exclusions.yaml`
- Raw dataset: `data/raw/masses_exclusions.csv`
- Base features: `mchi1`, `mchipm1`
- Target: `exclusion`
- Forbidden field: `Final_CLs`
- Editable baseline panel:
  `configs/runs/masses_exclusions_pysr_baseline_v1.yaml`
- Switch registry: `configs/pysr/switch_registry.yaml`

## Historical Work

- Classify preprocessing and PySR execution switches.
- Test transformation leakage and numerical domains without fitting PySR.
- Recommend conservative defaults with no unary operators.
- Prepare a new, non-overwriting run identity and output directory.
- Preserve saved continuous test labels/scores for independent metric checking.

## Evaluation Protocol

ROC-AUC is the primary metric and average precision is the secondary metric.
Both use continuous PySR scores. A future integrity command will recompute both
metrics from saved test artifacts without performing another fit.

## Boundaries

- No scientific fit occurs during dial discovery.
- Raw data and prior outputs are never overwritten.
- Derived features and physics-sensitive operators remain review-gated.
- Scientific conclusions and model-performance claims require thesis-author
  review.

## TODOs

- TODO: Confirm mass units.
- TODO: Confirm physical positive-label semantics.
- TODO: Obtain an exact A1-approved REBUILD contract before any fresh baseline
  fit.

Status: provisional, unverified, and pending review.
