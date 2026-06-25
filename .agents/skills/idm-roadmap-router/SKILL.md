---
name: idm-roadmap-router
description: Use when a prompt mentions project direction, next tasks, roadmap, phases, backends, PySR, SymbolFit, Operon, C++, Rust, dataset work, or physics documentation. Do not use for unrelated mechanical edits.
---

# IDM Roadmap Router

Use this skill to route work to the approved project structure.

## Workstream I - Main Workstream

1. Phase 0: Repository Framing
2. Phase 1: Data and Physics
3. Phase 2: Existing Codebase Triage
4. Phase 3: PySR Baseline Stabilization
5. Phase 4: Optimizing PySR
6. Phase 5: Mimic the PySR workflow for SymbolFit

## Workstream II - Extra Workstream

1. Phase 1: C++ Implementation - Operon
2. Phase 2: C++ Implementation - Native
3. Phase 3: Rust Implementation - Native

## Priority Rule

```text
Main Workstream > Operon Probe > Native C++ > Native Rust
```

## Routing Rules

- Treat PySR as the first backend, not the project identity.
- Treat SymbolFit as a later backend after PySR workflow stabilization.
- Treat Operon, native C++, and native Rust as exploratory backends.
- Treat nested sampling as upstream data generation or preprocessing, not symbolic regression itself.
- Do not execute Workstream II prematurely before the PySR baseline is stable and scientifically meaningful.
- If the prompt is ambiguous, route to the earliest applicable Workstream I phase and report the assumption.
