from revenex.phase2 import build_decision_evidence


def test_decision_evidence():
    result = build_decision_evidence(
        decision="AGGRESSIVE_RECOVERY_REVIEW",
        scenario="AGGRESSIVE",
        expected_collection=483120,
        remaining_exposure=66880,
        confidence=0.62,
        evidence=[
            "expected_collection=483120",
            "remaining_exposure=66880",
            "confidence=0.62",
        ],
    )

    assert result.decision == "AGGRESSIVE_RECOVERY_REVIEW"
    assert result.scenario == "AGGRESSIVE"
    assert result.expected_collection == 483120
    assert result.remaining_exposure == 66880
    assert result.confidence == 0.62
    assert result.evidence_count == 3
    assert result.explainable is True


def test_evidence_safety():
    result = build_decision_evidence()

    assert result.human_approval_required is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.read_only is True
