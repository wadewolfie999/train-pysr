"""Deterministic expression selection rules from SRRES-VP-1.0.0 §§8.4–8.6."""

from __future__ import annotations

from typing import Any


def select_within_front(
    expressions: list[dict[str, Any]],
    tolerance: float = 0.002000,
) -> dict[str, Any] | None:
    """Select one representative from a single configuration's Pareto front.

    expressions items must contain:
      - expression_id
      - configuration_id
      - complexity (int/float)
      - weighted_loss (float)
      - inner_validation_auc (float)
      - canonical_expression (str)
      - eligible (bool)
    """
    eligible = [e for e in expressions if e.get("eligible")]
    if not eligible:
        return None
    max_auc = max(float(e["inner_validation_auc"]) for e in eligible)
    retained = [
        e for e in eligible if float(e["inner_validation_auc"]) >= max_auc - tolerance
    ]
    retained.sort(
        key=lambda e: (
            int(e["complexity"]),
            float(e["weighted_loss"]),
            str(e["canonical_expression"]),
            str(e["configuration_id"]),
        )
    )
    chosen = dict(retained[0])
    chosen["selection_trace"] = {
        "rule": "SRRES-VP-1.0.0 §8.5 within-front",
        "eligible_count": len(eligible),
        "max_inner_validation_auc": max_auc,
        "tolerance": tolerance,
        "retained_count": len(retained),
        "chosen_expression_id": chosen["expression_id"],
        "tiebreak_order": [
            "lowest_complexity",
            "lowest_weighted_loss",
            "lexicographic_canonical_expression",
            "ascending_configuration_id",
        ],
    }
    return chosen


def rank_stage_a_representatives(
    representatives: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank Stage-A configuration representatives for advancement."""
    valid = [r for r in representatives if r is not None]
    valid.sort(
        key=lambda e: (
            -float(e["inner_validation_auc"]),
            int(e["complexity"]),
            float(e["weighted_loss"]),
            str(e["configuration_id"]),
        )
    )
    return valid


def advance_stage_a(
    representatives: list[dict[str, Any] | None],
) -> dict[str, Any]:
    ranked = rank_stage_a_representatives([r for r in representatives if r is not None])
    advanced = ranked[:2]
    return {
        "valid_configuration_count": len(ranked),
        "advanced_configuration_ids": [a["configuration_id"] for a in advanced],
        "advanced": advanced,
        "bundle_failed_no_valid_stage_a": len(ranked) == 0,
        "rule": "SRRES-VP-1.0.0 §8.6",
    }


def select_final_expression(
    stage_b_expressions: list[dict[str, Any]],
    tolerance: float = 0.002000,
) -> dict[str, Any] | None:
    """Select final expression from both Stage-B fronts combined."""
    return select_within_front(stage_b_expressions, tolerance=tolerance)
