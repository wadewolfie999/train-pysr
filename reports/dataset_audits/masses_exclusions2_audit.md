# Dataset Audit: masses_exclusions2

| Field | Value |
|---|---|
| Dataset ID | `masses_exclusions2` |
| File path | `data/raw/masses_exclusions2.csv` |
| File type | CSV raw data |
| Observed header | `mhiggs`, `mchi1`, `mchipm1`, `Final_CLs`, `exclusion` |
| Config path | `configs/datasets/masses_exclusions2.yaml` |
| Apparent status | Audit-only intake |
| Approval state | `requires_review` |

## Documented Roles

| Column | Documented role | Review status |
|---|---|---|
| `mhiggs` | Candidate feature | Requires review. |
| `mchi1` | Candidate feature | Requires review. |
| `mchipm1` | Candidate feature | Requires review. |
| `Final_CLs` | Audit-only | Do not use as feature or target unless explicitly approved. |
| `exclusion` | Provisional binary target | Requires review. |

## Unresolved TODOs

- TODO: confirm whether `mhiggs` is an allowed model feature.
- TODO: confirm units for `mhiggs`, `mchi1`, and `mchipm1`.
- TODO: confirm binary label semantics for `exclusion`.
- TODO: confirm relationship to `masses_exclusions.csv`.
- TODO: define preprocessing, split, metric, and class-imbalance rules.
- TODO: identify nested-sampling or upstream scan provenance, if any.
