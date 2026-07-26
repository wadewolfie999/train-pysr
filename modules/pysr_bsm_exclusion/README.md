# PySR BSM Exclusion Module

Status: **HISTORICAL MODULE CONTEXT — NON-CONTROLLING DURING REBUILD**

The module contents preserve pre-REBUILD technical context. They do not
activate a discovery pass, fit, metric run, or search.

This module organizes the first stabilized symbolic-regression backend for the
current binary exclusion dataset. It is part of the broader IDM
symbolic-regression framework and does not define the whole project.

## Dataset and Baseline

- Dataset id: `masses_exclusions`
- Raw path: `data/raw/masses_exclusions.csv`
- Baseline features: `mchi1`, `mchipm1`
- Target: binary `exclusion`
- `Final_CLs`: audit-only and forbidden from the baseline feature/target path

The editable panel and switch registry expose preprocessing, operator, loss,
complexity, budget, runtime, and output choices before Julia initialization.
No unary operator is selected by default.

## Current Boundary

The historical discovery pass performed configuration, numerical-domain,
preprocessing, leakage, and environment checks only. It did not authorize a
PySR fit. Future expressions, metrics, and physics interpretations remain
provisional until explicitly accepted by A1.
