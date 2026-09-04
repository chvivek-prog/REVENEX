from pathlib import Path


def test_command_center_exists():
    path = Path(
        "frontend/revenue_command_center.html"
    )

    assert path.exists()


def test_command_center_contains_api_endpoint():
    text = Path(
        "frontend/revenue_command_center.html"
    ).read_text()

    assert (
        "/api/v1/revenue-intelligence/analyze"
        in text
    )


def test_command_center_contains_safety_boundary():
    text = Path(
        "frontend/revenue_command_center.html"
    ).read_text()

    assert "DISABLED" in text
    assert "Financial Mutation" in text
    assert "Provider Mutation" in text


def test_command_center_contains_intelligence_pipeline():
    text = Path(
        "frontend/revenue_command_center.html"
    ).read_text()

    for stage in (
        "Observe",
        "Investigate",
        "Predict",
        "Simulate",
        "Decide",
        "Explain",
        "Audit",
        "Outcome",
        "Learn",
    ):
        assert stage in text


def test_frontend_server_exists():
    assert Path(
        "revenex/api/frontend_server.py"
    ).exists()
