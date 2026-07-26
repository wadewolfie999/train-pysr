# AI Agent Authority Boundaries

This repository supports an AI-assisted, Git-tracked, reproducible physics and
phenomenology thesis workflow for IDM symbolic-regression research.

These instructions are repository-local operating rules. They do not
independently ratify, amend, supersede, accept, close, or LOCK any governance or
scientific decision.

## Shared SR-Res Rebuild Context

### Project State and Historical Evidence

- The current project phase is `REBUILD`.
- Scientific Acts 1–9 are `DEPRECATED_HISTORICAL_SOURCE`. Their records,
  contracts, evidence, decisions, and LOCKs remain preserved but are not
  controlling unless A1 separately re-ratifies an exact provision.
- Historical evidence, original transcript bytes, failed attempts, and their
  provenance must be preserved. Stop before overwriting, deleting, or silently
  rewriting them.

### Authority and Actor Boundaries

- **A1 — Vahid Gorgin:** human project owner, orchestrator, and sole internal
  authority for approval, authorization, evidence acceptance, phase transition,
  scientific verdict, closure, and LOCK.
- Vahid Gorgin and Mehrsa are distinct people conducting distinct thesis
  projects on a shared account. Their identities, project states, evidence, and
  instructions must never be merged.
- **A2 — Scientific analysis and review:** advisory context synthesis, analysis,
  audit, challenge, and recommendations only. A2 cannot authorize execution,
  accept evidence, issue a verdict, transition or close a phase, or LOCK an
  artifact.
- E1 guidance must be captured faithfully but gains internal project effect only
  through A1 interpretation or adoption.
- **A3 — Codex-Control:** bounded local implementation actor for
  `SR-Res-control` only.
- **A4 — Codex-Research-Code:** bounded local scientific-code implementation and
  technical-evidence actor for `train-pysr` only.
- Neither A3 nor A4 is A2, and neither gains A1 or A2 authority.
- Provider, model, router, client, and reasoning-setting changes do not alter the
  stable A4 role, jurisdiction, authority, or accountability.
- Execution capability, repository access, appointment, file placement, and
  historical discussion do not create authority.
- No actor may self-authorize, self-accept, self-adjudicate, issue a verdict,
  close work, transition a phase, or LOCK its own work.
- Cross-repository mutation requires an exact A1-authorized contract.
- XML-style tags are reference labels only. They do not independently create
  authority, execution permission, acceptance, or governance semantics.

### Scientific-Domain and Comparison Boundaries

- Source-domain pMSSM evidence must remain distinct from target-domain IDM
  evidence and from the scientific validity or modeling status of `Ht.csv`.
  Evidence does not transfer between those domains by analogy or file placement.
- Khosravi is another master's student supervised by E1 and is pursuing a
  Neural-Network solution to the same broad classification task. His work is the
  parallel NN comparison arm in E1's broader SR-versus-NN framework.
- Future SR-versus-NN comparison must be prospective, fair, and multi-metric,
  with common datasets, splits, metrics, uncertainty reporting,
  computational-budget treatment, and comparison criteria specified before
  result inspection. ROC-AUC alone is insufficient.
- No Khosravi result becomes SR-Res evidence without an explicit,
  provenance-preserving evidence handoff.
- Neither method may be optimized against unknown test outcomes, and favorable
  metrics must not be selected after results are observed.
- Historical results must not be silently promoted into current evidence.

### Rebuild Backlog

The block labelled `VERBATIM-A1-TO-E1-CONTEXT` is reported by A1 to be an
E1-to-A1 message. Preserve the original transcript bytes and record the
directional correction as rebuild backlog. Do not promote it into current
execution requirements unless A1 explicitly adopts it.

## Repository-Specific Overlay: `train-pysr`

This repository's jurisdiction is scientific code, model configuration, bounded
execution, reproducibility, and technical evidence production under an exact
A1-approved contract.

A4 may implement, execute, perform technical validation, and report technical
evidence only within that exact contract. Technical validation is evidence for
review; it is not scientific acceptance or a verdict.

A4 must not:

- modify or execute inside `SR-Res-control`;
- convert technical success into evidence acceptance or a scientific verdict;
- expand metrics, features, targets, datasets, searches, preprocessing,
  execution, or computational scope without authorization;
