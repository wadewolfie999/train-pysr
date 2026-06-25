# Conventions

This file records current scientific, computational, and workflow conventions
for the repository. Codex-generated conventions and recommendations are
provisional, unverified, and pending review until accepted by the thesis author.

## Project Framing Conventions

The repository is an IDM symbolic-regression research framework.

PySR is the first symbolic-regression backend. PySR is not the full project
identity.

SymbolFit, Operon/C++, native C++, and native Rust are later backend workstreams
or exploratory implementation paths.

## Workstream Naming

Use these names:

- `Workstream I - Main Workstream`
- `Workstream II - Extra Workstream`

Workstream I is thesis-critical. Workstream II is exploratory and must not
block Workstream I.

Priority rule:

```text
Main Workstream > Operon Probe > Native C++ > Native Rust
```

## Phase Naming

Use this format:

```text
Workstream <I|II> / Phase <number> - <title>
```

Examples:

```text
Workstream I / Phase 0 - Repository Framing
Workstream I / Phase 1 - Data and Physics
Workstream II / Phase 1 - C++ Implementation - Operon
```

## Report Naming

Use descriptive filenames that include the workstream, phase, and report role.

Preferred pattern:

```text
docs/<workstream>-phase-<number>-<topic>.md
```

Canonical roadmap:

```text
docs/ROADMAP_IDM_SYMBOLIC_REGRESSION.md
```

Project brief:

```text
docs/PROJECT_BRIEF.md
```

## Config Naming

Run configs should preserve the existing config-driven pattern:

```text
configs/runs/<dataset_id>_<backend_or_task>_<purpose>.yaml
```

Dataset registry/config entries should preserve explicit dataset ids, target
definitions, feature sets, split rules, metric protocols, class-imbalance
handling, output paths, and review status.

TODO: confirm final config naming conventions for SymbolFit, Operon/C++,
native C++, and native Rust backends.

## Output Folder Naming

Generated outputs should continue to live under output directories, not raw
data paths.

Preferred pattern:

```text
outputs/runs/<dataset_id>_<backend_or_task>_<run_id>/
```

Generated outputs are not accepted scientific results until reviewed.

TODO: confirm whether backend-specific output subdirectories are required.

## Terminology

### IDM

IDM means Inert Doublet Model.

TODO: confirm the exact thesis-approved IDM notation, parameter names, units,
and physics constraints before using them in modeling claims.

### Symbolic Regression

Symbolic regression is the backend-assisted search for interpretable analytic
expressions that map reviewed inputs to reviewed targets or scores.

TODO: confirm the thesis-approved description before using it in supervisor-
facing scientific text.

### Backend

A backend is an implementation used to run symbolic-regression search or a
closely related candidate-expression workflow. Backend-specific behavior must
not silently change dataset, feature, target, metric, or split semantics.

### PySR Backend

The PySR backend is the first symbolic-regression backend in Workstream I. It
is the first workflow to stabilize before later backend comparisons.

### SymbolFit Backend

The SymbolFit backend is a later Workstream I backend intended to mimic the
reviewed PySR workflow where appropriate.

TODO: confirm SymbolFit installation, interface, supported objective functions,
and output format before implementation.

### Operon/C++ Backend

The Operon/C++ backend belongs to Workstream II as an exploratory probe. It
must not block the thesis-critical Workstream I path.

TODO: confirm Operon dependency, build, licensing, and interface constraints.

### Native C++ Backend

Native C++ is a lower-priority Workstream II exploratory implementation path.

TODO: confirm whether native C++ is intended as a production backend, prototype,
or rejection study.

### Native Rust Backend

Native Rust is a lower-priority Workstream II exploratory implementation path.

TODO: confirm whether native Rust is intended as a production backend,
prototype, or rejection study.

### Viability Boundary

A viability boundary is the reviewed boundary between model points or regions
that are considered viable and non-viable under the selected target definition.

TODO: confirm the exact target semantics, physics meaning, and review authority
for each dataset before using this term in claims.

### Symbolic Score Function

A symbolic score function is a symbolic expression that returns a continuous
score for evaluation or ranking. ROC/AUC must be computed from continuous
scores, not hard labels.

TODO: confirm whether each backend will produce scores, class labels, symbolic
expressions, or multiple artifacts.

### Nested-Sampling Output

Nested-sampling output is upstream data generation or preprocessing evidence
when it appears in the workflow. It is not the symbolic-regression model.

TODO: identify which repository datasets, if any, are directly derived from
nested-sampling outputs and record that provenance in reviewed configs or docs.

## Dataset Registry Conventions

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

Dataset-specific assumptions must live in dataset registry or configuration
entries. Adding a new dataset requires a registry/config update and review.

## Dataset Registry

### `masses_exclusions`

- Dataset id: `masses_exclusions`
- Raw path: `data/raw/masses_exclusions.csv`
- Observed shape: 12280 rows, 4 columns
- Observed columns: `mchi1`, `mchipm1`, `Final_CLs`, `exclusion`
- Default features: `mchi1`, `mchipm1`
- Target: binary `exclusion`
- `Final_CLs`: audit-only unless explicitly approved as a feature or target
- Missing values observed: none
- Duplicate rows observed: 0
- Observed class counts: `0` = 2263, `1` = 10017
- Approval status: requires review
- Open questions: units, label semantics details, preprocessing rules,
  train/test split rule, metric protocol details, class-imbalance strategy

No derivation rule for `exclusion` is asserted here.

## Feature And Target Approval

Feature columns and target columns must be declared in dataset registry/config
entries. Changes require review before use in training, evaluation, or
scientific interpretation.

Audit-only columns must not be used as features or targets unless explicitly
approved.

## Target-Label Semantics

Each dataset must define what each target label means. Binary, multiclass, and
continuous targets must be handled as distinct target definitions. The current
`masses_exclusions` target is binary exclusion; it must not be converted to
multiclass classification without review.

## Units

Units must be declared per dataset and per relevant column when known. Unknown
units must be marked `TODO` or `requires_review`.

## ROC/AUC Rule

ROC/AUC must be computed from continuous scores, never hard class labels.
Thresholded labels may be used for accuracy and confusion matrix reporting only.

AUC > 0.97 is an aspirational target for `masses_exclusions`, not a claim unless
proven by an actual reviewed run.

## Class-Imbalance Handling

Class imbalance must be handled explicitly and reproducibly. The strategy must
be declared per run in the dataset config or run config and recorded in run
metadata.

Acceptable initial methods include sample weighting or model-native class
weighting. Synthetic oversampling in physical mass space requires review before
use.

## Random Seeds And Split Recording

Train/test split rules and random seeds must be recorded for reproducibility.
Runs must not rely on unrecorded random state.

## Citation And Source Claims

Citations, source claims, physics claims, equations, and model-performance
claims require review. Codex must not fabricate citations or present unsupported
claims as accepted scientific content.

## Open Questions

Open questions should remain explicit in registry/config entries until reviewed
and resolved. Unknowns must not be silently filled with assumptions.
