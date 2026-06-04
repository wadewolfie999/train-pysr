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

## `evaluate_ml_baselines(dataset_id, run_config)`

Status: provisional, unverified, pending review.

- Load `run_config` and confirm it references `dataset_id`.
- Use only configured features and target.
- Compute ROC/AUC from continuous scores only.
- Record dataset id, config path, raw path, split rule, seed, feature set, target, class-imbalance handling, command, output path, and review status.
- Write metrics and ROC curve data to the configured run output directory without overwriting prior outputs.

Current initial command:

```bash
python scripts/evaluate_binary_classifiers.py --config configs/runs/masses_exclusions_eval.yaml
```

## `prepare_pysr_auc_search(dataset_id, run_config)`

Status: provisional, unverified, pending review.

- Review `run_config` for dataset id, feature set, target, split rule, seed, objective, PySR options, and output path.
- Confirm `Final_CLs` is not used as a feature.
- Use `--dry-run` before launching PySR training.

Current dry-run command:

```bash
python scripts/train_pysr_auc_search.py --config configs/runs/masses_exclusions_pysr_search.yaml --dry-run
```

## `run_pysr_auc_search(dataset_id, run_config)`

Status: provisional, unverified, pending review.

- Run only after review of the PySR config and search budget.
- Use balanced sample weights and the configured stratified split.
- Save equations, metrics, ROC curve data, metadata, and any model artifact only under the configured output directory.
- Treat any observed AUC as a run result pending review, not an accepted thesis result.

## `review_auc_results(run_id)`

Status: provisional, unverified, pending review.

- Confirm ROC/AUC was computed from continuous scores, not hard labels.
- Check dataset id, feature set, target, split rule, random seed, class-imbalance handling, metric implementation, output path, and code version.
- Verify whether any AUC > 0.97 statement is written only as observed in the run and pending review.
- Accept, reject, or supersede results only after thesis-author review.

## `log_run(run_id)`

Status: provisional, unverified, pending review.

- Record dataset id, config id, code version, random seeds, split rule, feature columns, target column, preprocessing, metrics, environment details, output paths, and review status.
- Store logs in generated run-log locations without overwriting prior logs.

## `review_results(run_id)`

Status: provisional, unverified, pending review.

- Check scientific correctness, convention consistency, dataset registration consistency, target and feature definitions, metric protocol, class-imbalance handling, reproducibility metadata, citation support, and output preservation.
- Mark results accepted, rejected, or requiring revision only after thesis-author review.
