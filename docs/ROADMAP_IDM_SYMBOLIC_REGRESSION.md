# Roadmap: IDM Symbolic Regression

## Purpose

This is the canonical roadmap for reframing the repository as an IDM symbolic-
regression research framework.

The roadmap has two workstreams:

- Workstream I - Main Workstream: thesis-critical path.
- Workstream II - Extra Workstream: exploratory backend implementation work.

Priority rule:

```text
Main Workstream > Operon Probe > Native C++ > Native Rust
```

## Dependency Map

```text
Workstream I / Phase 0
  -> Workstream I / Phase 1
  -> Workstream I / Phase 2
  -> Workstream I / Phase 3
  -> Workstream I / Phase 4
  -> Workstream I / Phase 5

Workstream II / Phase 1
  -> Workstream II / Phase 2
  -> Workstream II / Phase 3
```

Workstream II may begin only when it does not delay or dilute Workstream I.
Workstream II outputs do not replace Workstream I acceptance gates.

## Workstream I - Main Workstream

Workstream I is the thesis-critical path.

### Phase 0 - Repository Framing

Main outputs:

- `README.md` reframed around IDM symbolic regression.
- `PLANS.md` two-workstream roadmap.
- `AGENTS.md` agent guidance for future phase work.
- `docs/WORKFLOW.md` gated git-tracked phase workflow.
- `docs/CONVENTIONS.md` terminology and naming conventions.
- `docs/PROJECT_BRIEF.md` project framing.
- `docs/ROADMAP_IDM_SYMBOLIC_REGRESSION.md` canonical roadmap.

Exit conditions:

- Documentation reflects IDM symbolic-regression framing.
- PySR is documented as the first backend, not the whole project.
- Workstream I and Workstream II are distinguished.
- Unknown scientific details are marked `TODO`.
- Validation shows only authorized documentation files changed.
- Operator acceptance decision is obtained.

### Phase 1 - Data and Physics

Main outputs:

- reviewed dataset inventory;
- reviewed or `TODO` IDM terminology;
- reviewed or `TODO` units;
- reviewed or `TODO` target-label semantics;
- reviewed or `TODO` feature and target approval status;
- reviewed metric and split protocol notes.

Exit conditions:

- Modeling-approved datasets are distinguished from audit-only datasets.
- Dataset assumptions are recorded in documentation or configs.
- `Final_CLs` remains audit-only unless explicitly reviewed.
- Unknown physics/data details remain `TODO` or `requires_review`.

### Phase 2 - Existing Codebase Triage

Main outputs:

- map of scripts, configs, notebooks, modules, and outputs;
- classification of reusable, stale, blocked, or review-needed components;
- list of implementation risks and reproducibility gaps.

Exit conditions:

- Existing PySR/ML BSM exclusion work is mapped into the new framework.
- No source behavior changes are made without explicit authorization.
- Triage identifies the minimum changes needed for PySR stabilization.

### Phase 3 - PySR Baseline Stabilization

Main outputs:

- stable PySR baseline workflow;
- reviewed or explicitly provisional run configs;
- reproducible output and report structure;
- validation evidence for metric calculation and output paths.

Exit conditions:

- Baseline PySR execution is config-driven.
- Inputs, outputs, seeds, features, targets, splits, metrics, and review status
  are recorded.
- No final scientific claim is made without review.

### Phase 4 - Optimizing PySR

Main outputs:

- reviewed optimization plan;
- config-driven search variations;
- reproducible candidate reports;
- risk notes for expression complexity and metric interpretation.

Exit conditions:

- PySR optimization remains reproducible and reviewable.
- Candidate expressions and metrics are marked provisional until accepted.
- Optimization does not silently alter dataset or physics conventions.

### Phase 5 - Mimic the PySR Workflow for SymbolFit

Main outputs:

- SymbolFit workflow plan;
- SymbolFit config and output conventions;
- comparison-ready reporting structure;
- notes on backend differences.

Exit conditions:

- SymbolFit workflow mirrors the reviewed PySR workflow where appropriate.
- Backend-specific deviations are explicit.
- Comparison claims remain provisional until reviewed.

## Workstream II - Extra Workstream

Workstream II is exploratory and must not block Workstream I.

### Phase 1 - C++ Implementation - Operon

Main outputs:

- Operon/C++ feasibility note;
- dependency/build/interface notes;
- optional prototype or rejection report.

Exit conditions:

- Feasibility is documented.
- Any prototype is reproducible.
- Workstream I remains unblocked.

### Phase 2 - C++ Implementation - Native

Main outputs:

- native C++ feasibility note;
- architecture and maintenance risk assessment;
- optional prototype or rejection report.

Exit conditions:

- Native C++ path is accepted for continued exploration or rejected with
  reasons.
- Workstream I remains unblocked.

### Phase 3 - Rust Implementation - Native

Main outputs:

- native Rust feasibility note;
- architecture and maintenance risk assessment;
- optional prototype or rejection report.

Exit conditions:

- Native Rust path is accepted for continued exploration or rejected with
  reasons.
- Workstream I remains unblocked.

## Immediate Next Step After Phase 0

After operator acceptance of Phase 0, the next phase is:

```text
Workstream I / Phase 1 - Data and Physics
```

Phase 1 should resolve or mark `TODO` for IDM terms, units, dataset provenance,
target-label semantics, feature approval, validation protocol, baseline set,
and audit-only dataset status.

## Review Status

This roadmap is provisional, unverified, and pending review.

It does not claim accepted scientific performance or completed phase status.
