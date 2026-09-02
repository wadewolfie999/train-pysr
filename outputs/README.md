# Outputs

Generated outputs go under the single `outputs/` namespace. The active
notebook workflow uses:

- `outputs/pysr/<run_id>/` for PySR run artifacts and continuous scores;
- `outputs/auc/<run_id>/` for independent AUC analysis; and
- `outputs/report/` for supervisor-facing exports when required.

Historical `runs/` and `learning_runs/` trees were preserved outside the
repository and are not part of the active notebook workflow:

```text
SR-Workspace/train-pysr-archive-20260902/source-tree/outputs/
```

All outputs present before the REBUILD baseline are preserved historical
artifacts. They are non-controlling, are not accepted evidence, and must not be
used to select metrics, optimize against unknown test outcomes, or authorize a
new run. Promotion requires an explicit, provenance-preserving A1 evidence
handoff.

Previous outputs must not be overwritten intentionally.

Model results, figures, logs, and tables must include provenance. Technical
validation does not constitute scientific acceptance.
