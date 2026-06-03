# Dataset Audit

Status: provisional, unverified, pending review.

## Provenance

- Timestamp UTC: `2026-06-03T23:12:14.107435+00:00`
- Command: `scripts/audit_dataset.py --config configs/runs/masses_exclusions_audit.yaml`
- Config path: `configs/runs/masses_exclusions_audit.yaml`
- Dataset path: `data/raw/masses_exclusions.csv`
- Run id: `masses_exclusions_audit`
- Dataset id: `masses_exclusions`

## Summary

- Shape: 12280 rows, 4 columns
- Columns: `mchi1`, `mchipm1`, `Final_CLs`, `exclusion`
- Duplicate rows: 0

## Dtypes

- `mchi1`: `float64`
- `mchipm1`: `float64`
- `Final_CLs`: `float64`
- `exclusion`: `int64`

## Missing Values

- `mchi1`: 0
- `mchipm1`: 0
- `Final_CLs`: 0
- `exclusion`: 0

## Target

- Target column: `exclusion`
- Unique values: ['0', '1']
- Class counts: {'0': 2263, '1': 10017}

## Numeric Summary

- `mchi1`: {'count': 12280, 'min': 0.222243372, 'max': 1936.32098, 'mean': 506.8997794015612, 'std': 369.5868528519316}
- `mchipm1`: {'count': 12280, 'min': 92.0426893, 'max': 1981.43446, 'mean': 708.5308036215229, 'std': 466.9481141042298}
- `Final_CLs`: {'count': 12280, 'min': 0.0, 'max': 1.0, 'mean': 0.6088565005203781, 'std': 0.3982225478960791}
- `exclusion`: {'count': 12280, 'min': 0.0, 'max': 1.0, 'mean': 0.8157166123778502, 'std': 0.38773091565402823}

## Mass Checks

- Negative mass counts: {'mchi1': 0, 'mchipm1': 0}
- Mass ordering check: {'checked': True, 'mchipm1_greater_than_or_equal_mchi1_always': True, 'violations': 0}

## Audit-Only Columns

- Audit-only columns: ['Final_CLs']
- Final_CLs/target correlation: {'columns': ['Final_CLs', 'exclusion'], 'pearson': 0.7181377323447221, 'interpretation': 'Numerical association only; no physics meaning or exclusion rule is inferred.'}

## Notes

- Raw data was read only and not modified.
- Final_CLs is treated as audit-only.
- No exclusion rule is inferred.
- No empirical model performance is claimed.
