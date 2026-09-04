from revenex.revenue_graph import (
    RevenueNodeType,
    analyze_revenue_graph,
    build_revenue_graph,
)


def test_revenue_graph_connects_customer_order_invoice_payment():
    graph = build_revenue_graph(
        customers=[
            {
                "customer_id": "c1",
                "name": "Customer 1",
            }
        ],
        orders=[
            {
                "order_id": "o1",
                "customer_id": "c1",
            }
        ],
        invoices=[
            {
                "invoice_id": "i1",
                "customer_id": "c1",
                "order_id": "o1",
            }
        ],
        payments=[
            {
                "payment_id": "p1",
                "customer_id": "c1",
                "order_id": "o1",
                "invoice_id": "i1",
                "amount": 100000,
            }
        ],
    )

    assert len(graph.nodes) == 4
    assert len(graph.edges) == 6

    assert graph.node(
        "customer:c1"
    ).node_type == RevenueNodeType.CUSTOMER

    assert graph.node(
        "payment:p1"
    ).node_type == RevenueNodeType.PAYMENT

    assert any(
        edge.relationship == "PLACED_ORDER"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "GENERATED_INVOICE"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "SETTLES_INVOICE"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "PLACED_ORDER"
        and edge.source_id == "customer:c1"
        and edge.target_id == "order:o1"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "OWES_INVOICE"
        and edge.source_id == "customer:c1"
        and edge.target_id == "invoice:i1"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "GENERATED_INVOICE"
        and edge.source_id == "order:o1"
        and edge.target_id == "invoice:i1"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "MADE_PAYMENT"
        and edge.source_id == "customer:c1"
        and edge.target_id == "payment:p1"
        for edge in graph.edges
    )

    assert any(
        edge.relationship == "PAID_ORDER"
        and edge.source_id == "order:o1"
        and edge.target_id == "payment:p1"
        for edge in graph.edges
    )


def test_subscription_refund_settlement_dispute_payout():
    graph = build_revenue_graph(
        customers=[
            {"customer_id": "c1"}
        ],
        payments=[
            {
                "payment_id": "p1",
                "customer_id": "c1",
            }
        ],
        subscriptions=[
            {
                "subscription_id": "s1",
                "customer_id": "c1",
            }
        ],
        refunds=[
            {
                "refund_id": "r1",
                "payment_id": "p1",
            }
        ],
        settlements=[
            {
                "settlement_id": "st1",
                "payment_id": "p1",
            }
        ],
        disputes=[
            {
                "dispute_id": "d1",
                "payment_id": "p1",
            }
        ],
        payouts=[
            {
                "payout_id": "po1",
            }
        ],
    )

    report = analyze_revenue_graph(graph)

    assert report.customer_count == 1
    assert report.payment_count == 1
    assert report.subscription_count == 1
    assert report.refund_count == 1
    assert report.settlement_count == 1
    assert report.dispute_count == 1
    assert report.payout_count == 1
    assert report.connected_customer_count == 1
    assert report.read_only is True
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_orphan_detection():
    graph = build_revenue_graph(
        payments=[
            {
                "payment_id": "orphan-payment",
                "amount": 100,
            }
        ],
        invoices=[
            {
                "invoice_id": "orphan-invoice",
                "amount": 100,
            }
        ],
        orders=[
            {
                "order_id": "orphan-order",
                "amount": 100,
            }
        ],
    )

    report = analyze_revenue_graph(graph)

    assert report.orphan_payment_count == 1
    assert report.orphan_invoice_count == 1
    assert report.orphan_order_count == 1


def test_graph_is_deterministic():
    kwargs = {
        "customers": [
            {"customer_id": "c1"}
        ],
        "orders": [
            {
                "order_id": "o1",
                "customer_id": "c1",
            }
        ],
        "payments": [
            {
                "payment_id": "p1",
                "customer_id": "c1",
                "order_id": "o1",
            }
        ],
    }

    first = build_revenue_graph(**kwargs)
    second = build_revenue_graph(**kwargs)

    assert first == second