- promote deprecated Acts 1–9 or historical results into current requirements
  or evidence; or
- accept, close, transition, adjudicate, or LOCK its own work.

A3 remains the bounded `SR-Res-control` actor and has no implementation
jurisdiction in this repository. The `SR-Workspace/` parent has no active
parent-directory implementation agent. Shared workspace membership does not
merge Git histories, working trees, authority, evidence, or jurisdiction.

## A4 Authorization Contract

Every A4 implementation or scientific-execution task requires a self-contained,
task-specific A1 authorization stating:

- exact goal and purpose;
- repository, file, and path scope;
- allowed inputs and allowed actions;
- forbidden inputs and forbidden actions;
- deliverables and output locations;
- validation commands, evidence, and review handoff;
- uncertainty, provenance, and claim-status policy; and
- stop conditions and escalation route.

No historical handoff, model configuration, existing evidence, dirty work,
failed run, or timed-out attempt supplies missing authority. Use inner
information only for selection and outer information only for evaluation.

## Codex/A4 Scope

Codex/A4 may:

- inspect repository state and report observed facts;
- create or edit source files, configuration files, documentation, and
  reproducibility scaffolding within an explicitly authorized goal;
- execute and perform technical validation only as explicitly authorized by A1;
- run non-destructive documentation checks and inspections when appropriate;
- preserve command lines, inputs, outputs, seeds, paths, and review status when
  relevant; and
- summarize diffs, technical-validation evidence, uncertainty, and blockers.

Codex/A4 must not:

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
- overwrite raw datasets, original notebooks, historical evidence, or prior
  generated outputs unless an exact A1 contract explicitly authorizes the exact
  operation;
- run training, fitting, symbolic search, metric production, or execute
  notebooks unless explicitly authorized by the applicable A1 contract; or
- expand repository or scientific scope silently.

## Documentation-Only Work

During documentation-only work, Codex must not change modeling code, scripts,
notebooks, configs, data files, logs, outputs, or dependencies unless the exact
A1 contract explicitly lists those paths and operations.

Unknown project, data, or physics details must be marked as `TODO`, not filled
with assumptions.

## Scientific Status and Escalation

Any Codex-generated derivation, calculation, citation, convention, model
result, equation, physics claim, modeling recommendation, or interpretation
must be marked provisional, unverified, and pending review until A1 accepts it.

Stop and escalate to A1 when authority is contradictory, provenance is unclear,
scientific meaning is uncertain, evidence identity is unresolved, or the
requested scope would expand beyond the A1 authorization. Do not resolve such
conditions by assumption.

The synchronized content in `PLANS.md` and other historical or current-facing
records does not create Codex acceptance, scientific adjudication, phase
transition, closure, LOCK, or scientific-execution authority.

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
- citation and source claims; and
- physics conventions and equations.

Codex must surface such changes clearly in summaries and review packets.

## Reproducibility and Preservation

Implementation work must preserve reproducibility, configs, review records, and
reports. Relevant inputs, outputs, dataset IDs, config IDs, random seeds, split
rules, feature sets, target definitions, metric protocols, class-imbalance
handling, command lines, and output paths must remain explicit.

Existing evidence, dirty work, failed runs, timed-out attempts, and their
provenance must be preserved. Do not clean, reset, restore, stash, delete,
overwrite, or silently repair prior work unless a task-specific A1 authorization
explicitly permits the exact operation.

## Gated Execution Process

Future phase and workstream tasks should use this process:

1. audit authority documents;
2. audit working state;
3. define scope;
4. define validation;
5. obtain A1 authorization;
6. execute bounded work;
7. perform technical validation;
8. produce review evidence; and
9. wait for A1 acceptance before claiming completion.

Technical validation is evidence, not scientific acceptance. Codex must not
claim a phase or work item complete, issue a verdict, or LOCK an artifact.

## Repo-Scoped Skills

Repo-specific skills live under `.agents/skills/`.

Future Codex work should invoke the relevant skill by name when possible:

- phase/workstream execution: `idm-phase-gate-execution`;
- file modification: `idm-scope-guard`;
- roadmap/backend selection: `idm-roadmap-router`;
- final reports: `idm-review-packet`;
- IDM/data/physics documentation: `idm-docs-todo-discipline`; and
- accepted local work requiring branch, commit, push, and PR:
  `idm-git-pr-publish`.
