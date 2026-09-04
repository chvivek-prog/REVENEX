from revenex.audit.decision_trace import (
    build_decision_audit_trace,
    explain_decision,
)
from revenex.decision.engine import decide_recovery


def test_audit_trace_explains_decision():
    decision = decide_recovery(
        100000,
        0.80,
    )

    trace = build_decision_audit_trace(
        decision
    )

    assert trace.decision == decision.recommended_action
    assert trace.scenario is not None
    assert trace.expected_collection > 0
    assert trace.confidence >= 0
    assert len(trace.rationale) >= 3
    assert len(trace.evidence) >= 3


def test_audit_trace_contains_complete_pipeline():
    decision = decide_recovery(
        250000,
        0.70,
    )

    trace = explain_decision(decision)

    assert trace.stages == (
        "OBSERVE",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "EXPLAIN",
        "AUDIT",
    )


def test_audit_trace_is_always_approval_gated():
    decision = decide_recovery(
        500000,
        0.85,
    )

    trace = explain_decision(decision)

    assert trace.requires_approval is True
    assert trace.execution_allowed is False


def test_audit_trace_has_no_mutation():
    decision = decide_recovery(
        500000,
        0.85,
    )

    trace = explain_decision(decision)

    assert trace.automatic_action is False
    assert trace.financial_mutation is False
    assert trace.provider_mutation is False


def test_audit_trace_handles_empty_decision():
    decision = decide_recovery(
        0,
        0,
    )

    trace = explain_decision(decision)

    assert trace.decision == "MONITOR"
    assert trace.scenario is None
    assert trace.expected_collection == 0
    assert trace.execution_allowed is False
