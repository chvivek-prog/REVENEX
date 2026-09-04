from revenex.phase11 import generate_demo_report


def test_demo_report_is_ready():
    report = generate_demo_report()

    assert report.demo_ready is True
    assert report.read_only is True
    assert report.human_review_required is True
    assert report.title == "REVENEX Intelligence Platform"


def test_demo_contains_complete_pipeline():
    report = generate_demo_report()

    assert report.pipeline == (
        "OBSERVE",
        "UNDERSTAND",
        "INVESTIGATE",
        "PREDICT",
        "SIMULATE",
        "DECIDE",
        "EXPLAIN",
        "AUDIT",
        "MONITOR",
        "LEARN",
    )


def test_demo_contains_required_evidence():
    report = generate_demo_report()

    names = {item.name for item in report.evidence}

    assert "Outstanding Revenue" in names
    assert "Revenue At Risk" in names
    assert "Expected Collection" in names
    assert "Confidence" in names
    assert "Scenario" in names
    assert "Decision" in names


def test_demo_safety_is_locked():
    report = generate_demo_report()

    assert report.safety["execution_allowed"] is False
    assert report.safety["automatic_action"] is False
    assert report.safety["financial_mutation"] is False
    assert report.safety["provider_mutation"] is False
    assert report.safety["model_mutation"] is False
    assert report.safety["human_review_required"] is True
    assert report.safety["read_only"] is True


def test_demo_values_are_deterministic():
    first = generate_demo_report()
    second = generate_demo_report()

    assert first == second
