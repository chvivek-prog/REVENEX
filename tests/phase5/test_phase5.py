from revenex.phase5 import analyze_opportunities


def test_opportunity_is_ranked():
    report = analyze_opportunities(
        [
            {
                "resource_id": "customer-88",
                "exposure": 400000,
                "recoverable_value": 350000,
                "probability": 0.90,
                "urgency": 0.90,
                "confidence": 0.90,
                "evidence_quality": 0.95,
            },
            {
                "resource_id": "customer-47",
                "exposure": 150000,
                "recoverable_value": 100000,
                "probability": 0.60,
                "urgency": 0.60,
                "confidence": 0.70,
                "evidence_quality": 0.80,
            },
        ]
    )

    assert report.total_opportunities == 2
    assert report.opportunities[0].opportunity_id == "customer-88"
    assert report.opportunities[0].priority == "CRITICAL"


def test_report_aggregates_value():
    report = analyze_opportunities(
        [
            {
                "id": "a",
                "exposure": 100000,
                "recoverable_value": 70000,
                "probability": 0.5,
                "urgency": 0.5,
                "confidence": 0.5,
                "evidence_quality": 0.5,
            },
            {
                "id": "b",
                "exposure": 200000,
                "recoverable_value": 120000,
                "probability": 0.6,
                "urgency": 0.6,
                "confidence": 0.6,
                "evidence_quality": 0.7,
            },
        ]
    )

    assert report.total_exposure == 300000
    assert report.total_recoverable_value == 190000


def test_low_confidence_does_not_become_automatic():
    report = analyze_opportunities(
        [
            {
                "id": "review-1",
                "exposure": 500000,
                "recoverable_value": 100000,
                "probability": 0.9,
                "urgency": 0.9,
                "confidence": 0.1,
                "evidence_quality": 0.1,
            }
        ]
    )

    result = report.opportunities[0]

    assert result.human_review_required is True
    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_empty_input_is_safe():
    report = analyze_opportunities([])

    assert report.total_opportunities == 0
    assert report.total_exposure == 0
    assert report.total_recoverable_value == 0
    assert report.highest_priority == "NONE"
    assert report.read_only is True
    assert report.execution_allowed is False
