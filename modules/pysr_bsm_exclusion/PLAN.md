# Research Plan

## Objective

Develop a reviewed, reproducible comparison between PySR symbolic-regression models and standard machine-learning baselines for binary BSM exclusion classification.

## Inputs

- Module id: `pysr_bsm_exclusion`
- First dataset id: `masses_exclusions`
- Dataset registry: `configs/datasets/masses_exclusions.yaml`
- Raw dataset: `data/raw/masses_exclusions.csv`
- Default features: `mchi1`, `mchipm1`
- Target: binary `exclusion`

## Planned Outputs

- Reviewed run configurations.
- PySR model outputs and recorded expressions.
- Standard ML baseline outputs.
- ROC/AUC evaluation reports.
- Secondary threshold-dependent metric reports when approved.
- Run logs with reproducibility metadata.

## Evaluation Protocol

ROC/AUC must be computed from continuous model scores, not hard class labels.

Accuracy and confusion matrices may be reported only as threshold-dependent secondary metrics.

AUC > 0.97 is a target, not an achieved result unless produced by an actual reviewed run.

## PySR Track

- Use the reviewed dataset registry and run configuration.
- Use only approved features and target definitions.
- Record expression, score source, seed, split, metrics, and output path.
- Allow PySR expressions to grow if AUC improves, because expression simplicity is not the initial hard constraint.

## ML Baseline Track

Standard ML baselines should use the same dataset split, features, target, and metric protocol as PySR.

Baseline choices require review before supervisor-facing comparison.

## Reproducibility Requirements

- Class imbalance handling must be declared per run.
- Run config, seed, dataset version/path, feature set, target, metrics, and output path must be recorded.
- Raw data must remain unchanged.
- Prior generated outputs must not be overwritten.

## Acceptance Criteria

No result is accepted unless the run config, seed, dataset version/path, feature set, target, metrics, and output path are recorded.

Scientific conclusions, physics interpretations, citation claims, and model-performance claims require thesis-author review.

## Immediate Next Steps

- Review this module scaffold.
- Resolve required open questions for units, labels, validation protocol, and baseline set.
- Define reviewed run configuration files before implementing scripts.

This plan is provisional, unverified, and pending review.
