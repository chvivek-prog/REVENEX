
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlTowerResponse:
    executive_state: str
    priority: str
    revenue: dict[str, Any]
    operations: dict[str, Any]
    customer_revenue: dict[str, Any]
    risk: dict[str, Any]
    learning: dict[str, Any]
    pipeline: list[str]
    safety: dict[str, bool]
    read_only: bool
    executive_summary: str
