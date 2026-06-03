# Repo Workflows

These workflows are concise operational recipes for this repository. Untested workflows are provisional, unverified, and pending review.

## `audit_dataset(dataset_id, run_config)`

Status: provisional, unverified, pending review.

- Load the run config for `run_config`.
- Confirm the run config dataset id matches `dataset_id`.
- Load the dataset registry entry referenced by the run config.
- Verify the raw path exists without modifying raw data.
- Check declared columns against the raw dataset schema.
- Confirm feature columns, target column, audit-only columns, units, label semantics, preprocessing rules, split rule, metric protocol, class-imbalance strategy, approval status, and open questions.
- Write findings to a new generated audit output without overwriting prior outputs.

Current initial command:

```bash
python scripts/audit_dataset.py --config configs/runs/masses_exclusions_audit.yaml
```

This workflow remains provisional until executed and reviewed.

## `train_pysr(dataset_id, config_id)`

Status: provisional, unverified, pending review.

- Load dataset metadata from `dataset_id`.
- Load run configuration from `config_id`.
- Use only approved feature and target definitions.
- Apply only declared preprocessing, split, random seed, and class-imbalance strategy.
- Preserve raw data and original notebooks unchanged.
- Save model artifacts and run metadata to a new run-specific output location.

## `evaluate_auc(run_id)`

Status: provisional, unverified, pending review.

- Load the recorded run metadata and model outputs for `run_id`.
- Compute ROC/AUC from continuous scores, not hard class labels.
- Record the score source, split, target semantics, and any thresholding separately.
- Treat results as empirical claims only after review.

## `compare_ml_baselines(dataset_id, config_id)`

Status: provisional, unverified, pending review.

- Load the same reviewed dataset and config definitions used for PySR comparison.
- Train standard machine-learning baselines under the same split and metric protocol.
- Record class-imbalance handling and random seeds.
- Compare metrics without changing the registered target or feature set.

## `log_run(run_id)`

Status: provisional, unverified, pending review.

- Record dataset id, config id, code version, random seeds, split rule, feature columns, target column, preprocessing, metrics, environment details, output paths, and review status.
- Store logs in generated run-log locations without overwriting prior logs.

## `review_results(run_id)`

Status: provisional, unverified, pending review.

- Check scientific correctness, convention consistency, dataset registration consistency, target and feature definitions, metric protocol, class-imbalance handling, reproducibility metadata, citation support, and output preservation.
- Mark results accepted, rejected, or requiring revision only after thesis-author review.
