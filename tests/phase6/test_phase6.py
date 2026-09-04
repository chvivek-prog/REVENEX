from revenex.phase6 import build_action_plans


def test_plans_are_prioritized():
    report = build_action_plans(
        [
            {
                "opportunity_id": "customer-47",
                "priority": "HIGH",
                "recoverable_value": 100000,
                "confidence": 0.80,
            },
            {
                "opportunity_id": "customer-88",
                "priority": "CRITICAL",
                "recoverable_value": 350000,
                "confidence": 0.90,
            },
        ]
    )

    assert report.total_plans == 2
    assert report.plans[0].opportunity_id == "customer-88"
    assert report.plans[0].sequence == 1
    assert report.plans[0].urgency == "IMMEDIATE"
    assert report.highest_priority == "CRITICAL"


def test_expected_value_is_aggregated():
    report = build_action_plans(
        [
            {
                "opportunity_id": "a",
                "priority": "HIGH",
                "expected_value": 70000,
                "confidence": 0.70,
            },
            {
                "opportunity_id": "b",
                "priority": "MEDIUM",
                "expected_value": 120000,
                "confidence": 0.60,
            },
        ]
    )

    assert report.total_expected_value == 190000


def test_action_type_is_deterministic():
    report = build_action_plans(
        [
            {
                "opportunity_id": "settlement-1",
                "category": "SETTLEMENT_EXCEPTION",
                "priority": "HIGH",
                "expected_value": 50000,
                "confidence": 0.80,
            }
        ]
    )

    assert report.plans[0].action_type == "SETTLEMENT_REVIEW"


def test_governance_never_allows_execution():
    report = build_action_plans(
        [
            {
                "opportunity_id": "customer-88",
                "priority": "CRITICAL",
                "expected_value": 350000,
                "confidence": 0.90,
            }
        ]
    )

    plan = report.plans[0]

    assert report.human_review_required is True
    assert report.read_only is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False

    assert plan.human_review_required is True
    assert plan.read_only is True
    assert plan.execution_allowed is False
    assert plan.automatic_action is False
    assert plan.financial_mutation is False
    assert plan.provider_mutation is False


def test_empty_input_is_safe():
    report = build_action_plans([])

    assert report.total_plans == 0
    assert report.total_expected_value == 0
    assert report.highest_priority == "NONE"
    assert report.execution_allowed is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False
