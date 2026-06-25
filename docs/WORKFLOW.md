# Workflow

This repository uses a human-reviewed, Git-tracked phased workflow for IDM
symbolic-regression research.

## Roles

- The thesis author is the final scientific authority.
- ChatGPT may support scientific reasoning and review.
- Codex implements repository-side changes and reproducibility support.

Codex does not decide scientific acceptance. Codex-generated derivations,
calculations, citations, conventions, model results, equations, and physics
claims are provisional, unverified, and pending review.

## Phase Workflow

Every phase should follow this sequence:

1. inspect current authority documents;
2. inspect current git working state;
3. define bounded scope;
4. define validation checks;
5. obtain operator execution authorization;
6. execute only the authorized work;
7. run validation;
8. check scope compliance;
9. produce a review packet;
10. wait for operator acceptance before claiming completion.

## Two-Gate Execution

### Gate 1 - Operator Execution Authorization

Before mutation, Codex should report:

- authority audit;
- working-state audit;
- allowed files and prohibited files/actions;
- validation plan;
- rollback strategy.

No files should be edited before this gate is approved.

### Gate 2 - Operator Acceptance Decision

After bounded execution and validation, Codex should produce an Operator
Acceptance Candidate packet. The packet should include:

- branch name suggestion;
- authority and working-state summaries;
- files changed;
- diff summary;
- commands and checks run;
- validation results;
- scope compliance result;
- risks and residual risks;
- TODOs requiring human or supervisor input;
- rollback notes;
- recommended next phase.

Codex must not claim the phase is complete until the operator accepts the work.

## Validation And Scope Gates

After execution, validation must show whether the requested evidence exists.
Scope is valid only if:

- every changed file is inside the authorized scope;
- no prohibited file or artifact class changed;
- no hidden implementation, config, data, log, output, or dependency change
  occurred;
- no unresolved safety or authority ambiguity remains.

If validation fails, report revision needs. If scope is invalid, stop and report
the blocker.

## Phase Output Rule

Every phase must produce at least one of:

- documentation;
- reproducible code;
- validated output;
- a clear rejection or decision report.

The output must identify scope, assumptions, open questions, validation status,
and review status.

## Git State

Git tracks accepted repository state. Uncommitted changes should be reviewed
before commit. Commits should represent reviewed operational truth, not
historical transcript dumps.

Recommended branch naming:

```text
docs/<workstream-or-phase-summary>
feature/<workstream-or-phase-summary>
fix/<specific-issue-summary>
review/<review-or-audit-summary>
```

For this phase, the recommended branch name is:

```text
docs/workstream-i-phase-0-repository-framing
```

Commit messages should be concise and scoped to the reviewed change. Codex must
not stage, commit, push, merge, or open a pull request unless explicitly
authorized.

## Dataset Changes

Adding a new dataset requires a dataset registry/config update and review.
Dataset-specific assumptions must be declared in the dataset entry or related
config, not embedded silently in scripts.

Changing feature columns, target columns, target-label semantics, units,
preprocessing rules, split rules, metric protocols, or class-imbalance
strategies requires review.

## Raw Artifacts

Original notebooks and raw datasets must be preserved unchanged. Generated
outputs and run logs should be written to new output paths to avoid overwriting
prior results.

## Final Reporting

Final reports should distinguish:

- observed facts;
- inferred behavior;
- hypotheses;
- provisional recommendations;
- TODOs requiring human or supervisor review.

Reports must not convert provisional scientific content into accepted claims.
