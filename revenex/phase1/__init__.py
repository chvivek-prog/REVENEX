"""REVENEX Phase 1 — additive selection-ready intelligence."""

from .executive import (
    ExecutiveRevenueState,
    build_executive_revenue_state,
)
from .demo import (
    DemoScenario,
    get_demo_scenarios,
    get_demo_scenario,
)

__all__ = [
    "ExecutiveRevenueState",
    "build_executive_revenue_state",
    "DemoScenario",
    "get_demo_scenarios",
    "get_demo_scenario",
]
