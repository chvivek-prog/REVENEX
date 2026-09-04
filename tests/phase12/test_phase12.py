from revenex.phase12 import build_system_proof


def test_system_proof_is_ready():
    proof = build_system_proof()

    assert proof.system_name == "REVENEX Intelligence Platform"
    assert proof.system_version == "PHASE_12"
    assert proof.status == "PROOF_READY"
    assert proof.proof_score == 1.0
    assert proof.phase_coverage == "PHASE_0_TO_11"


def test_complete_pipeline_is_present():
    proof = build_system_proof()

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


def test_capability_inventory_is_present():
    proof = build_system_proof()

    assert "Revenue Intelligence" in proof.capabilities
    assert "Customer 360" in proof.capabilities
    assert "Revenue Forecasting" in proof.capabilities
    assert "Scenario Simulation" in proof.capabilities
    assert "Decision Intelligence" in proof.capabilities
    assert "Outcome Evaluation" in proof.capabilities
    assert "Learning Intelligence" in proof.capabilities
    assert "Event Reliability" in proof.capabilities
    assert "Money Flow Intelligence" in proof.capabilities


def test_evidence_snapshot_is_present():
    proof = build_system_proof()

    metrics = {
        item["metric"]: item["value"]
        for item in proof.evidence
    }

    assert metrics["Outstanding Revenue"] == 550000
    assert metrics["Revenue At Risk"] == 428500
    assert metrics["Expected Collection"] == 483120
    assert metrics["Prediction Confidence"] == 0.62
    assert metrics["Selected Scenario"] == "AGGRESSIVE"
    assert (
        metrics["Recommended Decision"]
        == "AGGRESSIVE_RECOVERY_REVIEW"
    )


def test_safety_boundary_is_locked():
    proof = build_system_proof()

    assert proof.read_only is True
    assert proof.human_review_required is True
    assert proof.execution_allowed is False
    assert proof.automatic_action is False
    assert proof.model_mutation is False
    assert proof.financial_mutation is False
    assert proof.provider_mutation is False

    assert proof.safety_boundary["execution_allowed"] is False
    assert proof.safety_boundary["automatic_action"] is False
    assert proof.safety_boundary["model_mutation"] is False
    assert proof.safety_boundary["financial_mutation"] is False
    assert proof.safety_boundary["provider_mutation"] is False


def test_governance_is_advisory():
    proof = build_system_proof()

    assert proof.governance["mode"] == "ADVISORY"
    assert proof.governance["human_control"] == "REQUIRED"
    assert proof.governance["audit_mode"] == "READ_ONLY"
    assert proof.governance["automatic_execution"] is False
    assert proof.governance["automatic_learning"] is False


def test_proof_is_deterministic():
    first = build_system_proof()
    second = build_system_proof()

    assert first == second
