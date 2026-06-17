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

For audit-only intake of a dataset with no reviewed target, `target_column` may
be `null`. That does not assign a modeling target.
