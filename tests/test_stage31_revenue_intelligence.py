from revenex.core.revenue_intelligence import (
    IntelligenceStage,
    RevenueState,
    run_revenue_intelligence,
)


def test_stage31_runs_complete_pipeline():
    state = RevenueState(
        invoices=(
            {
                "id": 101,
                "amount": 100000,
                "outstanding_amount": 100000,
                "days_overdue": 60,
            },
        ),
        payments=(),
    )

    result = run_revenue_intelligence(state)

    assert tuple(result.stages) == (
        "OBSERVE",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "AUDIT",
    )


def test_stage31_detects_overdue_risk():
    state = RevenueState(
        invoices=(
            {
                "id": 101,
                "outstanding_amount": 100000,
                "days_overdue": 60,
            },
        )
    )

    result = run_revenue_intelligence(state)

    findings = result.stages["INVESTIGATE"]

    assert len(findings) == 1
    assert findings[0].risk_score >= 0.70


def test_stage31_is_read_only():
    state = RevenueState(
        invoices=(
            {
                "id": 101,
                "outstanding_amount": 100000,
                "days_overdue": 60,
            },
        )
    )

    result = run_revenue_intelligence(state)
    execution = result.execution

    assert execution["read_only"] is True
    assert execution["automatic_action"] is False
    assert execution["provider_mutation"] is False
    assert execution["financial_mutation"] is False


def test_stage31_audit_covers_every_pipeline_stage():
    state = RevenueState()

    result = run_revenue_intelligence(state)
    audit = result.stages["AUDIT"]

    assert audit.stages_completed == tuple(
        stage.value for stage in IntelligenceStage
    )
