# Run Configurations

Run configs define reproducible repository tasks.

Each run config must declare:

- run id;
- dataset id;
- dataset config path;
- task type;
- feature columns;
- target column;
- random seed if applicable;
- output directory;
- review status.

Run configs are provisional until executed, verified, and reviewed.

No run config is active execution authority during `REBUILD`. The
pre-REBUILD PySR baseline candidate is preserved at
`configs/runs/masses_exclusions_pysr_baseline_v1.yaml`, with choices and
compatibility rules in `configs/pysr/switch_registry.yaml`. A4 may use or
technically validate a panel only under an exact A1-approved contract; technical
validation is not scientific acceptance.

For audit-only intake of a dataset with no reviewed target, `target_column` may
be `null`. That does not assign a modeling target.
