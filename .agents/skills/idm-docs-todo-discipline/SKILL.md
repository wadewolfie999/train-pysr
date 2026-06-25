---
name: idm-docs-todo-discipline
description: Use when editing IDM physics, dataset, label, target, preprocessing, nested-sampling, metrics, supervisor-decision, or thesis-claim documentation. Do not use for docs that do not touch scientific meaning.
---

# IDM Docs TODO Discipline

Use this skill to keep scientific documentation provisional and evidence-bound.

## Rules

- Do not invent dataset columns.
- Do not invent IDM parameters.
- Do not invent physics constraints.
- Do not invent supervisor-approved assumptions.
- Do not claim scientific results unless already evidenced in the repository.
- Mark unknowns as `TODO`.
- Preserve uncertainty explicitly.
- Separate confirmed facts from planned work.
- Do not turn roadmap intentions into completed claims.

## Acceptable Wording

```text
TODO: Confirm dataset columns and units with supervisor.
TODO: Confirm IDM parameter naming convention.
TODO: Confirm final comparison metrics against the neural-network workflow.
```

## Prohibited Wording

Do not write:

```text
The dataset contains columns X, Y, Z.
The model has achieved final validated performance.
The supervisor has approved this physics assumption.
```

unless those claims are directly supported by existing repository evidence.
