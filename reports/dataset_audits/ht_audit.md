# Dataset Audit: ht

| Field | Value |
|---|---|
| Dataset ID | `ht` |
| File path | `data/raw/Ht.csv` |
| File type | CSV raw data |
| Observed header | `Prob`, `logLik`, `M_S`, `M_R`, `M_Y`, `laL`, `omega`, `invBr`, `lilithLogl`, `PsiCross`, `vctc`, `logM_S`, `logM_R`, `delMA`, `delMC`, `logvt`, `Chi2` |
| Config path | `configs/datasets/ht.yaml` |
| Apparent status | Audit-only intake |
| Approval state | `requires_review` |

## Documented Roles

All observed columns are documented as unassigned and requiring review. No
target or approved feature set is assigned.

## Unresolved TODOs

- TODO: confirm the scientific meaning and units of each column.
- TODO: confirm whether this dataset has a target variable, likelihood
  objective, or filtering rule.
- TODO: confirm whether any columns are derived from or aliases of other
  columns.
- TODO: define preprocessing and modeling task only after supervisor review.
- TODO: identify nested-sampling or upstream scan provenance, if any.
