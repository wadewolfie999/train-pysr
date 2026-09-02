# Data Directory

## Purpose

This directory contains repository data artifacts for the IDM
symbolic-regression workflow. Raw datasets are preserved unchanged.

## Data Directory Status

The current project phase is `REBUILD`. Earlier phase-acceptance statements
are historical and non-controlling. This data policy is provisional, unverified,
and pending A1 review. Data documentation does not by itself approve a dataset
for modeling. Source-domain pMSSM evidence does not establish target-domain IDM
or `Ht.csv` validity.

## Notebook-First Active Workflow

The active VS Code workflow uses three notebooks:

1. `notebooks/01_pysr_run.ipynb` loads and validates `masses_exclusions`,
   performs the guarded PySR run, and writes provenance plus continuous scores.
2. `notebooks/02_auc_analysis.ipynb` reads saved scores and computes ROC-AUC,
   average precision, ROC data, and separate threshold metrics.
3. `notebooks/03_supervisor_report.ipynb` reads the saved run and analysis
   artifacts for supervisor-facing presentation.

The current immutable dataset location remains `data/raw/`. This preserves
existing paths and historical provenance while keeping all repository datasets
under the single top-level `data/` namespace. No raw file is moved or
overwritten by the notebook workflow.

## Dataset Approval States

| Dataset ID | Raw path | Status | Approval state | Notes |
|---|---|---|---|---|
| `masses_exclusions` | `data/raw/masses_exclusions.csv` | Registered modeled dataset | `requires_review` | Existing configs record default features `mchi1`, `mchipm1` and binary target `exclusion`; unresolved review items remain. |
| `masses_exclusions2` | `data/raw/masses_exclusions2.csv` | Audit-only intake | `requires_review` | Related mass/exclusion schema with added `mhiggs`; not approved for modeling. |
| `ht` | `data/raw/Ht.csv` | Audit-only intake | `requires_review` | Distinct likelihood/parameter-style dataset with no assigned modeling target. |

## How To Add A Dataset

1. Place immutable raw data under `data/raw/` only when explicitly authorized.
2. Add or update a dataset registry/config under `configs/datasets/`.
3. Record observed columns, roles, units, target status, audit-only fields, and
   approval state.
4. Update `docs/DATA_CONTRACT.md`.
5. Add an audit report under `reports/dataset_audits/` when metadata or header
   inspection is available.
6. Keep the dataset blocked from modeling until review accepts its feature,
   target, unit, preprocessing, split, metric, and class-imbalance rules.

## Required Metadata Before Modeling

- Dataset id.
- Raw path.
- Provenance or `TODO: identify provenance`.
- Column inventory.
- Feature columns.
- Target column and target-label semantics.
- Units or `requires_review`.
- Audit-only columns.
- Missing-value policy.
- Preprocessing rules.
- Split rule and random seeds.
- Metric protocol.
- Class-imbalance strategy.
- Review status.

## Audit-Only Vs Modeling-Approved Data

Audit-only data may be inspected for schema, provenance, and review needs. It
must not be used for modeling claims.

Modeling-approved data require an accepted contract that records features,
targets, labels, units, preprocessing, split rules, metrics, and review status.
No current dataset is documented as fully modeling-approved.

## Raw Vs Processed Data Policy

Raw files must not be overwritten. Derived or processed datasets must be written
outside `data/raw/` and must include provenance, command, config, and review
records before modeling use.

## Large Or Ignored Data Policy

Ignored generated outputs remain non-source artifacts unless explicitly
promoted through review. Files under ignored output paths must not be treated as
accepted raw data or accepted results by default.

## Provenance Requirements

Each dataset must identify upstream generation, scan, nested-sampling, or
preprocessing provenance where known. Unknown provenance must be marked
`TODO: identify provenance`.

## Column And Target Documentation Requirements

Column names, units, roles, target semantics, and audit-only status must be
documented in `docs/DATA_CONTRACT.md` and the relevant dataset config.
`Final_CLs` remains audit-only unless explicitly reviewed and approved.

## Reproducibility Requirements

Run records must include dataset id, config id, raw path, feature set, target,
audit-only exclusions, preprocessing, split rule, random seed, metric protocol,
class-imbalance handling, command line, output path, and review status.

## Open TODOs

- TODO: confirm units and physics meaning for all dataset columns.
- TODO: confirm binary `exclusion` label semantics.
- TODO: identify nested-sampling or upstream scan provenance for current data.
- TODO: define approval criteria for promoting audit-only intake to modeling.
