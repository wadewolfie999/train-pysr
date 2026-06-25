---
name: idm-review-packet
description: Use when finishing a bounded IDM assignment and reporting results for operator review. Do not use to claim final completion before operator acceptance.
---

# IDM Review Packet

Use this skill to report review-ready work as an Operator Acceptance Candidate.

## Required Packet Sections

1. Branch name suggestion
2. Authority audit summary
3. Working state summary
4. Files changed
5. Diff summary by file
6. Commands/checks run
7. Validation results
8. Scope compliance result
9. Risk / architecture review
10. TODOs requiring human or supervisor input
11. Residual risks
12. Rollback notes
13. Recommended next phase
14. Operator decision request:
    - Accept + integrate
    - Accept + hold
    - Revise
    - Reject

## Required Label

Always include:

```text
OAC: Operator Acceptance Candidate
```

## Prohibited Label

Do not say:

```text
OUT_COMPLETE
```

unless the operator has explicitly accepted and post-integration validation has passed.
