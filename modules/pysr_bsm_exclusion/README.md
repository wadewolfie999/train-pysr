# PySR BSM Exclusion Module

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

The current discovery pass performs configuration, numerical-domain,
preprocessing, leakage, and environment checks only. It must not call a PySR
fit. Future expressions, metrics, and physics interpretations remain
provisional until reviewed by the thesis author.
