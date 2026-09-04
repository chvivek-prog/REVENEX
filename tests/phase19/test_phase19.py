from revenex.phase19 import (
    OpportunityLevel,
    detect_revenue_opportunities,
)


def test_opportunity_is_detected():
    report = detect_revenue_opportunities([
        {
            "entity_id": "customer-1",
            "exposure": 100000,
            "expected_recovery": 80000,
            "confidence": 0.9,
            "urgency": 1,
            "evidence_quality": 1,
        }
    ])

    assert report.total_opportunities == 1
    assert report.opportunities[0].entity_id == "customer-1"


def test_critical_opportunity_is_detected():
    report = detect_revenue_opportunities([
        {
            "entity_id": "critical-customer",
            "exposure": 100000,
            "expected_recovery": 100000,
            "confidence": 1,
            "urgency": 1,
            "evidence_quality": 1,
        }
    ])

    opportunity = report.opportunities[0]

    assert opportunity.opportunity_score == 0.75
    assert opportunity.opportunity_level == OpportunityLevel.HIGH
    assert opportunity.recommended_focus == "PRIORITY_REVIEW"


def test_opportunities_are_ranked():
    report = detect_revenue_opportunities([
        {
            "entity_id": "low",
            "exposure": 100000,
            "expected_recovery": 20000,
            "confidence": 0.4,
            "urgency": 0.3,
            "evidence_quality": 0.5,
        },
        {
            "entity_id": "high",
            "exposure": 100000,
            "expected_recovery": 90000,
            "confidence": 1,
            "urgency": 1,
            "evidence_quality": 1,
        },
    ])

    assert report.opportunities[0].entity_id == "high"


def test_safety_boundary():
    report = detect_revenue_opportunities([])

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_evidence_refs_exist():
    report = detect_revenue_opportunities([
        {
            "entity_id": "customer-1",
            "exposure": 50000,
            "expected_recovery": 30000,
            "confidence": 0.8,
            "urgency": 0.7,
            "evidence_quality": 0.9,
        }
    ])

    assert "entity:customer-1" in report.opportunities[0].evidence_refs
    assert "exposure" in report.opportunities[0].evidence_refs
