from revenex.phase7 import build_decision_trace


def test_decision_trace_contains_reasoning_evidence_and_risk():
    report = build_decision_trace(
        [
            {
                "decision_id": "decision-88",
                "decision": "AGGRESSIVE_RECOVERY_REVIEW",
                "scenario": "AGGRESSIVE",
                "confidence": 0.62,
                "expected_collection": 483120,
                "remaining_exposure": 66880,
                "evidence": [
                    "expected_collection=483120",
                    "remaining_exposure=66880",
                ],
                "risks": [
                    "customer concentration",
                    "collection uncertainty",
                ],
                "alternatives": [
                    "MODERATE_RECOVERY_REVIEW",
                    "PASSIVE_MONITORING",
                ],
            }
        ]
    )

    trace = report.traces[0]

    assert trace.trace_id == "decision-88"
    assert trace.decision == "AGGRESSIVE_RECOVERY_REVIEW"
    assert trace.scenario == "AGGRESSIVE"
    assert trace.confidence == 0.62
    assert trace.expected_value == 483120
    assert trace.remaining_exposure == 66880
    assert len(trace.evidence) == 2
    assert len(trace.risks) == 2
    assert len(trace.alternatives) == 2
    assert trace.human_review_required is True
    assert trace.read_only is True


def test_low_confidence_requires_human_review():
    report = build_decision_trace(
        [
            {
                "decision_id": "low-confidence",
                "decision": "REVIEW",
                "scenario": "UNKNOWN",
                "confidence": 0.20,
                "expected_value": 100000,
                "remaining_exposure": 90000,
                "evidence": [],
            }
        ]
    )

    trace = report.traces[0]

    assert trace.governance_state == "HUMAN_REVIEW_REQUIRED"
    assert trace.human_review_required is True
    assert trace.execution_allowed is False
    assert trace.automatic_action is False
    assert trace.financial_mutation is False
    assert trace.provider_mutation is False


def test_governance_is_read_only():
    report = build_decision_trace(
        [
            {
                "decision_id": "safe-1",
                "decision": "RECOVERY_REVIEW",
                "scenario": "MODERATE",
                "confidence": 0.90,
                "expected_value": 200000,
                "remaining_exposure": 10000,
                "evidence": ["validated-payment-data"],
            }
        ]
    )

    assert report.audit_complete is True
    assert report.read_only is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_multiple_decisions_are_auditable():
    report = build_decision_trace(
        [
            {
                "decision_id": "a",
                "decision": "REVIEW_A",
                "confidence": 0.90,
                "expected_value": 100000,
                "remaining_exposure": 10000,
                "evidence": ["source-a"],
            },
            {
                "decision_id": "b",
                "decision": "REVIEW_B",
                "confidence": 0.30,
                "expected_value": 200000,
                "remaining_exposure": 150000,
                "evidence": [],
            },
        ]
    )

    assert report.total_decisions == 2
    assert report.decisions_requiring_review == 2
    assert report.high_risk_decisions == 1
    assert report.audit_complete is True


def test_empty_input_is_safe():
    report = build_decision_trace([])

    assert report.total_decisions == 0
    assert report.decisions_requiring_review == 0
    assert report.high_risk_decisions == 0
    assert report.audit_complete is True
    assert report.read_only is True
    assert report.execution_allowed is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False
