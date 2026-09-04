
"""
REVENEX Phase 14 — Advanced Simulation Engine.

Simulation is strictly READ-ONLY.

It estimates revenue outcomes under different strategies
without mutating invoices, payments, customers, providers,
financial state, or models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SimulationScenario(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"
    CUSTOM = "CUSTOM"


class SimulationRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class SimulationResult:
    scenario: SimulationScenario

    expected_collection: float
    remaining_exposure: float
    confidence: float

    risk: SimulationRisk

    recovery_strategy: str
    pricing_strategy: str
    discount_strategy: str
    payment_retry_strategy: str
    collection_timing: str
    cash_management: str

    evidence: tuple[str, ...]

    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False
    execution_allowed: bool = False
    automatic_action: bool = False
    human_approval_required: bool = True


# Deterministic strategy profiles.
#
# These are intentionally conservative development values.
# They are NOT claims of real-world performance.

_PROFILES = {
    SimulationScenario.CONSERVATIVE: {
        "collection_rate": 0.79,
        "confidence": 0.76,
        "risk": SimulationRisk.LOW,
        "recovery_strategy": "LOW_PRESSURE_RECOVERY",
        "pricing_strategy": "PRICE_PROTECTION",
        "discount_strategy": "MINIMAL_DISCOUNT",
        "payment_retry_strategy": "LIMITED_RETRY",
        "collection_timing": "EXTENDED_COLLECTION_WINDOW",
        "cash_management": "LIQUIDITY_PROTECTION",
    },
    SimulationScenario.BALANCED: {
        "collection_rate": 0.84,
        "confidence": 0.70,
        "risk": SimulationRisk.MEDIUM,
        "recovery_strategy": "BALANCED_RECOVERY",
        "pricing_strategy": "STANDARD_PRICING",
        "discount_strategy": "TARGETED_DISCOUNT",
        "payment_retry_strategy": "STANDARD_RETRY",
        "collection_timing": "STANDARD_COLLECTION_WINDOW",
        "cash_management": "BALANCED_LIQUIDITY",
    },
    SimulationScenario.AGGRESSIVE: {
        "collection_rate": 0.8784,
        "confidence": 0.62,
        "risk": SimulationRisk.HIGH,
        "recovery_strategy": "AGGRESSIVE_RECOVERY",
        "pricing_strategy": "FLEXIBLE_PRICING",
        "discount_strategy": "AGGRESSIVE_DISCOUNT",
        "payment_retry_strategy": "AGGRESSIVE_RETRY",
        "collection_timing": "ACCELERATED_COLLECTION",
        "cash_management": "MAXIMIZE_NEAR_TERM_CASH",
    },
}


def _money(value: Any) -> float:
    try:
        return max(0.0, float(value or 0.0))
    except (TypeError, ValueError):
        return 0.0


def _custom_profile(
    custom: dict[str, Any] | None,
) -> dict[str, Any]:

    custom = custom or {}

    rate = custom.get(
        "collection_rate",
        0.84,
    )

    confidence = custom.get(
        "confidence",
        0.65,
    )

    return {
        "collection_rate": max(
            0.0,
            min(1.0, float(rate)),
        ),
        "confidence": max(
            0.0,
            min(1.0, float(confidence)),
        ),
        "risk": SimulationRisk(
            custom.get(
                "risk",
                SimulationRisk.MEDIUM.value,
            )
        ),
        "recovery_strategy": custom.get(
            "recovery_strategy",
            "CUSTOM_RECOVERY",
        ),
        "pricing_strategy": custom.get(
            "pricing_strategy",
            "CUSTOM_PRICING",
        ),
        "discount_strategy": custom.get(
            "discount_strategy",
            "CUSTOM_DISCOUNT",
        ),
        "payment_retry_strategy": custom.get(
            "payment_retry_strategy",
            "CUSTOM_RETRY",
        ),
        "collection_timing": custom.get(
            "collection_timing",
            "CUSTOM_TIMING",
        ),
        "cash_management": custom.get(
            "cash_management",
            "CUSTOM_CASH_MANAGEMENT",
        ),
    }


def simulate_revenue(
    total_outstanding: float,
    *,
    scenario: SimulationScenario | str = SimulationScenario.BALANCED,
    custom: dict[str, Any] | None = None,
) -> SimulationResult:
    """
    Simulate a revenue recovery scenario.

    This function NEVER writes to persistent state.
    """

    if not isinstance(
        scenario,
        SimulationScenario,
    ):
        scenario = SimulationScenario(
            str(scenario).upper()
        )

    outstanding = _money(
        total_outstanding
    )

    if scenario == SimulationScenario.CUSTOM:
        profile = _custom_profile(custom)
    else:
        profile = dict(
            _PROFILES[scenario]
        )

    expected = round(
        outstanding
        * float(profile["collection_rate"]),
        2,
    )

    remaining = round(
        max(
            0.0,
            outstanding - expected,
        ),
        2,
    )

    evidence = (
        f"scenario={scenario.value}",
        f"outstanding={outstanding:.2f}",
        f"collection_rate="
        f"{float(profile['collection_rate']):.4f}",
        f"expected_collection={expected:.2f}",
        f"remaining_exposure={remaining:.2f}",
        f"confidence="
        f"{float(profile['confidence']):.4f}",
        "simulation=READ_ONLY",
        "financial_mutation=false",
        "provider_mutation=false",
    )

    return SimulationResult(
        scenario=scenario,
        expected_collection=expected,
        remaining_exposure=remaining,
        confidence=float(
            profile["confidence"]
        ),
        risk=profile["risk"],
        recovery_strategy=profile[
            "recovery_strategy"
        ],
        pricing_strategy=profile[
            "pricing_strategy"
        ],
        discount_strategy=profile[
            "discount_strategy"
        ],
        payment_retry_strategy=profile[
            "payment_retry_strategy"
        ],
        collection_timing=profile[
            "collection_timing"
        ],
        cash_management=profile[
            "cash_management"
        ],
        evidence=evidence,
    )


def simulate_scenarios(
    total_outstanding: float,
    *,
    custom: dict[str, Any] | None = None,
) -> tuple[SimulationResult, ...]:
    """
    Run the standard scenario set.

    Order is deterministic:
    CONSERVATIVE → BALANCED → AGGRESSIVE → CUSTOM
    """

    return tuple(
        simulate_revenue(
            total_outstanding,
            scenario=scenario,
            custom=custom,
        )
        for scenario in (
            SimulationScenario.CONSERVATIVE,
            SimulationScenario.BALANCED,
            SimulationScenario.AGGRESSIVE,
            SimulationScenario.CUSTOM,
        )
    )
