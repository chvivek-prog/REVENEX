from __future__ import annotations

from typing import Any

from .contracts import (
    RevenueEdge,
    RevenueGraph,
    RevenueNode,
    RevenueNodeType,
)


class RevenueGraphStore:
    """
    Deterministic in-memory graph builder.

    The graph is an intelligence representation.
    It never performs financial or provider mutations.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, RevenueNode] = {}
        self._edges: set[RevenueEdge] = set()

    def add_node(
        self,
        *,
        node_id: str,
        node_type: RevenueNodeType,
        attributes: dict[str, Any] | None = None,
    ) -> RevenueNode:
        node = RevenueNode(
            node_id=str(node_id),
            node_type=node_type,
            attributes=dict(attributes or {}),
        )

        self._nodes[node.node_id] = node
        return node

    def add_edge(
        self,
        *,
        source_id: str,
        target_id: str,
        relationship: str,
    ) -> RevenueEdge:
        if source_id not in self._nodes:
            raise KeyError(
                f"Unknown source node: {source_id}"
            )

        if target_id not in self._nodes:
            raise KeyError(
                f"Unknown target node: {target_id}"
            )

        edge = RevenueEdge(
            source_id=str(source_id),
            target_id=str(target_id),
            relationship=str(relationship),
        )

        self._edges.add(edge)
        return edge

    def build(self) -> RevenueGraph:
        return RevenueGraph(
            nodes=tuple(
                self._nodes[key]
                for key in sorted(self._nodes)
            ),
            edges=tuple(
                sorted(
                    self._edges,
                    key=lambda edge: (
                        edge.source_id,
                        edge.target_id,
                        edge.relationship,
                    ),
                )
            ),
        )


def _id(
    prefix: str,
    value: Any,
) -> str:
    return f"{prefix}:{value}"


def build_revenue_graph(
    *,
    customers: list[dict[str, Any]] | None = None,
    orders: list[dict[str, Any]] | None = None,
    invoices: list[dict[str, Any]] | None = None,
    payments: list[dict[str, Any]] | None = None,
    payment_links: list[dict[str, Any]] | None = None,
    subscriptions: list[dict[str, Any]] | None = None,
    refunds: list[dict[str, Any]] | None = None,
    settlements: list[dict[str, Any]] | None = None,
    disputes: list[dict[str, Any]] | None = None,
    payouts: list[dict[str, Any]] | None = None,
) -> RevenueGraph:

    store = RevenueGraphStore()

    customers = customers or []
    orders = orders or []
    invoices = invoices or []
    payments = payments or []
    payment_links = payment_links or []
    subscriptions = subscriptions or []
    refunds = refunds or []
    settlements = settlements or []
    disputes = disputes or []
    payouts = payouts or []

    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    for item in customers:
        customer_id = str(
            item.get(
                "customer_id",
                item.get("id", ""),
            )
        )

        if customer_id:
            store.add_node(
                node_id=_id("customer", customer_id),
                node_type=RevenueNodeType.CUSTOMER,
                attributes=item,
            )

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    for item in orders:
        order_id = str(
            item.get(
                "order_id",
                item.get("id", ""),
            )
        )

        if not order_id:
            continue

        node_id = _id("order", order_id)

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.ORDER,
            attributes=item,
        )

        customer_id = item.get(
            "customer_id"
        )

        if customer_id:
            customer_node = _id(
                "customer",
                customer_id,
            )

            if store._nodes.get(customer_node):
                store.add_edge(
                    source_id=customer_node,
                    target_id=node_id,
                    relationship="PLACED_ORDER",
                )

    # --------------------------------------------------------
    # Invoices
    # --------------------------------------------------------

    for item in invoices:
        invoice_id = str(
            item.get(
                "invoice_id",
                item.get("id", ""),
            )
        )

        if not invoice_id:
            continue

        node_id = _id(
            "invoice",
            invoice_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.INVOICE,
            attributes=item,
        )

        customer_id = item.get(
            "customer_id"
        )

        if customer_id:
            customer_node = _id(
                "customer",
                customer_id,
            )

            if customer_node in store._nodes:
                store.add_edge(
                    source_id=customer_node,
                    target_id=node_id,
                    relationship="OWES_INVOICE",
                )

        order_id = item.get(
            "order_id"
        )

        if order_id:
            order_node = _id(
                "order",
                order_id,
            )

            if order_node in store._nodes:
                store.add_edge(
                    source_id=order_node,
                    target_id=node_id,
                    relationship="GENERATED_INVOICE",
                )

    # --------------------------------------------------------
    # Payments
    # --------------------------------------------------------

    for item in payments:
        payment_id = str(
            item.get(
                "payment_id",
                item.get("id", ""),
            )
        )

        if not payment_id:
            continue

        node_id = _id(
            "payment",
            payment_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.PAYMENT,
            attributes=item,
        )

        customer_id = item.get(
            "customer_id"
        )

        if customer_id:
            customer_node = _id(
                "customer",
                customer_id,
            )

            if customer_node in store._nodes:
                store.add_edge(
                    source_id=customer_node,
                    target_id=node_id,
                    relationship="MADE_PAYMENT",
                )

        order_id = item.get(
            "order_id"
        )

        if order_id:
            order_node = _id(
                "order",
                order_id,
            )

            if order_node in store._nodes:
                store.add_edge(
                    source_id=order_node,
                    target_id=node_id,
                    relationship="PAID_ORDER",
                )

        invoice_id = item.get(
            "invoice_id"
        )

        if invoice_id:
            invoice_node = _id(
                "invoice",
                invoice_id,
            )

            if invoice_node in store._nodes:
                store.add_edge(
                    source_id=invoice_node,
                    target_id=node_id,
                    relationship="SETTLES_INVOICE",
                )

    # --------------------------------------------------------
    # Payment Links
    # --------------------------------------------------------

    for item in payment_links:
        link_id = str(
            item.get(
                "payment_link_id",
                item.get("id", ""),
            )
        )

        if not link_id:
            continue

        node_id = _id(
            "payment_link",
            link_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.PAYMENT_LINK,
            attributes=item,
        )

        customer_id = item.get(
            "customer_id"
        )

        if customer_id:
            customer_node = _id(
                "customer",
                customer_id,
            )

            if customer_node in store._nodes:
                store.add_edge(
                    source_id=customer_node,
                    target_id=node_id,
                    relationship="RECEIVES_PAYMENT_LINK",
                )

    # --------------------------------------------------------
    # Subscriptions
    # --------------------------------------------------------

    for item in subscriptions:
        subscription_id = str(
            item.get(
                "subscription_id",
                item.get("id", ""),
            )
        )

        if not subscription_id:
            continue

        node_id = _id(
            "subscription",
            subscription_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.SUBSCRIPTION,
            attributes=item,
        )

        customer_id = item.get(
            "customer_id"
        )

        if customer_id:
            customer_node = _id(
                "customer",
                customer_id,
            )

            if customer_node in store._nodes:
                store.add_edge(
                    source_id=customer_node,
                    target_id=node_id,
                    relationship="HAS_SUBSCRIPTION",
                )

    # --------------------------------------------------------
    # Refunds
    # --------------------------------------------------------

    for item in refunds:
        refund_id = str(
            item.get(
                "refund_id",
                item.get("id", ""),
            )
        )

        if not refund_id:
            continue

        node_id = _id(
            "refund",
            refund_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.REFUND,
            attributes=item,
        )

        payment_id = item.get(
            "payment_id"
        )

        if payment_id:
            payment_node = _id(
                "payment",
                payment_id,
            )

            if payment_node in store._nodes:
                store.add_edge(
                    source_id=payment_node,
                    target_id=node_id,
                    relationship="REFUNDED_BY",
                )

    # --------------------------------------------------------
    # Settlements
    # --------------------------------------------------------

    for item in settlements:
        settlement_id = str(
            item.get(
                "settlement_id",
                item.get("id", ""),
            )
        )

        if not settlement_id:
            continue

        node_id = _id(
            "settlement",
            settlement_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.SETTLEMENT,
            attributes=item,
        )

        payment_id = item.get(
            "payment_id"
        )

        if payment_id:
            payment_node = _id(
                "payment",
                payment_id,
            )

            if payment_node in store._nodes:
                store.add_edge(
                    source_id=payment_node,
                    target_id=node_id,
                    relationship="SETTLED_AS",
                )

    # --------------------------------------------------------
    # Disputes
    # --------------------------------------------------------

    for item in disputes:
        dispute_id = str(
            item.get(
                "dispute_id",
                item.get("id", ""),
            )
        )

        if not dispute_id:
            continue

        node_id = _id(
            "dispute",
            dispute_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.DISPUTE,
            attributes=item,
        )

        payment_id = item.get(
            "payment_id"
        )

        if payment_id:
            payment_node = _id(
                "payment",
                payment_id,
            )

            if payment_node in store._nodes:
                store.add_edge(
                    source_id=payment_node,
                    target_id=node_id,
                    relationship="DISPUTED_PAYMENT",
                )

    # --------------------------------------------------------
    # Payouts
    # --------------------------------------------------------

    for item in payouts:
        payout_id = str(
            item.get(
                "payout_id",
                item.get("id", ""),
            )
        )

        if not payout_id:
            continue

        node_id = _id(
            "payout",
            payout_id,
        )

        store.add_node(
            node_id=node_id,
            node_type=RevenueNodeType.PAYOUT,
            attributes=item,
        )

    return store.build()
