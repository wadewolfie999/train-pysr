# Codex Execution Protocol

## Scope

This protocol applies to future Codex tasks in this repository. Codex is a repository-side implementation and reproducibility assistant, not the final scientific authority.

## Required Pre-Task Reading

Before making changes, Codex must read the relevant current files for the task, including:

- `AGENTS.md`
- `PLANS.md`
- `SKILLS.md`
- `docs/CONVENTIONS.md`
- `docs/WORKFLOW.md`
- `docs/CODEX_REVIEW_CHECKLIST.md`
- relevant module files under `modules/`
- relevant dataset registry files under `configs/datasets/`

## Task Classification

Codex must identify whether the task is documentation, configuration, scaffolding, data audit, implementation, verification, review support, or run execution.

Run execution requires explicit instruction and reviewed configuration.

## Allowed Actions

Codex may scaffold files, scripts, configs, tests, checks, and documentation. Codex may run non-destructive inspections, tests, linters, and validation checks when appropriate.

Codex may propose scientific or modeling ideas only as provisional, unverified, and pending review.

## Forbidden Actions

Codex must not:

- approve its own scientific claims;
- invent physics assumptions, derivations, citations, source claims, benchmark results, or empirical performance;
- run training, execute notebooks, or run PySR unless explicitly instructed;
- overwrite raw data;
- overwrite previous outputs;
- silently change dataset features, targets, labels, units, metrics, split rules, class-imbalance strategy, or physics assumptions;
- compute ROC/AUC from hard class labels;
- promote audit-only columns to features or targets without explicit approval.

## Scientific-Output Marking Rule

Any Codex-generated derivation, calculation, citation, convention, model result, equation, physics claim, modeling recommendation, or interpretation must be marked:

- provisional;
- unverified;
- pending review.

## Dataset And Convention Protection

Dataset-specific assumptions must live in dataset registry or configuration files. Unknowns must be marked `requires_review`, not guessed.

Changes to features, targets, labels, units, preprocessing, split rules, metric protocol, class-imbalance strategy, or physics conventions require explicit review.

## Reproducibility Requirements

Future runs must record:

- dataset id;
- config id;
- random seed;
- split rule;
- feature set;
- target;
- metric protocol;
- command used;
- output path.

Run records should also include code version, environment details, class-imbalance handling, and review status when available.

## Output And Run-Directory Rules

Raw data must remain unchanged. Generated outputs must be written to new output paths and must not overwrite previous outputs.

Temporary PySR outputs and model artifacts are not accepted results until reviewed.

## Review-Before-Commit Rule

Codex must not commit unless explicitly instructed. Uncommitted changes should be reviewed before commit. Scientific conclusions and result claims require thesis-author review before acceptance.

## Standard Task Report Format

Each Codex task must end with:

- files changed;
- commands run;
- assumptions;
- open questions;
- verification status;
- recommendations marked provisional, unverified, pending review.
