# IDM Symbolic-Regression Research Framework

## Project Summary

This repository supports a thesis-oriented research workflow for symbolic
regression on Inert Doublet Model (IDM) dataset analysis.

The current repository contents were originally organized around PySR and
binary BSM exclusion modeling. In the new framing, PySR is the first symbolic-
regression backend, not the project identity. Existing PySR/BSM exclusion
work will be stabilized, reviewed, and generalized into a reproducible IDM
symbolic-regression framework.

The active modeled dataset id remains:

```text
masses_exclusions
```

The raw data path currently recorded for that dataset is:

```text
data/raw/masses_exclusions.csv
```

Additional professor-provided raw datasets are currently in audit-only intake:

- `masses_exclusions2`: related mass/exclusion schema with an added `mhiggs`
  column.
- `ht`: separate likelihood/parameter-style dataset with no assigned modeling
  target.

These intake datasets are not approved for modeling yet.

## Research Framing

The repository is being reframed as an IDM symbolic-regression framework with
multiple possible backends:

- PySR as the first backend to stabilize.
- SymbolFit as the next backend to mimic the reviewed PySR workflow.
- Operon/C++ as an exploratory later backend.
- Native C++ and native Rust as lower-priority exploratory implementations.

The repository should separate:

- upstream data generation or preprocessing;
- dataset and physics convention review;
- backend-specific symbolic-regression execution;
- reproducibility records and generated outputs;
- thesis-author and supervisor review.

Nested-sampling output, where relevant, is treated as upstream data generation
or preprocessing evidence, not as the symbolic-regression model itself.

## Workstreams

### Workstream I - Main Workstream

Workstream I is the thesis-critical path. It frames the repository, reviews the
data and physics conventions, triages the existing codebase, stabilizes the
PySR baseline, optimizes PySR, and then mimics the reviewed PySR workflow for
SymbolFit.

### Workstream II - Extra Workstream

Workstream II is exploratory and must not block Workstream I. It covers later
experiments with Operon/C++, native C++, and native Rust implementations.

Priority rule:

```text
Main Workstream > Operon Probe > Native C++ > Native Rust
```

## Current Phase

Current phase:

```text
Workstream I / Phase 0 - Repository Framing
```

Phase 0 is a documentation and planning phase. Its purpose is to align the
repository language and planning documents with the IDM symbolic-regression
framework before later data, physics, backend, or implementation work proceeds.

Phase 0 is not accepted or complete until the operator reviews the evidence and
explicitly accepts it.

## Current Scientific Status

The repository has existing provisional PySR/ML BSM exclusion scaffolding. The
current best approved-feature provisional result recorded before this framing
work is:

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

The approved base features currently recorded for `masses_exclusions` are:

```text
mchi1
mchipm1
```

The current target is binary `exclusion`.

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

Representative existing commands:

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
docs/        Workflow, conventions, review, and roadmap documentation.
modules/     Module-level plans, questions, and research notes.
notebooks/   Supervisor-facing and research-report notebooks.
outputs/     Ignored generated outputs and run artifacts.
scripts/     Audit, baseline, robustness, reproduction, and PySR scaffolding.
```

## Key Cautions

- Do not claim final thesis success from the current results.
- Do not claim PySR has produced final symbolic expressions for this candidate.
- Do not treat PySR as the whole project identity.
- Do not use `Final_CLs` as an approved feature or target.
- Do not compute ROC/AUC from hard labels.
- Do not overwrite raw data.
- Do not treat generated outputs as accepted evidence without review.
- Keep model results, physics interpretations, dataset conventions, and
  supervisor-facing claims marked provisional until human/supervisor review.
- Mark unknown project, data, or physics details as `TODO` rather than filling
  them with assumptions.

## AI-Assisted Workflow Note

Codex-CLI is a repo-side AI-assisted research workflow assistant. Its role can
include documentation, script scaffolding, configuration organization,
verification checks, Git-tracked checkpoints, and implementation review within
the repository workflow.

Codex is not a scientific authority. All model results, physics
interpretations, dataset conventions, and supervisor-facing claims remain
provisional until reviewed and accepted by the thesis author and supervisor.
