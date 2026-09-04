from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RevenueNodeType(str, Enum):
    CUSTOMER = "CUSTOMER"
    ORDER = "ORDER"
    INVOICE = "INVOICE"
    PAYMENT = "PAYMENT"
    PAYMENT_LINK = "PAYMENT_LINK"
    SUBSCRIPTION = "SUBSCRIPTION"
    REFUND = "REFUND"
    SETTLEMENT = "SETTLEMENT"
    DISPUTE = "DISPUTE"
    PAYOUT = "PAYOUT"
    WEBHOOK_EVENT = "WEBHOOK_EVENT"


@dataclass(frozen=True)
class RevenueNode:
    node_id: str
    node_type: RevenueNodeType
    attributes: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class RevenueEdge:
    source_id: str
    target_id: str
    relationship: str


@dataclass(frozen=True)
class RevenueGraph:
    nodes: tuple[RevenueNode, ...]
    edges: tuple[RevenueEdge, ...]

    def node(
        self,
        node_id: str,
    ) -> RevenueNode | None:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def outgoing(
        self,
        node_id: str,
    ) -> tuple[RevenueEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.source_id == node_id
        )

    def incoming(
        self,
        node_id: str,
    ) -> tuple[RevenueEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.target_id == node_id
        )

    def nodes_of_type(
        self,
        node_type: RevenueNodeType,
    ) -> tuple[RevenueNode, ...]:
        return tuple(
            node
            for node in self.nodes
            if node.node_type == node_type
        )
