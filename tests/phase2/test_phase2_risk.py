from revenex.phase2 import build_risk_priorities


def test_risk_priorities_are_sorted():
    result = build_risk_priorities(
        [
            {
                "resource_id": "low",
                "exposure": 100,
                "risk_score": 0.20,
            },
            {
                "resource_id": "critical",
                "exposure": 500,
                "risk_score": 0.95,
            },
            {
                "resource_id": "high",
                "exposure": 300,
                "risk_score": 0.70,
            },
        ]
    )

    assert [item.resource_id for item in result] == [
        "critical",
        "high",
        "low",
    ]

    assert result[0].priority == "CRITICAL"
    assert result[1].priority == "HIGH"


def test_risk_is_safe():
    result = build_risk_priorities(
        [
            {
                "resource_id": "customer-1",
                "exposure": 100000,
                "risk_score": 0.90,
            }
        ]
    )[0]

    assert result.human_review_required is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False
