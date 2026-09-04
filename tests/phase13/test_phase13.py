from revenex.phase13 import build_dashboard_proof


def test_dashboard_proof_is_demo_ready():
    proof = build_dashboard_proof()

    assert proof.state == "DEMO_READY"
    assert proof.title == "REVENEX Revenue Command Center"
    assert proof.read_only is True
    assert proof.human_review_required is True


def test_dashboard_has_complete_pipeline():
    proof = build_dashboard_proof()

    assert proof.pipeline == (
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


def test_dashboard_has_core_sections():
    proof = build_dashboard_proof()

    assert "Revenue Intelligence" in proof.intelligence_sections
    assert "Customer 360" in proof.intelligence_sections
    assert "Revenue Forecast" in proof.intelligence_sections
    assert "Scenario Simulation" in proof.intelligence_sections
    assert "Decision Center" in proof.intelligence_sections
    assert "Audit & Explainability" in proof.intelligence_sections
    assert "Outcome Monitoring" in proof.intelligence_sections
    assert "Learning Engine" in proof.intelligence_sections


def test_dashboard_metrics_are_deterministic():
    proof = build_dashboard_proof()

    metrics = {
        item["label"]: item["value"]
        for item in proof.metrics
    }

    assert metrics["OUTSTANDING REVENUE"] == 550000
    assert metrics["REVENUE AT RISK"] == 428500
    assert metrics["EXPECTED COLLECTION"] == 483120
    assert metrics["AI CONFIDENCE"] == 0.62
    assert metrics["SCENARIO"] == "AGGRESSIVE"
    assert metrics["RECOMMENDED ACTION"] == (
        "AGGRESSIVE_RECOVERY_REVIEW"
    )


def test_dashboard_safety_is_locked():
    proof = build_dashboard_proof()

    assert proof.execution_allowed is False
    assert proof.automatic_action is False
    assert proof.model_mutation is False
    assert proof.financial_mutation is False
    assert proof.provider_mutation is False

    assert proof.safety["execution_allowed"] is False
    assert proof.safety["automatic_action"] is False
    assert proof.safety["model_mutation"] is False
    assert proof.safety["financial_mutation"] is False
    assert proof.safety["provider_mutation"] is False


def test_dashboard_governance_is_advisory():
    proof = build_dashboard_proof()

    assert proof.governance["mode"] == "ADVISORY"
    assert proof.governance["human_control"] == "REQUIRED"
    assert proof.governance["audit_mode"] == "READ_ONLY"
    assert proof.governance["execution"] == "DISABLED"
    assert proof.governance["automatic_learning"] == "DISABLED"


def test_demo_sequence_is_complete():
    proof = build_dashboard_proof()

    assert len(proof.demo_sequence) == 10
    assert proof.demo_sequence[0] == "1. Command Center"
    assert proof.demo_sequence[-1] == "10. Safety Boundary"


def test_dashboard_proof_is_reproducible():
    first = build_dashboard_proof()
    second = build_dashboard_proof()

    assert first == second
