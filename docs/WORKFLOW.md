# Workflow

This repository uses a human-reviewed, Git-tracked workflow:

1. inspect;
2. propose;
3. implement;
4. verify;
5. review;
6. accept or reject.

## Roles

- The thesis author is the final scientific authority.
- ChatGPT may support scientific reasoning and review.
- Codex implements repository-side changes and reproducibility support.

Codex does not decide scientific acceptance. Codex-generated derivations, calculations, citations, conventions, model results, equations, and physics claims are provisional, unverified, and pending review.

## Git State

Git tracks accepted repository state. Uncommitted changes should be reviewed before commit. Commits should represent reviewed operational truth, not historical transcript dumps.

## Dataset Changes

Adding a new dataset requires a dataset registry/config update and review. Dataset-specific assumptions must be declared in the dataset entry or related config, not embedded silently in scripts.

Changing feature columns, target columns, target-label semantics, units, preprocessing rules, split rules, metric protocols, or class-imbalance strategies requires review.

## Raw Artifacts

Original notebooks and raw datasets must be preserved unchanged. Generated outputs and run logs should be written to new output paths to avoid overwriting prior results.
