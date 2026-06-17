# Data Directory

Raw datasets are preserved unchanged.

Each raw dataset must be registered in `configs/datasets/`.

Raw files must not be overwritten. Derived datasets must be written outside `data/raw/`.

Current intake-only raw datasets:

- `data/raw/masses_exclusions2.csv`: provisional related mass/exclusion dataset with added `mhiggs`.
- `data/raw/Ht.csv`: provisional distinct likelihood/parameter-style dataset with no assigned target.

These intake datasets require review before any modeling target, feature set, split rule, or metric protocol is assigned.
