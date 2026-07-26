# IDM Symbolic-Regression Research Framework

## Project Summary

This repository supports a thesis-oriented research workflow for symbolic
regression on Inert Doublet Model (IDM) dataset analysis.

The current project phase is `REBUILD`. Scientific Acts 1–9 and their
results are preserved as `DEPRECATED_HISTORICAL_SOURCE` and are not current
authority unless A1 separately re-ratifies an exact provision.

The repository contains a pre-REBUILD PySR-first binary exclusion workflow.
PySR remains the first symbolic-regression backend, not the project identity,
but no fit, search, metric production, or model execution is currently
authorized by the existence of that workflow.

The pre-REBUILD dataset registry records:

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

These intake datasets are not approved for modeling. Source-domain pMSSM
evidence must remain distinct from target-domain IDM evidence and from the
scientific validity or modeling status of `Ht.csv`.

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

Khosravi is another master's student supervised by E1 and provides the parallel
Neural-Network comparison arm in E1's broader SR-versus-NN framework. Any future
comparison must be prospectively specified, fair, and multi-metric, with common
datasets, splits, uncertainty reporting, computational-budget treatment, and
comparison criteria. No result transfers into SR-Res without a
provenance-preserving handoff; no method may be optimized against unknown test
outcomes or evaluated using metrics selected after observing results.

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

```text
REBUILD
```

No pre-REBUILD phase assignment, acceptance statement, configuration, command,
or artifact supplies current execution or scientific authority. New work
requires an exact A1-approved REBUILD contract.

## Current Scientific Status

Existing configs, reports, notebooks, logs, ignored outputs, and review-copy
scripts are preserved historical or provisional material. They are not promoted
into the REBUILD baseline or accepted as current evidence by this document.

No final thesis success, accepted physics interpretation, or accepted symbolic
model result is claimed here. All future model results and supervisor-facing
claims remain provisional, unverified, and pending human/supervisor review.

## Dataset and Feature Policy

The pre-REBUILD registry records the following default candidate features for
`masses_exclusions`; they are not re-ratified by this README:

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

Historical reproducibility command examples, not current execution authority:

```bash
python scripts/audit_dataset.py --config configs/runs/masses_exclusions_audit.yaml
python scripts/audit_dataset.py --config configs/runs/masses_exclusions2_audit.yaml
python scripts/audit_dataset.py --config configs/runs/ht_audit.yaml
python scripts/discover_pysr_dials.py --config configs/runs/masses_exclusions_pysr_baseline_v1.yaml --live-operator-check
python scripts/train_pysr_auc_search.py --config configs/runs/masses_exclusions_pysr_baseline_v1.yaml --dry-run
```

These commands are documentation only during REBUILD. Every fit, symbolic
search, metric-production run, or notebook execution remains blocked unless an
exact A1-approved contract authorizes it.

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

Codex/A4 is not a scientific authority. Technical validation is not scientific
acceptance. A1, Vahid Gorgin, alone records internal acceptance; E1 guidance
gains internal effect only through A1 interpretation or adoption.
