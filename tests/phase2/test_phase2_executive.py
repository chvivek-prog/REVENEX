from revenex.phase2 import build_executive_dashboard


def test_executive_dashboard():
    result = build_executive_dashboard(
        outstanding_revenue=550000,
        revenue_at_risk=428500,
        expected_collection=483120,
        confidence=0.62,
        recommended_action="AGGRESSIVE_RECOVERY_REVIEW",
    )

    assert result.outstanding_revenue == 550000
    assert result.revenue_at_risk == 428500
    assert result.expected_collection == 483120
    assert result.remaining_exposure == 66880
    assert result.recovery_opportunity == 428500
    assert result.confidence == 0.62
    assert result.recommended_action == "AGGRESSIVE_RECOVERY_REVIEW"
    assert result.decision_status == "ADVISORY"


def test_executive_safety():
    result = build_executive_dashboard(
        outstanding_revenue=100000,
        revenue_at_risk=50000,
        expected_collection=40000,
    )

    assert result.human_approval_required is True
    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.read_only is True
