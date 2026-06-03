# Codex Review Checklist

Use this checklist when reviewing Codex-generated files, scripts, plots, equations, metrics, and documentation. All checklist recommendations are provisional, unverified, and pending review.

## Scientific Review

- Physics correctness has been reviewed by the thesis author.
- Physics conventions have not drifted silently.
- Equations, derivations, and interpretations are marked provisional until accepted.
- Citations and source claims are real, relevant, and not fabricated.
- Unsupported claims have been removed or marked pending review.

## Dataset And Target Review

- Dataset registration matches the reviewed dataset config.
- Dataset-specific assumptions are not hard-coded outside registry/config entries.
- Feature columns match the approved feature list.
- Target column and target-label semantics match the approved target definition.
- Audit-only columns are not used as features or targets without approval.
- No binary target has been silently converted to multiclass classification.

## Evaluation Review

- ROC/AUC is computed from continuous scores, not hard class labels.
- Thresholded predictions are reported separately from ROC/AUC inputs.
- Class-imbalance handling is explicit and reproducible.
- Train/test split rule and random seeds are recorded.
- Metrics are not claimed as empirical results unless produced by an actual reviewed run.

## Artifact And Reproducibility Review

- Raw datasets are preserved unchanged.
- Original notebooks are preserved unchanged.
- Generated outputs do not overwrite prior outputs.
- Run logs include dataset id, config id, code version, random seeds, split rule, features, target, preprocessing, metrics, and output paths.
- Model artifacts are stored in generated output locations.
- Temporary PySR outputs are not treated as accepted results without review.
