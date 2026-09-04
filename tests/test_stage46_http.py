import json
import threading
import urllib.error
import urllib.request

from revenex.api.http_server import (
    create_server,
    validate_request,
)


def test_valid_request_shape():
    valid, error = validate_request(
        {
            "invoices": [],
            "payments": [],
            "decision_id": "http-46",
        }
    )

    assert valid is True
    assert error == ""


def test_unknown_request_fields_are_rejected():
    valid, error = validate_request(
        {
            "invoices": [],
            "payments": [],
            "execute": True,
        }
    )

    assert valid is False
    assert "Unsupported" in error


def test_execution_fields_are_rejected():
    for field in (
        "execute_payment",
        "refund",
        "capture_payment",
        "approve",
        "approval_id",
        "execution_allowed",
        "automatic_action",
        "financial_mutation",
        "provider_mutation",
    ):
        valid, error = validate_request(
            {
                "invoices": [],
                "payments": [],
                field: True,
            }
        )

        assert valid is False
        assert error


def test_invoices_must_be_list():
    valid, error = validate_request(
        {
            "invoices": {},
            "payments": [],
        }
    )

    assert valid is False
    assert "invoices" in error


def test_payments_must_be_list():
    valid, error = validate_request(
        {
            "invoices": [],
            "payments": {},
        }
    )

    assert valid is False
    assert "payments" in error


def test_decision_id_must_be_string():
    valid, error = validate_request(
        {
            "invoices": [],
            "payments": [],
            "decision_id": 123,
        }
    )

    assert valid is False


def test_real_http_health_and_analysis():
    server = create_server(
        "127.0.0.1",
        0,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    host, port = server.server_address

    try:
        health_request = urllib.request.Request(
            f"http://{host}:{port}/health",
            method="GET",
        )

        with urllib.request.urlopen(
            health_request,
            timeout=5,
        ) as response:
            health = json.loads(
                response.read()
            )

            assert response.status == 200
            assert health["status"] == "ok"
            assert (
                health["execution_allowed"]
                is False
            )
            assert (
                response.headers[
                    "X-REVENEX-Safety"
                ]
                == "READ-ONLY"
            )

        payload = json.dumps(
            {
                "invoices": [
                    {
                        "customer_id": "http-customer",
                        "amount": 100000,
                        "outstanding_amount": 80000,
                        "days_overdue": 90,
                    }
                ],
                "payments": [],
                "decision_id": "http-real-46",
            }
        ).encode()

        request = urllib.request.Request(
            (
                f"http://{host}:{port}"
                "/api/v1/revenue-intelligence/analyze"
            ),
            data=payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:
            result = json.loads(
                response.read()
            )

            assert response.status == 200
            assert (
                result["decision_id"]
                == "http-real-46"
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

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_http_rejects_execution_payload():
    server = create_server(
        "127.0.0.1",
        0,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    host, port = server.server_address

    try:
        payload = json.dumps(
            {
                "invoices": [],
                "payments": [],
                "decision_id": "attack-46",
                "execute_payment": True,
            }
        ).encode()

        request = urllib.request.Request(
            (
                f"http://{host}:{port}"
                "/api/v1/revenue-intelligence/analyze"
            ),
            data=payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            urllib.request.urlopen(
                request,
                timeout=5,
            )
        except urllib.error.HTTPError as error:
            assert error.code == 400

            result = json.loads(
                error.read()
            )

            assert (
                result["error"]
                == "invalid_request"
            )
        else:
            raise AssertionError(
                "Execution payload was accepted."
            )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_invalid_json_returns_400():
    server = create_server(
        "127.0.0.1",
        0,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    host, port = server.server_address

    try:
        request = urllib.request.Request(
            (
                f"http://{host}:{port}"
                "/api/v1/revenue-intelligence/analyze"
            ),
            data=b"{not-json",
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            urllib.request.urlopen(
                request,
                timeout=5,
            )
        except urllib.error.HTTPError as error:
            assert error.code == 400
        else:
            raise AssertionError(
                "Invalid JSON was accepted."
            )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
