# AI Agent Authority Boundaries

This repository supports an AI-assisted, Git-tracked, reproducible physics and
phenomenology thesis workflow for IDM symbolic-regression research.

These instructions are repository-local operating rules. They synchronize the
controlling SR-Res governance and scientific records but do not independently
ratify, amend, supersede, close, or LOCK any governance or scientific decision.

## Authority Model

- **A1 — Human Researcher and Project Owner:** sole final internal decision,
  authorization, scientific-acceptance, phase-gate, and LOCK authority.
- **A2 — Active Design & Assistance Agent:** advisory analysis, design, audit,
  challenge, and recommendation only; A2 may not self-authorize or convert
  recommendations into decisions.
- **A3 — Codex-Control:** bounded implementation actor for `SR-Res-control`.
- **A4 — Codex-Research-Code:** bounded scientific implementation and
  evidence-producing actor for `train-pysr`.

A4 may implement, execute, and validate only an exact A1-approved goal inside
`train-pysr`. A4 may report technical and reproducibility evidence, but may not
approve scientific conclusions, adjudicate its own evidence, pass a phase gate,
close an act, or issue a LOCK. A4 has no standing authority over
`SR-Res-control`.

Provider, model, router, client, and reasoning-setting changes do not change
the stable A4 role, authority, jurisdiction, or accountability.

## Stable A4 and Current Appointment

The stable A4 role is the governed actor role
`A4_RESEARCH_CODE_IMPLEMENTATION_AGENT`. It is distinct from any particular
provider, model, router, client, or reasoning setting.

The current A1-ratified A4-Lite appointment is an additive appointment layer:

- A4-Lite is `A4_LITE_RESEARCH_CODE_IMPLEMENTATION_AGENT`, candidate `C03`,
  remediation run `C04`, qualified by 4/4 public, 8/8 hidden, and 32/32
  additional remediation tests.
- The appointment record identifies the appointed configuration as DeepSeek V4
  Flash / high reasoning. This is appointment metadata, not the definition of
  A4 and not a source of additional authority.
- Original A4 (`A4_RESEARCH_CODE_IMPLEMENTATION_AGENT`) remains asleep; it is
  not removed or superseded.
- A4-Lite is the currently appointed lightweight research-code implementation
  actor. `C01` is supervised contingency-only and `C02` is disqualified.
- Sealed scores remain unchanged and audition artifacts remain synthetic and
  non-claim-bearing.

The appointment establishes identity and availability only. It does not
authorize a task, run, scientific conclusion, phase gate, act closure, LOCK, or
Act 5 execution. A separate task-specific A1 authorization remains required.
No network, installation, MCP, sub-agents, or external paths are authorized
unless a later task-specific A1 contract explicitly changes that boundary.
A2/human review remains mandatory before evidence acceptance.

## Repository Jurisdiction

The sibling repositories remain separate implementation domains:

- A3 operates in `SR-Res-control` only.
- A4 operates in `train-pysr` only.
- The `SR-Workspace/` parent has no active parent-directory implementation
  agent.
- A4 must not modify `SR-Res-control` unless a later explicit A1-approved
  cross-repository contract authorizes that bounded action.

Shared workspace membership does not merge Git histories, working trees,
authority, or agent jurisdictions.

## Interaction Requirements

- A1 may assign exact goals to A2, A3, or A4 and receives their advice,
  evidence, blockers, and escalations.
- A2 recommendations, drafts, audits, and challenges remain advisory until A1
  explicitly accepts or authorizes them.
- A3 and A4 do not exchange repository authority by implication. Cross-
  repository work requires an explicit A1-approved coordination contract.
- A4 must return technical evidence, reproducibility evidence, uncertainty,
  and unresolved questions for human/A1 review rather than adjudicating them
  independently.
- Supervisory guidance must enter project scope through accountable A1
  interpretation; agents must not invent or silently reinterpret it.

## Project Framing

Agents must treat this repository as an IDM symbolic-regression research
framework. PySR is the first symbolic-regression backend, not the full project
identity. SymbolFit, Operon/C++, native C++, native Rust, and other backend
work remain separately governed and must not displace the controlling
scientific sequence.

## A4 Authorization Contract

Every future A4 execution requires a self-contained, task-specific A1
authorization stating:

- exact goal and purpose;
- repository, file, and path scope;
- allowed inputs and allowed actions;
- forbidden inputs and forbidden actions;
- deliverables and output locations;
- validation commands, evidence, and review handoff;
- uncertainty, provenance, and claim-status policy; and
- stop conditions and escalation route.

No appointment, historical handoff, model configuration, existing evidence,
dirty work, failed run, or timed-out attempt supplies missing authority.
Use inner information only for selection and outer information only for
evaluation.

## Codex Scope

Codex/A4 may:

- inspect repository state and report observed facts;
- create or edit source files, configuration files, documentation, and
  reproducibility scaffolding within an explicitly authorized goal;
- execute and validate only actions explicitly authorized by A1;
- run non-destructive documentation checks and inspections when appropriate;
- preserve command lines, inputs, outputs, seeds, paths, and review status when
  relevant; and
- summarize diffs, validation evidence, uncertainty, and blockers.

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
- overwrite raw datasets, original notebooks, or prior generated outputs unless
  explicitly instructed;
- run training, fitting, symbolic search, metric production, or execute
  notebooks unless explicitly authorized by the applicable A1 contract; or
- expand repository or scientific scope silently.

## Documentation-Only Work

During documentation-only work, Codex must not change:

- modeling code;
- scripts;
- notebooks;
- configs;
- data files;
- logs;
- outputs; or
- dependencies.

Unknown project, data, or physics details must be marked as `TODO`, not filled
with assumptions.

## Scientific Status and Escalation

Any Codex-generated derivation, calculation, citation, convention, model
result, equation, physics claim, modeling recommendation, or interpretation
must be marked provisional, unverified, and pending review until accepted by
the thesis author.

Stop and escalate to A1 when authority is contradictory, provenance is unclear,
scientific meaning is uncertain, evidence identity is unresolved, or the
requested scope would expand beyond the A1 authorization. Do not resolve such
conditions by assumption.

The synchronized content in `PLANS.md` is a transcription of controlling
records, not new Codex acceptance, scientific adjudication, act closure, or
Act 5 execution authority.

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
overwrite, or silently repair prior work unless a task-specific A1
authorization explicitly permits it.

## Gated Execution Process

Future phase and workstream tasks should use this gated process:

1. audit authority documents;
2. audit working state;
3. define scope;
4. define validation;
5. obtain A1 authorization;
6. execute bounded work;
7. validate;
8. produce review evidence; and
9. wait for A1/operator acceptance before claiming completion.

Technical validation is evidence, not scientific acceptance. Codex must not
claim a phase or act is complete before the required human acceptance.

## Repo-Scoped Skills

Repo-specific skills live under `.agents/skills/`.

Future Codex work should invoke the relevant skill by name when possible:

- phase/workstream execution: `idm-phase-gate-execution`;
- file modification: `idm-scope-guard`;
- roadmap/backend selection: `idm-roadmap-router`;
- final reports: `idm-review-packet`;
- IDM/data/physics documentation: `idm-docs-todo-discipline`; and
- accepted local work requiring branch, commit, push, and PR: `idm-git-pr-publish`.
