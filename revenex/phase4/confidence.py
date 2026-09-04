from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfidenceAssessment:
    confidence: float
    level: str
    evidence_score: float
    data_completeness: float
    consistency_score: float
    requires_review: bool
    read_only: bool


def _bounded(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0)))
    except (TypeError, ValueError):
        return 0.0


def assess_confidence(
    *,
    evidence_score: Any = 0,
    data_completeness: Any = 0,
    consistency_score: Any = 0,
) -> ConfidenceAssessment:

    evidence = _bounded(evidence_score)
    completeness = _bounded(data_completeness)
    consistency = _bounded(consistency_score)

    confidence = round(
        evidence * 0.40
        + completeness * 0.35
        + consistency * 0.25,
        4,
    )

    if confidence >= 0.80:
        level = "HIGH"
    elif confidence >= 0.60:
        level = "MEDIUM"
    else:
        level = "LOW"

    return ConfidenceAssessment(
        confidence=confidence,
        level=level,
        evidence_score=round(evidence, 4),
        data_completeness=round(completeness, 4),
        consistency_score=round(consistency, 4),
        requires_review=True,
        read_only=True,
    )
