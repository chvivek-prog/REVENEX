from revenex.phase14 import build_traceability_report


def test_traceability_is_verified():
    report = build_traceability_report()

    assert report.status == "TRACEABILITY_VERIFIED"
    assert report.traceability_score == 1.0
    assert report.chain_complete is True
    assert report.evidence_complete is True
    assert report.explanation_complete is True
    assert report.governance_complete is True


def test_evidence_is_complete():
    report = build_traceability_report()

    assert len(report.evidence) == 6

    ids = {
        item.evidence_id
        for item in report.evidence
    }

    assert ids == {
        "EV-001",
        "EV-002",
        "EV-003",
        "EV-004",
        "EV-005",
        "EV-006",
    }


def test_decision_is_traceable_to_evidence():
    report = build_traceability_report()

    decision_records = [
        record
        for record in report.records
        if record.stage == "DECIDE"
    ]

    assert len(decision_records) == 1

    decision = decision_records[0]

    assert "EV-002" in decision.input_refs
    assert "EV-003" in decision.input_refs
    assert "EV-004" in decision.input_refs
    assert "EV-005" in decision.input_refs
    assert "EV-006" in decision.input_refs

    assert decision.output == (
        "AGGRESSIVE_RECOVERY_REVIEW"
    )


def test_all_trace_records_are_explainable():
    report = build_traceability_report()

    assert len(report.records) == 6

    for record in report.records:
        assert record.trace_id == report.trace_id
        assert record.stage
        assert len(record.input_refs) > 0
        assert record.explanation
        assert record.human_review_required is True
        assert record.read_only is True


def test_governance_is_locked():
    report = build_traceability_report()

    assert report.human_review_required is True
    assert report.read_only is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.model_mutation is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_traceability_is_deterministic():
    first = build_traceability_report()
    second = build_traceability_report()

    assert first == second
