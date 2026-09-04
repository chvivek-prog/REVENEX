from revenex.phase3 import build_dashboard_view_model


def test_dashboard_view_model():
    result = build_dashboard_view_model(
        outstanding_revenue=550000,
        revenue_at_risk=428500,
        expected_collection=483120,
        confidence=0.62,
        risk_level="HIGH",
        scenario="AGGRESSIVE",
        recommended_action="AGGRESSIVE_RECOVERY_REVIEW",
    )

    assert result.title == "REVENEX Revenue Command Center"
    assert result.outstanding_revenue == 550000
    assert result.revenue_at_risk == 428500
    assert result.expected_collection == 483120
    assert result.remaining_exposure == 66880
    assert result.confidence == 0.62
    assert result.risk_level == "HIGH"
    assert result.scenario == "AGGRESSIVE"
    assert result.recommended_action == "AGGRESSIVE_RECOVERY_REVIEW"
    assert result.decision_status == "ADVISORY"


def test_dashboard_pipeline():
    result = build_dashboard_view_model()

    assert result.pipeline == (
        "OBSERVE",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "EXPLAIN",
        "AUDIT",
        "OUTCOME",
        "LEARN",
    )


def test_dashboard_safety():
    result = build_dashboard_view_model()

    assert result.human_approval_required is True
    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
    assert result.read_only is True


def test_dashboard_serialization():
    result = build_dashboard_view_model(
        outstanding_revenue=100000,
        expected_collection=75000,
        confidence=0.80,
    )

    data = result.to_dict()

    assert data["outstanding_revenue"] == 100000
    assert data["remaining_exposure"] == 25000
    assert data["confidence"] == 0.80
    assert data["execution_allowed"] is False
