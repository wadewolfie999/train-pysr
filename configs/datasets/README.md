# Dataset Config Conventions

## Purpose

This directory records dataset registry/config metadata for IDM
symbolic-regression work.

## Status

The current project phase is `REBUILD`. Earlier phase-acceptance statements
are historical and non-controlling. Dataset configs remain review-sensitive. A
config file does not approve a dataset for modeling or scientific execution.

## Current Dataset Configs

| Dataset ID | Config path | Raw path | Status |
|---|---|---|---|
| `masses_exclusions` | `configs/datasets/masses_exclusions.yaml` | `data/raw/masses_exclusions.csv` | Registered; approval state `requires_review`. |
| `masses_exclusions2` | `configs/datasets/masses_exclusions2.yaml` | `data/raw/masses_exclusions2.csv` | Audit-only intake; approval state `requires_review`. |
| `ht` | `configs/datasets/ht.yaml` | `data/raw/Ht.csv` | Audit-only intake; no assigned target. |

## Required Fields

Future dataset configs should record:

- `dataset_id`;
- raw path;
- observed schema;
- column roles;
- units or `requires_review`;
- feature columns;
- target column and label semantics;
- audit-only columns;
- missing-value status;
- preprocessing rules;
- split rules and random seeds;
- metric protocol;
- class-imbalance strategy;
- approval state;
- open questions.

## Activation Rule

Dataset configs are not active modeling approvals until
`docs/DATA_CONTRACT.md` approves the relevant dataset, feature set, target,
labels, units, preprocessing, split rule, metric protocol, and
class-imbalance strategy.

## Open TODOs

- TODO: confirm whether a stricter schema format is required.
- TODO: confirm naming conventions for future SymbolFit, Operon/C++, native
  C++, and native Rust dataset configs.
