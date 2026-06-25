# Plans

## Current Roadmap Phase

Current phase:

```text
Workstream I / Phase 0 - Repository Framing
```

This phase reframes the repository from a PySR-centered BSM exclusion workflow
into a thesis-oriented IDM symbolic-regression research framework.

Phase 0 remains pending operator acceptance until the review packet is accepted.

## Project Direction

The repository supports symbolic regression for Inert Doublet Model (IDM)
dataset analysis. PySR is the first backend to stabilize, but the project is
not limited to PySR.

The roadmap is split into two workstreams:

- Workstream I: main thesis-critical workflow.
- Workstream II: exploratory backend implementation work that must not block
  Workstream I.

Priority rule:

```text
Main Workstream > Operon Probe > Native C++ > Native Rust
```

## Existing Context To Preserve

- `masses_exclusions` is the first registered modeled dataset.
- `masses_exclusions2` is audit-only intake; it has a related mass/exclusion
  schema with added `mhiggs` and is not approved for modeling.
- `ht` is audit-only intake; it is a distinct likelihood/parameter-style dataset
  with no assigned modeling target.
- `Final_CLs` is audit-only unless explicitly reviewed and approved.
- ROC/AUC must be computed from continuous scores, not hard class labels.
- AUC > 0.97 is an aspirational target for `masses_exclusions`, not a claim
  unless proven by an actual reviewed run.
- All recommendations in this file are provisional, unverified, and pending
  review.

## Workstream I - Main Workstream

Workstream I is the thesis-critical path.

### Phase 0 - Repository Framing

Purpose:

- Align authority docs with the IDM symbolic-regression research framework.
- Make PySR the first backend rather than the project identity.
- Establish Workstream I and Workstream II boundaries.

Dependencies:

- Existing repository docs and current git state audit.
- Operator execution authorization.

Exit conditions:

- `README.md` identifies the repository as an IDM symbolic-regression framework.
- `PLANS.md` defines the two-workstream roadmap.
- `docs/PROJECT_BRIEF.md` and `docs/ROADMAP_IDM_SYMBOLIC_REGRESSION.md` exist.
- Documentation preserves review-sensitive scientific status.
- Validation shows only allowed documentation files changed.
- Operator reviews the acceptance packet.

### Phase 1 - Data and Physics

Purpose:

- Review dataset registrations, target semantics, units, and physics terms.
- Separate known facts from `TODO` items requiring human or supervisor review.

Dependencies:

- Accepted Phase 0 framing.

Exit conditions:

- Dataset and physics conventions are recorded or marked `TODO`.
- Audit-only datasets remain blocked from modeling until approved.
- Feature, target, metric, split, and class-imbalance rules are explicit.

### Phase 2 - Existing Codebase Triage

Purpose:

- Map existing scripts, configs, notebooks, modules, and outputs to the new
  framework.
- Identify what can be reused, retired, or generalized.

Dependencies:

- Phase 1 data and physics review.

Exit conditions:

- Existing code paths are classified by role.
- Reproducibility risks and stale assumptions are identified.
- No modeling behavior is changed without explicit scope authorization.

### Phase 3 - PySR Baseline Stabilization

Purpose:

- Stabilize PySR as the first symbolic-regression backend.
- Preserve reproducibility through configs, review records, and output paths.

Dependencies:

- Phase 2 triage.
- Reviewed dataset and metric conventions.

Exit conditions:

- Baseline PySR workflow is documented, config-driven, and reproducible.
- Runs record inputs, outputs, seeds, features, targets, metrics, and review
  status.
- Claims remain provisional until reviewed.

### Phase 4 - Optimizing PySR

Purpose:

- Improve the PySR workflow after the baseline is stable.
- Tune search settings and candidate selection under reviewed constraints.

Dependencies:

- Phase 3 baseline stabilization.

Exit conditions:

- Optimization changes are config-driven and reproducible.
- Metrics and generated expressions are reviewable.
- No final scientific claim is made without human/supervisor review.

### Phase 5 - Mimic the PySR Workflow for SymbolFit

Purpose:

- Reuse the reviewed PySR workflow structure for a SymbolFit backend.
- Compare workflow behavior without changing scientific definitions silently.

Dependencies:

- Phase 4 PySR workflow evidence.
- Reviewed SymbolFit backend requirements.

Exit conditions:

- SymbolFit workflow mirrors the reviewed PySR workflow where appropriate.
- Backend-specific differences are documented.
- Comparison readiness is assessed without inventing final metrics.

## Workstream II - Extra Workstream

Workstream II is exploratory. It must not block Workstream I.

### Phase 1 - C++ Implementation - Operon

Purpose:

- Probe Operon/C++ as a possible backend.

Dependencies:

- Workstream I remains prioritized.
- Reviewed interface assumptions from the main workflow.

Exit conditions:

- Operon feasibility is documented.
- Any prototype is reproducible or rejected with reasons.
- No Workstream I gate is delayed by this work.

### Phase 2 - C++ Implementation - Native

Purpose:

- Explore a native C++ symbolic-regression implementation after the Operon
  probe.

Dependencies:

- Workstream II Phase 1 findings.
- Continued non-blocking status relative to Workstream I.

Exit conditions:

- Native C++ feasibility, risks, and maintenance cost are documented.
- Any prototype has clear reproducibility and review boundaries.

### Phase 3 - Rust Implementation - Native

Purpose:

- Explore a native Rust symbolic-regression implementation after higher-
  priority backend probes.

Dependencies:

- Workstream II Phase 2 findings.
- Continued non-blocking status relative to Workstream I.

Exit conditions:

- Native Rust feasibility, risks, and maintenance cost are documented.
- Any prototype is reproducible or explicitly rejected.

## Immediate Next Step

After Phase 0 is accepted, the next phase is:

```text
Workstream I / Phase 1 - Data and Physics
```

Phase 1 should resolve or explicitly mark `TODO` for units, label semantics,
IDM terminology, validation protocol, baseline set, and dataset approval status.
