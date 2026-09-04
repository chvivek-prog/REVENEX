
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISMATCH = "MISMATCH"
    MISSING_EXPECTED = "MISSING_EXPECTED"
    MISSING_OBSERVED = "MISSING_OBSERVED"
    MISSING_INTERNAL = "MISSING_INTERNAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class MismatchType(str, Enum):
    NONE = "NONE"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    MISSING_EVENT = "MISSING_EVENT"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    TIMING_MISMATCH = "TIMING_MISMATCH"
    UNKNOWN = "UNKNOWN"


class ReconciliationSeverity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class ReconciliationRecord:
    reconciliation_id: str
    resource_type: str
    resource_id: str
    expected_amount: float | None
    observed_amount: float | None
    internal_amount: float | None
    expected_status: str | None
    observed_status: str | None
    internal_status: str | None
    status: ReconciliationStatus
    mismatch_type: MismatchType
    amount_variance: float | None
    revenue_impact: float
    severity: ReconciliationSeverity
    explanation: str
    requires_human_review: bool
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationReport:
    status: ReconciliationStatus
    total_records: int
    matched_records: int
    partial_records: int
    mismatched_records: int
    missing_records: int
    critical_records: int
    high_records: int
    total_revenue_impact: float
    records: tuple[ReconciliationRecord, ...]
    executive_summary: str
    safety: dict[str, bool]
