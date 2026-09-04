from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LeakageSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LeakageType(str, Enum):
    UNPAID_INVOICE = "UNPAID_INVOICE"
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"
    PAYMENT_MISMATCH = "PAYMENT_MISMATCH"
    REFUND_EXPOSURE = "REFUND_EXPOSURE"
    DISPUTE_EXPOSURE = "DISPUTE_EXPOSURE"
    SETTLEMENT_GAP = "SETTLEMENT_GAP"
    ORPHAN_PAYMENT = "ORPHAN_PAYMENT"
    ORPHAN_INVOICE = "ORPHAN_INVOICE"
    ORPHAN_ORDER = "ORPHAN_ORDER"


@dataclass(frozen=True)
class RevenueLeakage:
    leakage_id: str
    leakage_type: LeakageType
    severity: LeakageSeverity
    entity_type: str
    entity_id: str
    expected_amount: float
    observed_amount: float
    leakage_amount: float
    explanation: str
    evidence: tuple[str, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


@dataclass(frozen=True)
class RevenueLeakageReport:
    total_leakage_amount: float
    leakage_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    unpaid_invoice_exposure: float
    partial_payment_exposure: float
    payment_mismatch_exposure: float
    refund_exposure: float
    dispute_exposure: float
    settlement_gap_exposure: float
    orphan_exposure: float
    executive_summary: str
    leakages: tuple[RevenueLeakage, ...]
    human_review_required: bool = True
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False
