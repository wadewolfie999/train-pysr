# IDM Dataset Contract

## Purpose

This document is the central data contract for IDM symbolic-regression work.
It records observed repository facts, review states, and open TODOs before
PySR baseline stabilization or later backend comparison.

## Current Status

Phase 0 - Repository Framing is explicitly accepted. This Phase 1 contract is
provisional, unverified, and pending review. Documentation here does not by
itself approve a dataset, feature, target, unit, label meaning, preprocessing
rule, split rule, metric protocol, or class-imbalance strategy for modeling.

## Dataset Registry

| Dataset ID | Path | Status | Purpose | Approval state | Notes |
|---|---|---|---|---|---|
| `masses_exclusions` | `data/raw/masses_exclusions.csv` | Registered modeled dataset | Existing binary exclusion workflow and first PySR candidate dataset | `requires_review` | Default features and target are recorded in `configs/datasets/masses_exclusions.yaml`; scientific semantics remain review-sensitive. |
| `masses_exclusions2` | `data/raw/masses_exclusions2.csv` | Audit-only intake | Related mass/exclusion schema with added `mhiggs` | `requires_review` | Not approved for modeling; feature and target roles are provisional. |
| `ht` | `data/raw/Ht.csv` | Audit-only intake | Distinct likelihood/parameter-style dataset | `requires_review` | No assigned modeling target or approved feature set. |

## Dataset Approval States

| Approval state | Meaning | Modeling use |
|---|---|---|
| `requires_review` | Repository has metadata, but human/supervisor review is still required. | Blocked until review resolves required TODOs. |
| `audit-only intake` | Dataset may be inspected for schema and provenance only. | Not allowed for modeling tasks. |
| `registered modeled dataset` | Dataset has a registered config and existing modeled workflow. | Allowed only through reviewed configs and still subject to unresolved TODOs. |
| `modeling-approved` | Dataset contract, features, target, labels, units, preprocessing, splits, and metrics are reviewed. | No current dataset is documented at this state. |

## File And Path Inventory

| Path | Artifact class | Observed status | Notes |
|---|---|---|---|
| `data/raw/masses_exclusions.csv` | Raw data | Registered | Header observed: `mchi1`, `mchipm1`, `Final_CLs`, `exclusion`. |
| `data/raw/masses_exclusions2.csv` | Raw data | Audit-only intake | Header observed: `mhiggs`, `mchi1`, `mchipm1`, `Final_CLs`, `exclusion`. |
| `data/raw/Ht.csv` | Raw data | Audit-only intake | Header observed: `Prob`, `logLik`, `M_S`, `M_R`, `M_Y`, `laL`, `omega`, `invBr`, `lilithLogl`, `PsiCross`, `vctc`, `logM_S`, `logM_R`, `delMA`, `delMC`, `logvt`, `Chi2`. |
| `configs/datasets/masses_exclusions.yaml` | Dataset config | Registered | Records default features, binary target, audit-only `Final_CLs`, and review TODOs. |
| `configs/datasets/masses_exclusions2.yaml` | Dataset config | Audit-only intake metadata | Records candidate columns and provisional target state requiring review. |
| `configs/datasets/ht.yaml` | Dataset config | Audit-only intake metadata | Records unassigned columns and no target. |
| `configs/runs/*.yaml` | Run or audit config | Config | Existing configs reference audit, baseline, robustness, candidate, and PySR smoke/search workflows. |

## Column Inventory

| Column | Observed in | Role | Unit | Meaning | Approval state | Notes |
|---|---|---|---|---|---|---|
| `mchi1` | `masses_exclusions`, `masses_exclusions2` | Default feature in `masses_exclusions`; candidate feature in `masses_exclusions2` | `requires_review` | TODO: confirm with supervisor | `requires_review` | Recorded in configs. |
| `mchipm1` | `masses_exclusions`, `masses_exclusions2` | Default feature in `masses_exclusions`; candidate feature in `masses_exclusions2` | `requires_review` | TODO: confirm with supervisor | `requires_review` | Recorded in configs. |
| `mhiggs` | `masses_exclusions2` | Candidate feature requiring review | `requires_review` | TODO: confirm with supervisor | `requires_review` | Not approved for modeling. |
| `Final_CLs` | `masses_exclusions`, `masses_exclusions2` | Audit-only diagnostic | `requires_review` | TODO: confirm with supervisor | Audit-only unless explicitly approved | Must not be used as feature or target without review. |
| `exclusion` | `masses_exclusions`, `masses_exclusions2` | Target in `masses_exclusions`; provisional target in `masses_exclusions2` | Not applicable | Binary label semantics require review | `requires_review` | Unique values documented as `0` and `1` in configs. |
| `Prob` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `logLik` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `M_S` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `M_R` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `M_Y` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `laL` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `omega` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `invBr` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `lilithLogl` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `PsiCross` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `vctc` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `logM_S` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `logM_R` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `delMA` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `delMC` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `logvt` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |
| `Chi2` | `ht` | Unassigned | `requires_review` | TODO: confirm with supervisor | `requires_review` | No modeling role assigned. |

