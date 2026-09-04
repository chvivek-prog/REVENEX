from revenex.phase20.risk_propagation import (
    PropagationLevel,
    analyze_risk_propagation,
)


def test_propagation_detects_remaining_exposure():
    report = analyze_risk_propagation([
        {
            "entity_id": "customer-1",
            "exposure": 100000,
            "expected_recovery": 60000,
            "urgency": 1,
            "confidence": 1,
            "evidence_quality": 1,
        }
    ])

    item = report.propagations[0]

    assert item.direct_exposure == 100000
    assert item.remaining_exposure == 40000
    assert item.propagated_exposure == 80000
    assert item.risk_path[-1] == "SYSTEM_EXPOSURE"


def test_concentration_is_detected():
    report = analyze_risk_propagation([
        {
            "entity_id": "dominant",
            "exposure": 400000,
            "expected_recovery": 100000,
            "urgency": 1,
            "confidence": 1,
        },
        {
            "entity_id": "small",
            "exposure": 100000,
            "expected_recovery": 50000,
            "urgency": 0.5,
            "confidence": 0.8,
        },
    ])

    dominant = report.propagations[0]

    assert dominant.entity_id == "dominant"
    assert dominant.concentration_ratio == 0.8


def test_high_propagation_is_ranked_first():
    report = analyze_risk_propagation([
        {
            "entity_id": "small",
            "exposure": 10000,
            "expected_recovery": 5000,
            "urgency": 0.2,
            "confidence": 0.5,
        },
        {
            "entity_id": "large",
            "exposure": 90000,
            "expected_recovery": 10000,
            "urgency": 1,
            "confidence": 1,
        },
    ])

    assert report.propagations[0].entity_id == "large"


def test_dependencies_are_explainable():
    report = analyze_risk_propagation([
        {
            "entity_id": "customer-88",
            "exposure": 100000,
            "expected_recovery": 20000,
            "urgency": 1,
            "confidence": 1,
        }
    ])

    dependency = report.propagations[0].dependencies[0]

    assert dependency.source_id == "customer-88"
    assert dependency.target_id == "revenue-system"
    assert dependency.relationship == "REVENUE_EXPOSURE_TO_SYSTEM"
    assert dependency.evidence_ref == "entity:customer-88"


def test_safety_boundary():
    report = analyze_risk_propagation([])

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False
