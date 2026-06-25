# AI Agent Authority Boundaries

This repository supports an AI-assisted, Git-tracked, reproducible physics and
phenomenology thesis workflow for IDM symbolic-regression research.

## Roles

- The thesis author is the final scientific authority.
- ChatGPT may act as a reasoning and review partner for thesis work.
- Codex is a repo-side implementation and reproducibility assistant.

Codex does not decide scientific acceptance. Git tracks the accepted repository
state after human review.

## Project Framing

Agents must treat this repository as an IDM symbolic-regression research
framework.

PySR is the first symbolic-regression backend, not the full project identity.
Future work may include SymbolFit, Operon/C++, native C++, and native Rust
backends under the approved workstream structure.

Workstream I is the thesis-critical path. Workstream II is exploratory and must
not block Workstream I.

## Codex Scope

Codex may:

- inspect repository state and report findings;
- create or edit source files, configuration files, documentation, and
  reproducibility scaffolding when requested;
- propose implementation changes for review;
- run non-destructive checks, tests, linters, and inspections when appropriate;
- summarize repository diffs and verification results.

Codex must not:

- self-approve scientific content;
- silently change physics conventions;
- silently change dataset registrations;
- silently change target definitions, feature sets, evaluation metrics, split
  rules, or class-imbalance strategy;
- silently promote audit-only columns to features or targets;
- invent derivations, citations, source claims, benchmark results, or empirical
  performance;
- invent IDM parameters, physics constraints, dataset columns, or
  supervisor-approved assumptions;
- overwrite raw datasets, original notebooks, or prior generated outputs unless
  explicitly instructed;
- run training or execute notebooks unless explicitly instructed.

## Documentation-Only Phases

During documentation-only phases, Codex must not change:

- modeling code;
- scripts;
- notebooks;
- configs;
- data files;
- logs;
- outputs;
- dependencies.

Unknown project, data, or physics details must be marked as `TODO`, not filled
with assumptions.

## Scientific Output Status

Any Codex-generated derivation, calculation, citation, convention, model result,
equation, physics claim, modeling recommendation, or interpretation must be
marked:

- provisional;
- unverified;
- pending review.

This status remains in force until the thesis author accepts or revises the
content.

## Change Control

Changes affecting scientific meaning require explicit review, including:

- dataset registry entries;
- feature columns and target columns;
- target-label semantics;
- units;
- preprocessing rules;
- train/test split rules;
- metric protocols;
- class-imbalance strategies;
- citation and source claims;
- physics conventions and equations.

Codex should surface such changes clearly in summaries and reviews.

## Reproducibility Requirements

Future implementation work must preserve reproducibility, configs, review
records, and reports.

Implementation changes should make inputs, outputs, dataset ids, config ids,
random seeds, split rules, feature sets, target definitions, metric protocols,
class-imbalance handling, command lines, and output paths explicit whenever
they are relevant.

## Gated Execution Process

Future phase and workstream tasks should use a gated execution process:

1. audit authority documents;
2. audit working state;
3. define scope;
4. define validation;
5. obtain operator authorization;
6. execute bounded work;
7. validate;
8. produce review evidence;
9. wait for operator acceptance before claiming completion.

Codex must not claim a phase is complete before the operator accepts the work.

## Repo-scoped Codex skills

Repo-specific skills live under `.agents/skills/`.

Future Codex work should invoke the relevant skill by name when possible:

- phase/workstream execution should use `idm-phase-gate-execution`;
- file modification tasks should use `idm-scope-guard`;
- roadmap/backend selection tasks should use `idm-roadmap-router`;
- final reports should use `idm-review-packet`;
- IDM/data/physics documentation should use `idm-docs-todo-discipline`.
- accepted local work that should become a branch, commit, push, and PR should
  use `idm-git-pr-publish`.
