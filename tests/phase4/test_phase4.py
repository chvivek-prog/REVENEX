from revenex.phase4 import (
    assess_confidence,
    assess_evidence_quality,
    calculate_revenue_health,
    prioritize_opportunities,
)


def test_revenue_health():
    result = calculate_revenue_health(
        outstanding_revenue=550000,
        revenue_at_risk=428500,
        expected_collection=483120,
    )

    assert result.outstanding_revenue == 550000
    assert result.revenue_at_risk == 428500
    assert result.expected_collection == 483120
    assert result.remaining_exposure == 66880
    assert 0 <= result.score <= 100


def test_health_safety():
    result = calculate_revenue_health(
        outstanding_revenue=100000,
        revenue_at_risk=50000,
        expected_collection=40000,
    )

    assert result.human_review_required is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.read_only is True


def test_confidence():
    result = assess_confidence(
        evidence_score=0.9,
        data_completeness=0.8,
        consistency_score=0.7,
    )

    assert result.confidence == 0.815
    assert result.level == "HIGH"
    assert result.requires_review is True
    assert result.read_only is True


def test_opportunity_prioritization():
    result = prioritize_opportunities(
        [
            {
                "resource_id": "low",
                "exposure": 100000,
                "probability": 0.30,
                "urgency": 0.20,
            },
            {
                "resource_id": "high",
                "exposure": 400000,
                "probability": 0.90,
                "urgency": 0.90,
            },
        ]
    )

    assert result[0].resource_id == "high"
    assert result[0].priority == "CRITICAL"
    assert result[0].expected_value == 360000


def test_opportunity_safety():
    result = prioritize_opportunities(
        [
            {
                "resource_id": "customer-1",
                "exposure": 100000,
                "probability": 0.80,
                "urgency": 0.80,
            }
        ]
    )[0]

    assert result.human_review_required is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_evidence_quality():
    result = assess_evidence_quality(
        evidence_count=5,
        required_fields_present=True,
        source_consistency=1.0,
        stale_data=False,
    )

    assert result.score == 1.0
    assert result.level == "HIGH"
    assert result.human_review_required is True
    assert result.read_only is True


def test_low_evidence_is_detected():
    result = assess_evidence_quality(
        evidence_count=0,
        required_fields_present=False,
        source_consistency=0,
        stale_data=True,
    )

    assert result.level == "LOW"
    assert result.score == 0.0
