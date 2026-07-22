# IDM Physics Assumptions

## Purpose

This document defines the physics-assumption boundary for IDM
symbolic-regression work. It separates accepted repository framing from
scientific assumptions that still require human or supervisor review.

## Current Status

Phase 0 - Repository Framing is explicitly accepted. The physics content in
this document is provisional, unverified, and pending review. It does not claim
final IDM conventions, final viability semantics, final exclusion semantics, or
supervisor approval.

## IDM Scope

The repository is framed as an IDM symbolic-regression research framework.
Symbolic regression searches for interpretable expressions over reviewed
features and reviewed targets or scores. It does not define the IDM physics
model, physical constraints, dataset provenance, or thesis conclusions.

## Confirmed Assumptions

| Item | Confirmed repository statement | Source class |
|---|---|---|
| Project identity | IDM symbolic-regression research framework | Accepted Phase 0 docs |
| Backend boundary | PySR is the first symbolic-regression backend, not the full project identity | Accepted Phase 0 docs |
| Workstream priority | Workstream I is thesis-critical; Workstream II is exploratory and non-blocking | Accepted Phase 0 docs |
| Nested-sampling boundary | Nested sampling is upstream data generation or preprocessing, not symbolic regression | Accepted Phase 0 docs |
| Scientific authority | The thesis author and supervisor remain the review authority for scientific meaning | Authority docs |

## Assumptions Requiring Supervisor Confirmation

| Topic | Status | Required action |
|---|---|---|
| IDM parameter notation | TODO: confirm with supervisor | Record accepted symbols and aliases. |
| Units for mass-like columns | TODO: confirm with supervisor | Record units for `mchi1`, `mchipm1`, `mhiggs`, `M_S`, `M_R`, `M_Y`, and related columns if applicable. |
| Physical constraints | TODO: confirm with supervisor | Record constraints before using them in filters, expressions, or claims. |
| `exclusion` label semantics | TODO: confirm with supervisor | Define what `0` and `1` mean physically. |
| Viability boundary | TODO: confirm with supervisor | Define whether and how binary labels map to viable/non-viable regions. |
| `Final_CLs` interpretation | TODO: confirm with supervisor | Keep audit-only unless approved. |
| `ht` likelihood/parameter interpretation | TODO: confirm with supervisor | Define target, objective, filtering, and column meanings before modeling. |

## IDM Parameter Notation

Observed repository column names include `mchi1`, `mchipm1`, `mhiggs`, `M_S`,
`M_R`, `M_Y`, `laL`, `omega`, `invBr`, `lilithLogl`, `PsiCross`, `vctc`,
`logM_S`, `logM_R`, `delMA`, `delMC`, `logvt`, and `Chi2`.

These names are observed column names, not thesis-approved IDM notation. TODO:
confirm with supervisor the accepted notation, aliases, units, and whether each
column is an input parameter, derived quantity, likelihood diagnostic, target,
or audit-only value.

## Units And Dimensional Consistency

Units are `requires_review` in current dataset configs except where a target
unit is marked not applicable. No dimensional analysis, unit conversion, or
dimensionless transformation is approved by this document.

Before a symbolic expression is interpreted physically, the reviewed contract
must record the units of each input, target, derived feature, and output score.

## Physical Constraints

No final physical constraints are asserted here. Existing configs record some
observed audit facts, such as no negative masses observed in the registered
mass datasets and an observed `mchipm1 >= mchi1` condition. These are audit
observations, not accepted IDM constraints.

TODO: confirm with supervisor which constraints are physical requirements,
data-generation artifacts, scan bounds, or quality-control filters.

## Exclusion And Viability Semantics

The repository records a binary `exclusion` target for `masses_exclusions` and
a provisional binary `exclusion` target for `masses_exclusions2`. The physical
meaning of labels `0` and `1` is `requires_review`.

Do not convert binary exclusion labels into viability, discovery, confidence,
or likelihood claims without explicit review.

## Dataset-Label Physics Interpretation

| Dataset ID | Label or objective status | Physics interpretation |
|---|---|---|
| `masses_exclusions` | Binary `exclusion` target recorded | TODO: confirm with supervisor. |
| `masses_exclusions2` | Provisional binary `exclusion` target | TODO: confirm with supervisor. |
| `ht` | No target assigned | TODO: confirm target, likelihood objective, or filtering rule. |

## Forbidden Assumptions

- Do not infer final physical meaning from column names alone.
- Do not treat `Final_CLs` as an approved feature or target.
- Do not treat audit correlations as exclusion rules.
- Do not assume nested-sampling provenance without repository evidence.
- Do not assert use of MultiNest, dynesty, JAXNS, or another upstream tool
  unless future evidence records it.
- Do not claim supervisor approval from the existence of this document.
- Do not claim a final accepted symbolic expression or physics interpretation.

## Relationship To Symbolic Regression

Symbolic regression may search for interpretable expressions only over reviewed
inputs and reviewed targets or scores. Backend-specific behavior must not
change feature, target, label, unit, metric, split, or preprocessing semantics.

PySR is the first backend to stabilize after Phase 1 and Phase 2 review work.
SymbolFit and Workstream II backends must inherit reviewed data and physics
contracts rather than redefining them silently.

## Relationship To Neural-Network Comparison

The repository anticipates later neural-network comparison work, but final
comparison metrics and reporting rules are TODO. Neural-network comparison must
use the same reviewed dataset, feature, target, split, metric, and
class-imbalance definitions as the symbolic-regression workflow unless a
reviewed exception is recorded.

## Review Checklist

- IDM notation is reviewed.
- Units are reviewed.
- Physical constraints are reviewed.
- Label semantics are reviewed.
- Target/objective definitions are reviewed.
- Audit-only fields are excluded from modeling claims.
- Nested-sampling provenance is identified or marked TODO.
- Symbolic-regression outputs are kept separate from physics acceptance.
- Neural-network comparison metrics are reviewed before use.

## Open TODOs

- TODO: confirm with supervisor the accepted IDM parameter notation.
- TODO: confirm with supervisor all units and dimensional assumptions.
- TODO: confirm with supervisor physical constraints and scan boundaries.
- TODO: confirm with supervisor exclusion and viability semantics.
- TODO: confirm with supervisor the role of `Final_CLs`.
- TODO: confirm with supervisor the scientific role of the `ht` dataset.
- TODO: define final comparison metrics for neural-network work.
