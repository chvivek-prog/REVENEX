from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryAnalysis:
    payment_id: str
    status: str
    failure_type: str
    failure_reason: str
    amount: float
    recovery_probability: float
    strategy: str
    rationale: str
    requires_human_approval: bool = True
    read_only: bool = True
    automatic_action: bool = False
    financial_mutation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
