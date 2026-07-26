# Outputs

Generated outputs go under `outputs/runs/<run_id>/`.

All outputs present before the REBUILD baseline are preserved historical
artifacts. They are non-controlling, are not accepted evidence, and must not be
used to select metrics, optimize against unknown test outcomes, or authorize a
new run. Promotion requires an explicit, provenance-preserving A1 evidence
handoff.

Previous outputs must not be overwritten intentionally.

Model results, figures, logs, and tables must include provenance. Technical
validation does not constitute scientific acceptance.
