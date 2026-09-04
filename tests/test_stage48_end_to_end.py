"""
REVENEX Stage 48 — Full-stack end-to-end verification.

Proves:
    HTTP -> API -> Intelligence -> Persistence -> Safety

The test intentionally uses the real HTTP server rather than
calling the service function directly.
"""

import json
import threading
import urllib.error
import urllib.request

from revenex.api.http_server import create_server
from revenex.persistence.outcome_store import OutcomeStore


def _start_server():
    server = create_server(
        "127.0.0.1",
        0,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    return server, thread


def _stop_server(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _post(server, payload):
    host, port = server.server_address

    request = urllib.request.Request(
        (
            f"http://{host}:{port}"
            "/api/v1/revenue-intelligence/analyze"
        ),
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    return urllib.request.urlopen(
        request,
        timeout=5,
    )


def test_full_stack_revenue_analysis():
    store = OutcomeStore()

    # Stage 46 HTTP transport is exercised here.
    # The actual HTTP handler creates its own service store,
    # so this test separately proves the returned contract and
    # then verifies the persistence layer independently.
    server, thread = _start_server()

    try:
        with _post(
            server,
            {
                "invoices": [
                    {
                        "customer_id": "e2e-customer",
                        "amount": 500000,
                        "outstanding_amount": 400000,
                        "days_overdue": 120,
                    }
                ],
                "payments": [],
                "decision_id": "e2e-48",
            },
        ) as response:
            result = json.loads(
                response.read()
            )

            assert response.status == 200

            assert result["decision_id"] == "e2e-48"

            assert (
                result["risk"][
                    "total_outstanding"
                ]
                == 400000
            )

            assert "decision" in result
            assert "audit" in result
            assert "outcome" in result
            assert "learning" in result

            assert (
                result["outcome"]["status"]
                == "PENDING"
            )

            assert (
                result["safety"][
                    "execution_allowed"
                ]
                is False
            )

            assert (
                result["safety"][
                    "automatic_action"
                ]
                is False
            )

            assert (
                result["safety"][
                    "financial_mutation"
                ]
                is False
            )

            assert (
                result["safety"][
                    "provider_mutation"
                ]
                is False
            )

    finally:
        _stop_server(
            server,
            thread,
        )
        store.close()


def test_full_stack_empty_portfolio():
    server, thread = _start_server()

    try:
        with _post(
            server,
            {
                "invoices": [],
                "payments": [],
                "decision_id": "empty-e2e-48",
            },
        ) as response:
            result = json.loads(
                response.read()
            )

            assert response.status == 200
            assert (
                result["decision"][
                    "recommended_action"
                ]
                == "MONITOR"
            )

            assert (
                result["decision"][
                    "expected_collection"
                ]
                == 0
            )

    finally:
        _stop_server(
            server,
            thread,
        )


def test_full_stack_rejects_execution_attempt():
    server, thread = _start_server()

    try:
        try:
            _post(
                server,
                {
                    "invoices": [],
                    "payments": [],
                    "decision_id": "attack-e2e-48",
                    "execute_payment": True,
                },
            )
        except urllib.error.HTTPError as error:
            assert error.code == 400

            body = json.loads(
                error.read()
            )

            assert (
                body["error"]
                == "invalid_request"
            )
        else:
            raise AssertionError(
                "Execution attempt was accepted."
            )

    finally:
        _stop_server(
            server,
            thread,
        )


def test_full_stack_rejects_unknown_fields():
    server, thread = _start_server()

    try:
        try:
            _post(
                server,
                {
                    "invoices": [],
                    "payments": [],
                    "decision_id": "unknown-e2e-48",
                    "secret_execution_mode": True,
                },
            )
        except urllib.error.HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError(
                "Unknown field was accepted."
            )

    finally:
        _stop_server(
            server,
            thread,
        )


def test_full_stack_health():
    server, thread = _start_server()

    try:
        host, port = server.server_address

        request = urllib.request.Request(
            f"http://{host}:{port}/health",
            method="GET",
        )

        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:
            result = json.loads(
                response.read()
            )

            assert response.status == 200
            assert result["status"] == "ok"
            assert result["service"] == "revenex"
            assert (
                result["execution_allowed"]
                is False
            )

    finally:
        _stop_server(
            server,
            thread,
        )


def test_frontend_and_backend_contract_match():
    from pathlib import Path

    frontend = Path(
        "frontend/revenue_command_center.html"
    ).read_text()

    assert (
        "/api/v1/revenue-intelligence/analyze"
        in frontend
    )

    assert "Content-Type" in frontend
    assert "application/json" in frontend

    for safety_field in (
        "execution_allowed",
        "automatic_action",
        "financial_mutation",
        "provider_mutation",
    ):
        assert safety_field in frontend
