from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    RevenueGraph,
    RevenueNodeType,
)


@dataclass(frozen=True)
class RevenueGraphIntelligence:
    total_nodes: int
    total_edges: int
    customer_count: int
    order_count: int
    invoice_count: int
    payment_count: int
    payment_link_count: int
    subscription_count: int
    refund_count: int
    settlement_count: int
    dispute_count: int
    payout_count: int
    connected_customer_count: int
    orphan_payment_count: int
    orphan_invoice_count: int
    orphan_order_count: int
    read_only: bool = True
    financial_mutation: bool = False
    provider_mutation: bool = False


def analyze_revenue_graph(
    graph: RevenueGraph,
) -> RevenueGraphIntelligence:

    def count(node_type: RevenueNodeType) -> int:
        return len(
            graph.nodes_of_type(node_type)
        )

    customers = graph.nodes_of_type(
        RevenueNodeType.CUSTOMER
    )

    connected_customers = sum(
        1
        for customer in customers
        if graph.outgoing(customer.node_id)
        or graph.incoming(customer.node_id)
    )

    def orphan_count(
        node_type: RevenueNodeType,
    ) -> int:
        return sum(
            1
            for node in graph.nodes_of_type(node_type)
            if not graph.incoming(node.node_id)
            and not graph.outgoing(node.node_id)
        )

    return RevenueGraphIntelligence(
        total_nodes=len(graph.nodes),
        total_edges=len(graph.edges),
        customer_count=count(
            RevenueNodeType.CUSTOMER
        ),
        order_count=count(
            RevenueNodeType.ORDER
        ),
        invoice_count=count(
            RevenueNodeType.INVOICE
        ),
        payment_count=count(
            RevenueNodeType.PAYMENT
        ),
        payment_link_count=count(
            RevenueNodeType.PAYMENT_LINK
        ),
        subscription_count=count(
            RevenueNodeType.SUBSCRIPTION
        ),
        refund_count=count(
            RevenueNodeType.REFUND
        ),
        settlement_count=count(
            RevenueNodeType.SETTLEMENT
        ),
        dispute_count=count(
            RevenueNodeType.DISPUTE
        ),
        payout_count=count(
            RevenueNodeType.PAYOUT
        ),
        connected_customer_count=(
            connected_customers
        ),
        orphan_payment_count=orphan_count(
            RevenueNodeType.PAYMENT
        ),
        orphan_invoice_count=orphan_count(
            RevenueNodeType.INVOICE
        ),
        orphan_order_count=orphan_count(
            RevenueNodeType.ORDER
        ),
    )
