from revenex.phase8 import run_intelligence_pipeline


def test_full_intelligence_pipeline():
    result = run_intelligence_pipeline(
        [
            {
                "resource_id": "customer-88",
                "category": "REVENUE_RECOVERY",
                "exposure": 400000,
                "recoverable_value": 350000,
                "probability": 0.90,
                "urgency": 0.90,
                "confidence": 0.90,
                "evidence_quality": 0.95,
            },
            {
                "resource_id": "customer-47",
                "category": "REVENUE_RECOVERY",
                "exposure": 150000,
                "recoverable_value": 100000,
                "probability": 0.60,
                "urgency": 0.60,
                "confidence": 0.70,
                "evidence_quality": 0.80,
            },
        ]
    )

    assert result.status == "COMPLETE"
    assert result.total_opportunities == 2
    assert result.total_action_plans == 2
    assert result.total_decisions == 2
    assert result.highest_priority == "CRITICAL"

    assert (
        result.pipeline.opportunities.opportunities[0]
        .opportunity_id
        == "customer-88"
    )

    assert (
        result.pipeline.action_plans.plans[0]
        .opportunity_id
        == "customer-88"
    )

    assert (
        result.pipeline.decision_trace.traces[0]
        .decision
        == "REVENUE_RECOVERY_REVIEW"
    )


def test_pipeline_preserves_governance():
    result = run_intelligence_pipeline(
        [
            {
                "resource_id": "customer-1",
                "exposure": 500000,
                "recoverable_value": 300000,
                "probability": 0.90,
                "urgency": 0.90,
                "confidence": 0.80,
                "evidence_quality": 0.90,
            }
        ]
    )

    assert result.human_review_required is True
    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.automatic_action is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False

    assert (
        result.pipeline.opportunities.execution_allowed
        is False
    )

    assert (
        result.pipeline.action_plans.execution_allowed
        is False
    )

    assert (
        result.pipeline.decision_trace.execution_allowed
        is False
    )


def test_pipeline_is_safe_with_empty_input():
    result = run_intelligence_pipeline([])

    assert result.status == "COMPLETE"
    assert result.total_opportunities == 0
    assert result.total_action_plans == 0
    assert result.total_decisions == 0
    assert result.highest_priority == "NONE"
    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_pipeline_contains_auditable_chain():
    result = run_intelligence_pipeline(
        [
            {
                "resource_id": "audit-1",
                "exposure": 200000,
                "recoverable_value": 120000,
                "probability": 0.70,
                "urgency": 0.70,
                "confidence": 0.75,
                "evidence_quality": 0.80,
            }
        ]
    )

    opportunity = (
        result.pipeline.opportunities.opportunities[0]
    )
    plan = result.pipeline.action_plans.plans[0]
    trace = result.pipeline.decision_trace.traces[0]

    assert opportunity.opportunity_id == "audit-1"
    assert plan.opportunity_id == "audit-1"
    assert trace.trace_id == plan.plan_id
    assert len(trace.evidence) >= 3
    assert trace.human_review_required is True
