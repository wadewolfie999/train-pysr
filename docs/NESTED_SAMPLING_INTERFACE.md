# Nested-Sampling Interface

## Purpose

This document defines the boundary between upstream nested-sampling outputs and
downstream symbolic-regression work.

## Boundary Statement

Nested sampling, when present, is upstream data generation, scanning, or
preprocessing evidence. It is not the symbolic-regression backend and must not
silently define feature roles, target semantics, units, preprocessing rules,
split rules, metrics, or physics claims.

## Upstream Tools

No current repository evidence proves that MultiNest, dynesty, JAXNS, or any
other named nested-sampling tool produced the registered datasets. Tool names
must remain TODO until provenance evidence is recorded.

| Dataset ID | Upstream tool evidence | Status |
|---|---|---|
| `masses_exclusions` | TODO: identify provenance | `requires_review` |
| `masses_exclusions2` | TODO: identify provenance | `requires_review` |
| `ht` | TODO: identify provenance | `requires_review` |

## Expected Input/Output Relationship

Upstream scan or nested-sampling outputs may provide raw rows, likelihood
diagnostics, weights, parameter values, derived quantities, or labels. Symbolic
regression may consume only reviewed downstream columns and reviewed targets or
scores declared in the dataset contract.

## Dataset Provenance Requirements

Each dataset must record:

- source file path;
- dataset id;
- upstream generator or scanner, if known;
- upstream command or configuration, if known;
- random seeds or sampling settings, if known;
- scan bounds and physical constraints, if known;
- column mapping from upstream names to repository names;
- whether rows are raw samples, filtered samples, weighted samples, or derived
  rows;
- review status.

## Required Metadata From Nested-Sampling Runs

If a future dataset is derived from nested sampling, it must record:

| Metadata | Required status |
|---|---|
| Tool name and version | TODO until identified |
| Sampling configuration | TODO until identified |
| Prior definitions | TODO until reviewed |
| Likelihood definition | TODO until reviewed |
| Evidence values | TODO until reviewed |
| Sample weights | TODO until reviewed |
| Effective sample size or diagnostics | TODO until reviewed |
| Random seeds | TODO until identified |
| Output column schema | TODO until reviewed |
| Postprocessing or filtering | TODO until reviewed |

## Parameter And Column Mapping Requirements

Every upstream column must map to exactly one documented downstream role:

- reviewed feature;
- reviewed target;
- reviewed sample weight;
- reviewed diagnostic/audit-only column;
- derived feature requiring review;
- unknown / `requires_review`.

Columns with unknown meaning must not be used for modeling.

## Sample Weights, Likelihoods, Evidences, And Diagnostics

Likelihood-like columns, probabilities, evidences, confidence levels, chi-square
values, and sample weights are diagnostic or objective metadata until reviewed.
They must not become features, targets, labels, or sample weights for symbolic
regression by implication.

`Final_CLs`, `Prob`, `logLik`, and `Chi2` require review before any modeling
role is assigned.

## Preprocessing Handoff Rules

The handoff from upstream output to symbolic-regression input must record:

- raw input path;
- generated or processed output path, if any;
- row filters;
- deduplication rules;
- missing-value handling;
- unit conversions;
- derived-column definitions;
- target construction;
- class-imbalance handling;
- train/validation/test split rule;
- random seed;
- review status.

## What Symbolic Regression May Consume

Symbolic regression may consume only columns and derived features that the data
contract marks as reviewed for the relevant run configuration. Current
repository evidence permits `masses_exclusions` workflows to reference
`mchi1`, `mchipm1`, and binary `exclusion` through existing configs, but units,
positive-label semantics, preprocessing, split rules, metrics, and class
imbalance remain review-sensitive.

## What Symbolic Regression Must Not Consume Without Review

- Audit-only diagnostics such as `Final_CLs`.
- Likelihood or probability columns such as `Prob` or `logLik`.
- Evidence, weight, diagnostic, or chi-square columns.
- Columns with unknown units or unknown physics meaning when a physical claim
  would depend on that meaning.
- Any generated output under ignored output paths unless explicitly promoted
  through review.

## Reproducibility Requirements

Nested-sampling-derived datasets must preserve enough metadata to reproduce or
audit the handoff. Required records include upstream configuration, dataset id,
raw path, processed path if any, column mapping, feature and target definitions,
review status, command line, random seeds, and output paths.

## Open TODOs

- TODO: identify provenance for `masses_exclusions`.
- TODO: identify provenance for `masses_exclusions2`.
- TODO: identify provenance for `ht`.
- TODO: define accepted metadata schema for nested-sampling-derived datasets.
- TODO: confirm whether any current columns are likelihoods, weights,
  evidences, or diagnostics.
