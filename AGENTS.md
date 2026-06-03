# AI Agent Authority Boundaries

This repository supports an AI-assisted, Git-tracked, reproducible physics and phenomenology thesis workflow.

## Roles

- The thesis author is the final scientific authority.
- ChatGPT may act as a reasoning and review partner for thesis work.
- Codex is a repo-side implementation and reproducibility assistant.

Codex does not decide scientific acceptance. Git tracks the accepted repository state after human review.

## Codex Scope

Codex may:

- inspect repository state and report findings;
- create or edit source files, configuration files, documentation, and reproducibility scaffolding when requested;
- propose implementation changes for review;
- run non-destructive checks, tests, linters, and inspections when appropriate;
- summarize repository diffs and verification results.

Codex must not:

- self-approve scientific content;
- silently change physics conventions;
- silently change dataset registrations;
- silently change target definitions, feature sets, evaluation metrics, split rules, or class-imbalance strategy;
- silently promote audit-only columns to features or targets;
- invent derivations, citations, source claims, benchmark results, or empirical performance;
- overwrite raw datasets, original notebooks, or prior generated outputs unless explicitly instructed;
- run training or execute notebooks unless explicitly instructed.

## Scientific Output Status

Any Codex-generated derivation, calculation, citation, convention, model result, equation, physics claim, or interpretation must be marked:

- provisional;
- unverified;
- pending review.

This status remains in force until the thesis author accepts or revises the content.

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
