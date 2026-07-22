# Dataset Audit Reports

## Purpose

This directory stores lightweight dataset audit reports based on repository
metadata and safe header/schema inspection.

## Status

Reports here are audit evidence only. They do not approve datasets, features,
targets, labels, units, preprocessing, split rules, metrics, or
class-imbalance strategies for modeling.

## Expected Report Content

Each report should include:

- dataset id;
- file path;
- file type;
- observed header;
- apparent dataset status;
- documented or unknown role;
- known audit-only columns;
- unresolved TODOs;
- review status.

## Current Reports

| Dataset ID | Report | Status |
|---|---|---|
| `masses_exclusions` | `masses_exclusions_audit.md` | Header and config metadata audit. |
| `masses_exclusions2` | `masses_exclusions2_audit.md` | Header and config metadata audit. |
| `ht` | `ht_audit.md` | Header and config metadata audit. |
