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

The active PySR baseline uses a commented human-editable panel at
`configs/runs/masses_exclusions_pysr_baseline_v1.yaml`. Allowed choices,
classifications, defaults, and compatibility rules are declared separately in
`configs/pysr/switch_registry.yaml`. Validate a panel with `--dry-run` before
initializing Julia or starting a fit.

For audit-only intake of a dataset with no reviewed target, `target_column` may
be `null`. That does not assign a modeling target.