## Feature Columns

| Dataset ID | Approved/default features | Provisional features | Unknown or unassigned features |
|---|---|---|---|
| `masses_exclusions` | `mchi1`, `mchipm1` | Derived mass features appear in run configs and require review before being treated as general contract defaults. | None documented. |
| `masses_exclusions2` | None | `mhiggs`, `mchi1`, `mchipm1` | None documented. |
| `ht` | None | None | All observed columns require review before any feature role is assigned. |

## Target Columns

| Dataset ID | Target column | Target type | Label semantics | Approval state |
|---|---|---|---|---|
| `masses_exclusions` | `exclusion` | Binary | `requires_review` | `requires_review` |
| `masses_exclusions2` | `exclusion` | Binary, provisional | `requires_review` | `requires_review` |
| `ht` | None assigned | Not applicable | TODO: confirm with supervisor | `requires_review` |

## Diagnostic And Audit-Only Columns

`Final_CLs` is audit-only unless explicitly reviewed and approved. It must not
be used as a feature or target for thesis evidence. Any diagnostic result that
uses `Final_CLs` must remain separate from approved modeling claims.

## Labels And Target Semantics

The observed binary values for `exclusion` are recorded as `0` and `1` in
dataset configs. The physics meaning of each label is TODO: confirm with
supervisor. Positive-label handling remains `requires_review` in run configs.

## Units

All physical units remain `requires_review` unless a dataset config marks the
unit as not applicable. TODO: confirm with supervisor before using units in
physics interpretation, symbolic expressions, plots, or thesis-facing claims.

## Missing Values

Existing dataset configs record zero missing values for registered columns in
`masses_exclusions`, `masses_exclusions2`, and `ht`. These are documented audit
facts and do not approve modeling use.

## Derived Or Engineered Features

Some run configs document engineered mass features for `masses_exclusions`,
including `delta_m`, `sum_m`, `ratio_m`, `log_mchi1`, and `log_mchipm1`.
These are config-scoped candidates, not a global data-contract approval.
TODO: confirm with supervisor which derived features are allowed for Phase 3
PySR baseline stabilization.

## Preprocessing Assumptions

Preprocessing rules are `requires_review` for all datasets. No scaling,
filtering, transformation, imputation, class balancing, target conversion, or
row exclusion may be treated as approved unless recorded in reviewed configs or
future accepted data-contract updates.

## Train, Validation, And Test Split Requirements

Split rules must record dataset id, config id, target definition, feature set,
random seed, stratification rule if used, and output paths. Existing references
to seed-42 stratified splits are provisional workflow evidence, not a final
global split policy.

## Random Seed And Reproducibility Requirements

Every modeling or audit run must record:

- dataset id and dataset config path;
- raw data path;
- feature columns and target column;
- audit-only columns excluded from modeling;
- preprocessing rule;
- split rule and random seed;
- metric protocol;
- class-imbalance handling;
- command line and output path;
- review status.

## Leakage And Forbidden-Feature Policy

- Audit-only columns are forbidden as features or targets unless explicitly
  approved through review.
- `Final_CLs` is forbidden for thesis-evidence modeling unless reviewed.
- ROC/AUC must be computed from continuous model scores, not hard labels.
- Target-derived, label-derived, or post-hoc diagnostic columns require explicit
  review before any modeling use.

## Modeling Approval Checklist

- Dataset id and raw path are registered.
- Column inventory is documented.
- Feature columns are reviewed.
- Target column and label semantics are reviewed.
- Units are reviewed or explicitly marked not applicable.
- Preprocessing rules are reviewed.
- Split rule, random seeds, and metric protocol are reviewed.
- Class-imbalance strategy is reviewed.
- Audit-only and forbidden fields are excluded.
- Nested-sampling or other upstream provenance is identified or marked TODO.
- Human/supervisor review decision is recorded.

## Open TODOs Requiring Human Or Supervisor Input

- TODO: confirm with supervisor the IDM parameter notation and units.
- TODO: confirm with supervisor the binary `exclusion` label semantics.
- TODO: confirm with supervisor whether `mhiggs` is an allowed model feature.
- TODO: confirm whether `ht` has a target variable, likelihood objective, or
  filtering rule.
- TODO: identify nested-sampling provenance for each dataset, if any.
- TODO: define preprocessing, split, metric, and class-imbalance protocols.
- TODO: decide whether derived mass features are approved for baseline PySR.
