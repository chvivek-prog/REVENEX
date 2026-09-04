from revenex.phase20 import (
    InterventionLevel,
    InterventionType,
    recommend_interventions,
)


def test_intervention_is_created():
    report = recommend_interventions([
        {
            "entity_id": "customer-1",
            "exposure": 100000,
            "expected_recovery": 60000,
            "confidence": 0.8,
            "urgency": 0.9,
            "evidence_quality": 1,
        }
    ])

    assert report.total_interventions == 1
    assert report.interventions[0].entity_id == "customer-1"


def test_high_urgency_recovery_review():
    report = recommend_interventions([
        {
            "entity_id": "customer-critical",
            "exposure": 100000,
            "expected_recovery": 80000,
            "confidence": 1,
            "urgency": 1,
            "evidence_quality": 1,
        }
    ])

    item = report.interventions[0]

    assert item.intervention_type == InterventionType.RECOVERY_REVIEW
    assert item.intervention_level if hasattr(item, "intervention_level") else True
    assert item.level == InterventionLevel.HIGH
    assert item.intervention_score == 0.75
    assert item.recommended_focus == "PRIORITY_HUMAN_REVIEW"


def test_low_evidence_requires_data_review():
    report = recommend_interventions([
        {
            "entity_id": "weak-data",
            "exposure": 100000,
            "expected_recovery": 50000,
            "confidence": 0.5,
            "urgency": 0.5,
            "evidence_quality": 0,
        }
    ])

    assert (
        report.interventions[0].intervention_type
        == InterventionType.DATA_REVIEW
    )


def test_interventions_are_ranked():
    report = recommend_interventions([
        {
            "entity_id": "low",
            "exposure": 100000,
            "expected_recovery": 10000,
            "confidence": 0.3,
            "urgency": 0.2,
            "evidence_quality": 0.3,
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

    assert report.interventions[0].entity_id == "high"


def test_safety_boundary():
    report = recommend_interventions([])

    assert report.read_only is True
    assert report.human_review_required is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_evidence_refs_are_present():
    report = recommend_interventions([
        {
            "entity_id": "customer-2",
            "exposure": 50000,
            "expected_recovery": 25000,
            "confidence": 0.8,
            "urgency": 0.8,
            "evidence_quality": 0.9,
        }
    ])

    refs = report.interventions[0].evidence_refs

    assert "entity:customer-2" in refs
    assert "exposure" in refs
    assert "expected_recovery" in refs
