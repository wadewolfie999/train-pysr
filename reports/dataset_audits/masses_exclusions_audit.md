# Dataset Audit: masses_exclusions

| Field | Value |
|---|---|
| Dataset ID | `masses_exclusions` |
| File path | `data/raw/masses_exclusions.csv` |
| File type | CSV raw data |
| Observed header | `mchi1`, `mchipm1`, `Final_CLs`, `exclusion` |
| Config path | `configs/datasets/masses_exclusions.yaml` |
| Apparent status | Registered modeled dataset |
| Approval state | `requires_review` |

## Documented Roles

| Column | Documented role | Review status |
|---|---|---|
| `mchi1` | Feature | Units and physics meaning require review. |
| `mchipm1` | Feature | Units and physics meaning require review. |
| `Final_CLs` | Audit-only | Do not use as feature or target unless explicitly approved. |
| `exclusion` | Binary target | Label semantics require review. |

## Unresolved TODOs

- TODO: confirm units for `mchi1` and `mchipm1`.
- TODO: confirm binary label semantics for `exclusion`.
- TODO: define preprocessing, split, metric, and class-imbalance rules.
- TODO: identify nested-sampling or upstream scan provenance, if any.
