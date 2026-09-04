from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceQuality:
    score: float
    level: str
    evidence_count: int
    required_fields_present: bool
    source_consistency: float
    stale_data: bool
    human_review_required: bool
    read_only: bool


def _bounded(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0)))
    except (TypeError, ValueError):
        return 0.0


def assess_evidence_quality(
    *,
    evidence_count: int = 0,
    required_fields_present: bool = False,
    source_consistency: Any = 0,
    stale_data: bool = False,
) -> EvidenceQuality:

    count = max(0, int(evidence_count or 0))
    consistency = _bounded(source_consistency)

    count_score = min(1.0, count / 5.0)
    field_score = 1.0 if required_fields_present else 0.0
    freshness_score = 0.0 if stale_data else 1.0

    score = round(
        count_score * 0.30
        + field_score * 0.30
        + consistency * 0.25
        + freshness_score * 0.15,
        4,
    )

    if score >= 0.80:
        level = "HIGH"
    elif score >= 0.60:
        level = "MEDIUM"
    else:
        level = "LOW"

    return EvidenceQuality(
        score=score,
        level=level,
        evidence_count=count,
        required_fields_present=required_fields_present,
        source_consistency=round(consistency, 4),
        stale_data=bool(stale_data),
        human_review_required=True,
        read_only=True,
    )
