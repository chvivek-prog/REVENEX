from revenex.phase10 import run_production_readiness


def test_production_readiness_passes():
    report = run_production_readiness()

    assert report.status == (
        "PRODUCTION_READY_FOR_READ_ONLY_DEMO"
    )
    assert report.score == 1.0
    assert report.passed_checks == 9
    assert report.failed_checks == 0

    assert report.phase_coverage == "PHASE_0_TO_9"
    assert report.reproducible is True
    assert report.api_contract_ready is True
    assert report.dashboard_contract_ready is True
    assert report.safety_boundary_verified is True


def test_safety_boundary_is_locked():
    report = run_production_readiness()

    assert report.human_review_required is True
    assert report.read_only is True
    assert report.execution_allowed is False
    assert report.automatic_action is False
    assert report.model_mutation is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False


def test_failed_contract_is_detected():
    report = run_production_readiness(
        dashboard_contract=False,
    )

    assert report.status == "READINESS_REVIEW_REQUIRED"
    assert report.score < 1.0
    assert report.failed_checks == 1
    assert report.dashboard_contract_ready is False


def test_execution_cannot_be_marked_ready():
    report = run_production_readiness(
        execution_disabled=False,
    )

    assert report.status == "READINESS_REVIEW_REQUIRED"
    assert report.safety_boundary_verified is False
    assert report.execution_allowed is False
    assert report.financial_mutation is False
    assert report.provider_mutation is False
    assert report.model_mutation is False


def test_all_checks_have_audit_details():
    report = run_production_readiness()

    assert len(report.checks) == 9

    for check in report.checks:
        assert check.name
        assert isinstance(check.passed, bool)
        assert check.detail
