from revenex.phase15 import (
    OpportunityPriority,
    identify_revenue_opportunities,
)


def test_opportunities_are_identified():
    report = identify_revenue_opportunities(
        [
            {
                "customer_id": "customer-47",
                "exposure": 150000,
                "risk_score": 0.80,
                "confidence": 0.90,
                "recoverable_amount": 120000,
            },
            {
                "customer_id": "customer-88",
                "exposure": 400000,
                "risk_score": 0.90,
                "confidence": 0.80,
                "recoverable_amount": 320000,
            },
        ]
    )

    assert len(report.opportunities) == 2
    assert report.total_opportunity == 440000
    assert report.highest_priority_customer == "customer-88"


def test_priority_is_deterministic():
    report = identify_revenue_opportunities(
        [
            {
                "customer_id": "customer-critical",
                "exposure": 100000,
                "risk_score": 1.0,
                "confidence": 1.0,
                "recoverable_amount": 90000,
            }
        ]
    )

    opportunity = report.opportunities[0]

    assert opportunity.priority == OpportunityPriority.CRITICAL
    assert opportunity.opportunity_score == 1.0


def test_opportunities_are_ranked():
    report = identify_revenue_opportunities(
        [
            {
                "customer_id": "low",
                "exposure": 100000,
                "risk_score": 0.20,
                "confidence": 0.20,
                "recoverable_amount": 20000,
            },
            {
                "customer_id": "high",
                "exposure": 300000,
                "risk_score": 0.90,
                "confidence": 0.90,
                "recoverable_amount": 250000,
            },
        ]
    )

    assert report.opportunities[0].customer_id == "high"


def test_recoverable_amount_can_be_derived():
    report = identify_revenue_opportunities(
        [
            {
                "customer_id": "customer-1",
                "exposure": 100000,
                "risk_score": 0.80,
                "confidence": 0.80,
                "recovery_rate": 0.50,
            }
        ]
    )

    assert report.opportunities[0].recoverable_amount == 50000


def test_zero_exposure_is_ignored():
    report = identify_revenue_opportunities(
        [
            {
                "customer_id": "customer-zero",
                "exposure": 0,
                "risk_score": 1.0,
                "confidence": 1.0,
            }
        ]
    )

    assert report.opportunities == ()
    assert report.total_opportunity == 0


def test_governance_is_locked():
    report = identify_revenue_opportunities(
        [
            {
                "customer_id": "customer-1",
                "exposure": 100000,
                "risk_score": 0.8,
                "confidence": 0.8,
                "recoverable_amount": 50000,
            }
        ]
    )

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False

    opportunity = report.opportunities[0]

    assert opportunity.read_only is True
    assert opportunity.human_review_required is True


def test_opportunity_analysis_is_deterministic():
    customers = [
        {
            "customer_id": "customer-a",
            "exposure": 200000,
            "risk_score": 0.70,
            "confidence": 0.80,
            "recoverable_amount": 100000,
        },
        {
            "customer_id": "customer-b",
            "exposure": 300000,
            "risk_score": 0.80,
            "confidence": 0.90,
            "recoverable_amount": 200000,
        },
    ]

    first = identify_revenue_opportunities(customers)
    second = identify_revenue_opportunities(customers)

    assert first == second
