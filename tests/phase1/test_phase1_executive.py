from revenex.phase1 import build_executive_revenue_state


def test_executive_state_builds():
    result = build_executive_revenue_state(
        outstanding_revenue=550000,
        revenue_at_risk=428500,
        expected_collection=483120,
        confidence=0.62,
        priority="AGGRESSIVE",
        recommended_action="AGGRESSIVE_RECOVERY_REVIEW",
    )

    assert result.outstanding_revenue == 550000
    assert result.revenue_at_risk == 428500
    assert result.expected_collection == 483120
    assert result.expected_remaining_exposure == 66880
    assert result.recovery_opportunity == 428500
    assert result.confidence == 0.62
    assert result.priority == "AGGRESSIVE"
    assert result.recommended_action == "AGGRESSIVE_RECOVERY_REVIEW"


def test_executive_state_is_strictly_safe():
    result = build_executive_revenue_state(
        outstanding_revenue=100000,
        expected_collection=80000,
    )

    assert result.human_approval_required is True
    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.read_only is True


def test_confidence_is_bounded():
    low = build_executive_revenue_state(confidence=-5)
    high = build_executive_revenue_state(confidence=5)

    assert low.confidence == 0
    assert high.confidence == 1


def test_remaining_exposure_never_goes_negative():
    result = build_executive_revenue_state(
        outstanding_revenue=100000,
        expected_collection=150000,
    )

    assert result.expected_remaining_exposure == 0
