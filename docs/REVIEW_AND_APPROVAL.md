# Review And Approval Protocol

## Scope

This protocol defines how outputs from Codex, scripts, notebooks, and model runs become accepted repository material.

## Review Authority

The thesis author is the final scientific authority. Codex cannot approve its own output. ChatGPT may assist with reasoning and review but does not replace author approval.

Supervisor instructions and cited sources override AI-generated content.

## Review Classes

- Documentation and governance.
- Dataset and configuration changes.
- Source code and scripts.
- Notebook-derived outputs.
- Model runs and metrics.
- Symbolic equations.
- Plots and tables.
- Scientific claims and interpretations.

## Required Evidence By Output Type

Documentation must identify scope, assumptions, open questions, and review status.

Code and configuration must identify inputs, outputs, dependencies, command or entry point, and verification checks.

Results must identify dataset id, config id, command used, output path, metric protocol, and reproducibility metadata.

## Acceptance States

- `draft`
- `implemented`
- `verified`
- `reviewed`
- `accepted`
- `rejected`
- `superseded`

## Rejection Criteria

Reject or revise outputs that:

- invent physics assumptions, citations, derivations, or empirical performance;
- change features, targets, labels, units, split rules, preprocessing, metrics, or class-imbalance handling without explicit review;
- compute ROC/AUC from hard class labels;
- overwrite raw data or previous outputs;
- lack required reproducibility evidence;
- make unsupported scientific claims.

## Scientific-Claim Review

Scientific claims require evidence and review before acceptance. Claims must be marked provisional, unverified, and pending review until accepted by the thesis author.

## Code/Config Review

Dataset and configuration changes require explicit review if they affect features, targets, labels, units, split rules, preprocessing, metrics, or class-imbalance handling.

Code/config review should check repository conventions, dataset registry consistency, reproducibility metadata, output paths, and non-overwrite behavior.

## Result/Metric Review

ROC/AUC claims require:

- continuous scores, not hard labels;
- dataset id;
- feature set;
- target;
- split rule;
- random seed;
- class-imbalance handling;
- metric implementation;
- output path;
- code version or commit hash.

Threshold-dependent metrics such as accuracy and confusion matrices must be reported separately from ROC/AUC.

## Plot/Table Review

Plots and tables require:

- generating script or command;
- input data source;
- output path;
- caption draft;
- review status.

## Symbolic Equation Review

Symbolic equations require:

- source model/run id;
- expression form;
- variables defined;
- domain/units stated or marked `requires_review`;
- validation metrics;
- review status.

## Commit Policy

Commits should contain reviewed operational truth. Codex must not commit unless explicitly instructed. Accepted commits should avoid historical transcript dumps and unsupported scientific claims.

## Standard Review Record Template

```text
review_id:
date:
reviewer:
output_type:
files_or_paths:
source_command_or_run_id:
dataset_id:
config_id:
code_version_or_commit:
status:
evidence_checked:
issues_found:
decision:
follow_up:
notes:
```

Recommendations in this protocol are provisional, unverified, and pending review.
