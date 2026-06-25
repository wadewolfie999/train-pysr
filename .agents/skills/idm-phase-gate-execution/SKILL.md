---
name: idm-phase-gate-execution
description: Use when executing an IDM project phase, workstream, roadmap item, or bounded implementation/documentation assignment. Do not use for simple read-only questions or one-command inspections.
---

# IDM Phase Gate Execution

Use this skill to keep phase and workstream execution bounded.

## Required Loop

1. Run a pre-execution audit before mutation.
2. Identify authority documents, current branch, worktree state, allowed files, and validation commands.
3. Stop before editing unless operator execution authorization is explicit in the current prompt.
4. Execute only the authorized bounded scope.
5. Run the validation gate defined before execution.
6. Run a scope gate comparing intended files with changed files.
7. Produce an Operator Acceptance Candidate review packet.
8. Wait for the operator acceptance decision.
9. Do not claim completion until the operator accepts and post-integration validation passes.

## Gate Language

- Use `HALT_NEEDS_OPERATOR_AUTHORIZATION` when mutation is not explicitly authorized.
- Use `HALT_BLOCKED` when required authority, scope, or validation evidence is missing.
- Use `OAC: Operator Acceptance Candidate` for review-ready work.

## Prohibited Behavior

- Do not audit, edit, validate, self-accept, and claim completion in one uncontrolled pass.
- Do not treat a clean validation run as operator acceptance.
- Do not say `OUT_COMPLETE` before explicit operator acceptance and post-integration validation.
