# PySR / ML BSM Exclusion Workflow

## Project Summary

This repository supports a reproducible research workflow for PySR and standard
machine-learning surrogate modeling for binary BSM exclusion classification.
The active modeled dataset id is `masses_exclusions`, with raw data stored at
`data/raw/masses_exclusions.csv`.

Additional professor-provided raw datasets are currently in audit-only intake:

- `masses_exclusions2`: related mass/exclusion schema with an added `mhiggs`
  column.
- `ht`: separate likelihood/parameter-style dataset with no assigned modeling
  target.

These intake datasets are not approved for modeling yet.

The supervisor-facing report notebook is:

```text
notebooks/pysr_bsm_exclusion_report.ipynb
```

The workflow is intended to separate repository-side implementation,
configuration, verification, and review from scientific acceptance. PySR final
symbolic search has not yet been launched for the current candidate.

## Current Status

The current work is in a reproducible research layer before the final PySR
symbolic-search step. The current best approved-feature provisional result is:

```text
feature set / model: mass_engineered_v1 / hist_gradient_boosting_grid_01
fixed split: stratified, random_seed = 42
ROC-AUC: 0.9757422365348225
```

This ROC-AUC value was observed for the approved engineered-mass candidate on
the fixed seed-42 stratified split. Robustness across repeated splits and
cross-validation folds is not fully established.

No final thesis success, accepted physics interpretation, or accepted symbolic
model result is claimed here. All model results and supervisor-facing claims
remain provisional, unverified, and pending human/supervisor review.

## Dataset and Feature Policy

The approved base features are:

```text
mchi1
mchipm1
```

The target is binary `exclusion`.

`Final_CLs` is diagnostic/audit-only. It must not be used as an approved model
feature or target unless explicitly reviewed and approved. Diagnostic results
using `Final_CLs` are not thesis evidence.

ROC/AUC must be computed from continuous model scores, never from hard class
labels. Threshold-dependent metrics, if used, must be reported separately from
ROC/AUC.

Dataset conventions, units, target-label semantics, feature definitions,
preprocessing rules, split rules, metric protocols, and class-imbalance
strategies remain review-sensitive and should be declared in configuration or
registry files.

New raw datasets must enter through audit-only registry/config updates before
any target, feature set, split rule, metric, or training task is assigned.

## Reproducibility

Run definitions are organized through repository configs and scripts so that
inputs, feature sets, target definitions, split rules, class-imbalance handling,
metrics, and output paths can be reviewed and reproduced.

Representative commands:

```bash
python scripts/audit_dataset.py --config configs/runs/masses_exclusions_audit.yaml
python scripts/audit_dataset.py --config configs/runs/masses_exclusions2_audit.yaml
python scripts/audit_dataset.py --config configs/runs/ht_audit.yaml
python scripts/evaluate_strong_baselines.py --config configs/runs/masses_exclusions_strong_baselines.yaml
python scripts/evaluate_robustness.py --config configs/runs/masses_exclusions_robustness.yaml
python scripts/reproduce_auc97_candidate.py --config configs/runs/masses_exclusions_auc97_candidate.yaml
python scripts/train_pysr_auc_search.py --config configs/runs/masses_exclusions_pysr_search.yaml --dry-run
```

The PySR command above is a dry run. The final symbolic search should remain
blocked until the relevant dataset conventions, feature conventions,
validation protocol, and robustness status have been reviewed.

Ignored generated outputs may exist locally under:

```text
outputs/runs/
```

These generated outputs are not raw data and should not be treated as accepted
results unless reviewed.

## Repository Layout

```text
configs/     Dataset registry entries and run configurations.
data/raw/    Raw datasets; these should remain unchanged.
docs/        Workflow, conventions, review, and approval documentation.
modules/     Module-level plans, questions, and research notes.
notebooks/   Supervisor-facing and research-report notebooks.
outputs/     Ignored generated outputs and run artifacts.
scripts/     Audit, baseline, robustness, reproduction, and PySR scaffolding.
```

## Key Cautions

- Do not claim final thesis success from the current results.
- Do not claim PySR has produced final symbolic expressions for this candidate.
- Do not use `Final_CLs` as an approved feature or target.
- Do not compute ROC/AUC from hard labels.
- Do not overwrite raw data.
- Do not treat generated outputs as accepted evidence without review.
- Keep model results, physics interpretations, dataset conventions, and
  supervisor-facing claims marked provisional until human/supervisor review.

## AI-Assisted Workflow Note

Codex-CLI was used as a repo-side AI-assisted research workflow assistant to
support reproducible development. Its role included script scaffolding,
configuration organization, verification checks, Git-tracked checkpoints, and
implementation review within the repository workflow.

Codex was not treated as a scientific authority. All model results, physics
interpretations, dataset conventions, and supervisor-facing claims remain
provisional until reviewed and accepted by the thesis author and supervisor.
