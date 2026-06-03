# Conventions

This file records current scientific and computational conventions for the repository. Codex-generated conventions and recommendations are provisional, unverified, and pending review until accepted by the thesis author.

## Dataset Registration

Each dataset must declare:

- dataset id;
- raw path;
- schema;
- feature columns;
- target column;
- label semantics;
- units;
- preprocessing rules;
- train/test split rule;
- metric protocol;
- class-imbalance strategy;
- approval status;
- open questions.

Dataset-specific assumptions must live in dataset registry or configuration entries. Adding a new dataset requires a registry/config update and review.

## Dataset Registry

### `masses_exclusions`

- Dataset id: `masses_exclusions`
- Raw file: `masses_exclusions.csv`
- Known columns: `mchi1`, `mchipm1`, `Final_CLs`, `exclusion`
- Default features: `mchi1`, `mchipm1`
- Target: binary exclusion
- `Final_CLs`: audit-only unless explicitly approved as a feature or target
- Approval status: requires review
- Open questions: units, label semantics details, preprocessing rules, train/test split rule, metric protocol details, class-imbalance strategy

No derivation rule for `exclusion` is asserted here.

## Feature And Target Approval

Feature columns and target columns must be declared in dataset registry/config entries. Changes require review before use in training, evaluation, or scientific interpretation.

Audit-only columns must not be used as features or targets unless explicitly approved.

## Target-Label Semantics

Each dataset must define what each target label means. Binary, multiclass, and continuous targets must be handled as distinct target definitions. The current `masses_exclusions` target is binary exclusion; it must not be converted to multiclass classification without review.

## Units

Units must be declared per dataset and per relevant column when known. Unknown units must be marked `TBD` or `requires_review`.

## ROC/AUC Rule

ROC/AUC must be computed from continuous scores, not hard class labels. Thresholded labels may be reported separately, but they are not a valid source for ROC/AUC.

AUC > 0.97 is an aspirational target for `masses_exclusions`, not a claim unless proven by an actual reviewed run.

## Class-Imbalance Handling

Class imbalance must be handled explicitly and reproducibly. The strategy must be declared in the dataset config or run config and recorded in run metadata.

## Random Seeds And Split Recording

Train/test split rules and random seeds must be recorded for reproducibility. Runs must not rely on unrecorded random state.

## Citation And Source Claims

Citations, source claims, physics claims, equations, and model-performance claims require review. Codex must not fabricate citations or present unsupported claims as accepted scientific content.

## Open Questions

Open questions should remain explicit in registry/config entries until reviewed and resolved. Unknowns must not be silently filled with assumptions.
