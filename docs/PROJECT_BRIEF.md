# Project Brief: IDM Symbolic-Regression Framework

## Objective

This repository supports a thesis-oriented symbolic-regression framework for
Inert Doublet Model (IDM) dataset analysis.

The immediate objective is to move from a PySR-centered BSM exclusion workflow
to a broader, reproducible IDM symbolic-regression research framework. PySR is
the first backend to stabilize, not the identity of the project.

## Motivation

The thesis workflow needs a repository structure that separates:

- reviewed dataset and physics conventions;
- upstream data generation or preprocessing;
- symbolic-regression backend execution;
- reproducible configs and output records;
- human and supervisor review.

This separation is required so that backend comparisons do not silently change
features, targets, metric protocols, split rules, units, or physics
interpretations.

## Research Scope

The active modeled dataset currently recorded by the repository is:

```text
masses_exclusions
```

The existing workflow also records audit-only intake datasets:

```text
masses_exclusions2
ht
```

These intake datasets are not approved for modeling until their dataset
registry entries, targets, features, units, and evaluation rules are reviewed.

TODO: confirm the final IDM parameter notation, units, target-label semantics,
and physics constraints with the thesis author and supervisor.

## Backend Strategy

The backend strategy is staged:

1. stabilize PySR as the first symbolic-regression backend;
2. optimize PySR under reviewed reproducibility constraints;
3. mimic the reviewed PySR workflow for SymbolFit;
4. probe Operon/C++ as exploratory Workstream II work;
5. evaluate native C++ and native Rust only after higher-priority paths.

The priority rule is:

```text
Main Workstream > Operon Probe > Native C++ > Native Rust
```

## Nested-Sampling Boundary

Nested sampling, where relevant, is treated as upstream data generation or
preprocessing. It is not the symbolic-regression model.

TODO: identify which current or future datasets are derived from
nested-sampling outputs and record that provenance in reviewed documentation or
configuration.

## Neural-Network Comparison

A comparison with a neural-network workflow is expected later in the thesis
workflow. This brief does not define final comparison metrics because the
current repository authority docs do not yet provide reviewed final metrics for
that comparison.

TODO: define comparison metrics, baseline models, and reporting requirements
after the dataset and physics conventions are reviewed.

## Thesis Relevance

Workstream I is the thesis-critical path because it establishes the reviewed
data, physics, reproducibility, and backend workflow required before scientific
claims can be made.

Workstream II is exploratory. It can produce feasibility notes, prototypes, or
rejection reports, but it must not block Workstream I.

## Review Status

This brief is provisional, unverified, and pending review.

It does not claim confirmed scientific performance, accepted physics
interpretation, accepted symbolic expressions, or final thesis results.
