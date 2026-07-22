# Plans

This file is a repository-local synchronization of the controlling SR-Res
governance and scientific records. Updating it does not independently ratify,
amend, supersede, close, or LOCK any decision. A1 review remains required.

## Locked Scientific Sequence

The exact nine-act scientific sequence is:

1. Define the exact scientific claim.
2. Audit existing PySR evidence.
3. Lock the validation protocol.
4. Reproduce the current `>0.97` result.
5. Run the stability campaign.
6. Verify and select the reportable result.
7. Freeze the evidence package.
8. Build the professor-facing `.ipynb`.
9. Perform adversarial review and final sign-off.

The sequence is ordered and non-substitutable. The current claim is the
A1-controlled PySR claim defined for the specified pMSSM benchmark. No
scientific acceptance may be inferred from files under `SR-Res-work`.

## Latest A1-Authorized State

| Act | Locked sequence item | Current state and boundary |
| --- | --- | --- |
| 1 | Define the exact scientific claim | `FINISHED — A1 LOCKED`. The claim definition and paired two-feature/three-feature arm decision are controlling records. |
| 2 | Audit existing PySR evidence | `CLOSED BY A1`. The A1-ratified calibration did not reopen the act; no claim-bearing PySR stability evidence was found, and historical unrecovered artifacts remain unverifiable and quarantined. |
| 3 | Lock the validation protocol | `A1 APPROVED AND LOCKED — CLOSED`. `SRRES-VP-1.0.0` is the locked protocol, with the recorded limitation concerning currently unknown grouping information. |
| 4 | Reproduce the current `>0.97` result | `COMPLETED — BOUNDED DIAGNOSTIC REPRODUCTION OBSERVED — EXACT EQUALITY FALSE — STABILITY NOT ESTABLISHED`. The accepted outputs are standard-ML, non-PySR, non-claim-bearing, and quarantined. |
| 5 | Run the stability campaign | The historical campaign is `CAMPAIGN_FAILED — NON-ADJUDICABLE — NO SCIENTIFIC VERDICT`. It is frozen; its opportunity under `SRRES-VP-1.0.0` was consumed and must not be retried, repaired, replaced, or promoted as evidence. |
| 6 | Verify and select the reportable result | `PENDING — UNAUTHORIZED UNTIL REACHED`. No result may be selected or scientifically adjudicated from the failed historical campaign. |
| 7 | Freeze the evidence package | `PENDING — UNAUTHORIZED UNTIL REACHED`. No evidence package may be frozen from the failed campaign or from unactivated replacement work. |
| 8 | Build the professor-facing `.ipynb` | `PENDING — UNAUTHORIZED UNTIL REACHED`. Notebook work must wait for a valid frozen evidence package. |
| 9 | Perform adversarial review and final sign-off | `PENDING — UNAUTHORIZED UNTIL REACHED`. Final sign-off remains an A1 decision. |

## Act 5 Recovery Boundary

A1 approved `SRRES-VP-1.0.1` only as a limited protocol amendment. It:

- freezes the historical Act 5 campaign as failed and non-adjudicable;
- permits preparation for exactly one fresh replacement campaign;
- changes no dataset, feature, target, split, seed, search space, budget,
  selection rule, metric, bootstrap, threshold, or scientific acceptance
  criterion;
- prohibits historical Act 5 outputs from serving as evidence for replacement
  work; and
- requires a new run identity, new directories, fresh splits, a fresh offline
  environment, a clean detached checkout, and a separate final A1 execution
  activation.

This amendment does not authorize the replacement campaign. The only currently
authorized functional work is the bounded no-fit remediation described by A1:
prepare a fresh copy and apply the exact runner correction from
`temp_equation_file=True` to `temp_equation_file=False`, then perform the
specified no-fit checks and return the remediation evidence for A1 review.

Replacement fitting, symbolic search, metric production, outer-test access,
scientific Act 5 execution, and evidence adjudication remain unauthorized
unless a newer explicit A1 activation record exists. Stop before every call to
`fit`.

## Scope Outside the Current Sequence

IDM application, `Ht.csv`, SymbolFit integration, expression-error work, and
broader backend exploration are post-current or separately governed scope.
They must not be presented as substitutes for the controlling nine-act
campaign. PySR is the first backend for this sequence, not the full project
identity.

No dataset registration, feature set, target definition, unit convention,
preprocessing rule, split rule, metric protocol, or class-imbalance strategy
may be changed through this plan. Unknown or unresolved scientific details
remain `TODO` or are escalated to A1.

## Operating Rule

Every future execution in `train-pysr` requires the self-contained,
task-specific A1 authorization described in `AGENTS.md`. Existing evidence,
dirty work, failed runs, timed-out attempts, and historical outputs must be
preserved. These synchronized documents are review-ready operating records,
not final acceptance or execution authority.
