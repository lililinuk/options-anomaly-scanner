from __future__ import annotations

from collections.abc import Sequence

from app.research.forward_outcome import ResearchSampleFoundation


def deterministic_primary_occurrence(
    occurrences: Sequence[ResearchSampleFoundation],
) -> ResearchSampleFoundation | None:
    """Choose one defensive aggregate representative without dropping occurrences."""

    eligible = [row for row in occurrences if row.primary_research_eligible]
    if not eligible:
        return None
    window_keys = {row.outcome_window_key for row in eligible}
    if len(window_keys) != 1:
        raise ValueError("Defensive deduplication requires one outcome window")
    return min(
        eligible,
        key=lambda row: (row.candidate_first_knowledge_at, str(row.product_candidate_id)),
    )
