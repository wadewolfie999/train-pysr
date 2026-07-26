# Project Brief: IDM Symbolic-Regression Framework

Status: **HISTORICAL PLANNING SOURCE — NON-CONTROLLING DURING REBUILD**

This brief preserves pre-REBUILD framing. Statements below describing an
immediate objective, accepted phase, or starting authority are historical and
do not authorize current work unless A1 re-ratifies an exact provision.

## Objective

This repository supports a thesis-oriented symbolic-regression framework for
Inert Doublet Model (IDM) dataset analysis.

The pre-REBUILD objective was to move from a PySR-centered BSM exclusion workflow
to a broader, reproducible IDM symbolic-regression research framework. PySR is
the first backend to stabilize, not the identity of the project.

The historical record states that Phase 0 - Repository Framing was accepted.
That record is preserved but is not current REBUILD authority.

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

Khosravi, another master's student supervised by E1, forms the parallel
Neural-Network comparison arm in E1's broader SR-versus-NN framework. Any future
comparison must prospectively specify common datasets, splits, multiple metrics,
uncertainty reporting, computational-budget treatment, and comparison criteria.
No post-result metric selection, unknown-test-outcome optimization, or evidence
transfer without a provenance-preserving handoff is authorized.

## Thesis Relevance

Workstream I is the thesis-critical path because it establishes the reviewed
data, physics, reproducibility, and backend workflow required before scientific
claims can be made.

Workstream II is exploratory. It can produce feasibility notes, prototypes, or
rejection reports, but it must not block Workstream I.

## Review Status

This brief preserves the historical record that Phase 0 - Repository Framing
was accepted; it does not re-ratify that status during REBUILD.
Scientific claims, dataset conventions, physics interpretations, and model
results remain provisional, unverified, and pending review.

It does not claim confirmed scientific performance, accepted physics
interpretation, accepted symbolic expressions, or final thesis results.
