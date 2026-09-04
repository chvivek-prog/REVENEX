from revenex.phase18 import (
    ImpactLevel,
    prioritize_revenue_impact,
)


def test_opportunities_are_prioritized():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "customer-a",
                "exposure": 100000,
                "expected_recovery": 70000,
                "confidence": 0.8,
                "urgency": 0.9,
                "evidence_quality": 0.9,
            },
            {
                "entity_id": "customer-b",
                "exposure": 50000,
                "expected_recovery": 10000,
                "confidence": 0.6,
                "urgency": 0.4,
                "evidence_quality": 0.5,
            },
        ]
    )

    assert report.opportunities_analyzed == 2
    assert report.opportunities[0].entity_id == "customer-a"
    assert report.highest_priority_id == "OPP-0001"


def test_remaining_exposure_is_calculated():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "customer-a",
                "exposure": 100000,
                "expected_recovery": 70000,
                "confidence": 0.8,
                "urgency": 0.9,
                "evidence_quality": 0.9,
            }
        ]
    )

    opportunity = report.opportunities[0]

    assert opportunity.remaining_exposure == 30000


def test_score_is_bounded():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "customer-a",
                "exposure": 100000,
                "expected_recovery": 100000,
                "confidence": 1,
                "urgency": 1,
                "evidence_quality": 1,
            }
        ]
    )

    assert 0 <= report.highest_priority_score <= 1


def test_critical_priority_is_detected():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "critical-customer",
                "exposure": 100000,
                "expected_recovery": 100000,
                "confidence": 1,
                "urgency": 1,
                "evidence_quality": 1,
            }
        ]
    )

    opportunity = report.opportunities[0]

    assert opportunity.impact_level == ImpactLevel.CRITICAL
    assert opportunity.recommended_focus == "IMMEDIATE_REVIEW"


def test_zero_exposure_is_safe():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "zero",
                "exposure": 0,
                "expected_recovery": 50000,
                "confidence": 0,
                "urgency": 0,
                "evidence_quality": 0,
            }
        ]
    )

    opportunity = report.opportunities[0]

    assert opportunity.exposure == 0
    assert opportunity.expected_recovery == 0
    assert opportunity.remaining_exposure == 0


def test_totals_are_aggregated():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "a",
                "exposure": 100000,
                "expected_recovery": 70000,
                "confidence": 0.8,
                "urgency": 0.8,
                "evidence_quality": 0.8,
            },
            {
                "entity_id": "b",
                "exposure": 200000,
                "expected_recovery": 100000,
                "confidence": 0.7,
                "urgency": 0.6,
                "evidence_quality": 0.7,
            },
        ]
    )

    assert report.total_exposure == 300000
    assert report.total_expected_recovery == 170000
    assert report.total_remaining_exposure == 130000


def test_evidence_references_exist():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "customer-a",
                "exposure": 100000,
                "expected_recovery": 50000,
                "confidence": 0.8,
                "urgency": 0.8,
                "evidence_quality": 0.8,
            }
        ]
    )

    assert len(report.opportunities[0].evidence_refs) == 6


def test_governance_is_locked():
    report = prioritize_revenue_impact(
        [
            {
                "entity_id": "customer-a",
                "exposure": 100000,
                "expected_recovery": 50000,
                "confidence": 0.8,
                "urgency": 0.8,
                "evidence_quality": 0.8,
            }
        ]
    )

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False

    for opportunity in report.opportunities:
        assert opportunity.read_only is True
        assert opportunity.human_review_required is True


def test_prioritization_is_deterministic():
    records = [
        {
            "entity_id": "a",
            "exposure": 100000,
            "expected_recovery": 70000,
            "confidence": 0.8,
            "urgency": 0.9,
            "evidence_quality": 0.9,
        },
        {
            "entity_id": "b",
            "exposure": 200000,
            "expected_recovery": 100000,
            "confidence": 0.7,
            "urgency": 0.5,
            "evidence_quality": 0.6,
        },
    ]

    first = prioritize_revenue_impact(records)
    second = prioritize_revenue_impact(records)

    assert first == second
