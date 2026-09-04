
"""
from revenex.api.webauthn_auth import (
    registration_options,
    registration_verify,
    authentication_options,
    authentication_verify,
    has_credentials,
)

REVENEX Stage 46 — Real HTTP Transport.

Dependency-free HTTP transport for the Revenue Intelligence API.

The transport layer:
    - validates request shape
    - rejects execution-related fields
    - delegates intelligence to the service layer
    - returns JSON
    - never executes financial/provider mutations
"""

from __future__ import annotations

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
from revenex.recoverai.http_integration import handle_recoverai_webhook
from revenex.recoverai.razorpay_client import create_payment_link

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from revenex.api.revenue_intelligence import (
    analyze_revenue,
    record_revenue_outcome,
    response_to_dict,
)


ALLOWED_FIELDS = {
    "invoices",
    "payments",
    "decision_id",
}


FORBIDDEN_FIELDS = {
    "execute",
    "execute_payment",
    "refund",
    "capture_payment",
    "create_payment",
    "approve",
    "approval_id",
    "authorised_by_approval_id",
    "execution_allowed",
    "automatic_action",
    "financial_mutation",
    "provider_mutation",
}


def validate_request(
    body: Any,
) -> tuple[bool, str]:
    if not isinstance(body, dict):
        return False, "Request body must be a JSON object."

    unknown = set(body) - ALLOWED_FIELDS

    if unknown:
        return (
            False,
            "Unsupported request field(s): "
            + ", ".join(sorted(unknown)),
        )

    forbidden = set(body) & FORBIDDEN_FIELDS

    if forbidden:
        return (
            False,
            "Execution-related fields are forbidden.",
        )

    invoices = body.get("invoices", [])
    payments = body.get("payments", [])

    if not isinstance(invoices, list):
        return False, "invoices must be a list."

    if not isinstance(payments, list):
        return False, "payments must be a list."

    decision_id = body.get(
        "decision_id",
        "http-decision",
    )

    if not isinstance(decision_id, str):
        return False, "decision_id must be a string."

    if not decision_id.strip():
        return False, "decision_id must not be empty."

    return True, ""



def _cors_origin(origin):
    allowed = {
        "http://127.0.0.1:8788",
        "http://localhost:8788",
    }
    return origin if origin in allowed else "null"

class RevenueHTTPRequestHandler(
    BaseHTTPRequestHandler
):
    server_version = "REVENEX/46"

    def _json_response(
        self,
        status: int,
        payload: dict[str, Any],
    ) -> None:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            default=str,
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(encoded)),
        )
        self.send_header(
            "Access-Control-Allow-Origin",
            "http://127.0.0.1:8788",
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS",
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )
        self.send_header(
            "X-REVENEX-Safety",
            "READ-ONLY",
        )
        self.send_header(
            "X-Content-Type-Options",
            "nosniff",
        )
        self.end_headers()

        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header(
            "Access-Control-Allow-Origin",
            "http://127.0.0.1:8788",
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS",
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type",
        )
        self.send_header(
            "Access-Control-Max-Age",
            "600",
        )
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            frontend = Path(__file__).resolve().parents[2] / "frontend" / "revenue_command_center.html"
            try:
                encoded = frontend.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(encoded)
            except OSError:
                self._json_response(500, {"error": "frontend_not_available"})
            return

        if self.path == "/health":
            self._json_response(
                200,
                {
                    "status": "ok",
                    "service": "revenex",
                    "stage": 46,
                    "execution_allowed": False,
                },
            )
            return

        self._json_response(
            404,
            {
                "error": "not_found",
            },
        )

    def do_POST(self) -> None:
        content_length = self.headers.get(
            "Content-Length"
        )

        if content_length is None:
            self._json_response(
                400,
                {
                    "error": "missing_content_length",
                },
            )
            return

        try:
            length = int(content_length)
        except ValueError:
            self._json_response(
                400,
                {
                    "error": "invalid_content_length",
                },
            )
            return

        if length <= 0:
            self._json_response(
                400,
                {
                    "error": "empty_request",
                },
            )
            return

        if length > 2_000_000:
            self._json_response(
                413,
                {
                    "error": "request_too_large",
                },
            )
            return

        raw = self.rfile.read(length)

        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json_response(
                400,
                {
                    "error": "invalid_json",
                },
            )
            return

        # ------------------------------------------------------------
        # RECOVERAI TEST PAYMENT LINK
        # ------------------------------------------------------------
        if self.path == "/api/v1/recoverai/test-payment-link":
            if not isinstance(body, dict):
                self._json_response(
                    400,
                    {
                        "error": "invalid_request",
                        "message": "Request body must be a JSON object.",
                    },
                )
                return

            amount = body.get("amount", 10000)
            reference_id = body.get(
                "reference_id",
                "recoverai-dashboard-demo",
            )
            description = body.get(
                "description",
                "REVENEX RecoverAI Test Recovery",
            )

            try:
                result = create_payment_link(
                    amount=int(amount),
                    currency="INR",
                    reference_id=str(reference_id),
                    description=str(description),
                )
            except PermissionError as exc:
                self._json_response(
                    403,
                    {
                        "error": "test_actions_disabled",
                        "message": str(exc),
                    },
                )
                return
            except Exception as exc:
                self._json_response(
                    502,
                    {
                        "error": "razorpay_error",
                        "message": str(exc),
                    },
                )
                return

            self._json_response(
                200,
                {
                    "success": True,
                    "mode": "test",
                    "payment_link_id": result.get("id"),
                    "status": result.get("status"),
                    "short_url": result.get("short_url"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency", "INR"),
                },
            )
            return

        # ------------------------------------------------------------
        # OUTCOME RECORDING
        # ------------------------------------------------------------
        if self.path == "/api/v1/recoverai/webhook":
            signature = self.headers.get("X-Razorpay-Signature")

            try:
                result = handle_recoverai_webhook(
                    raw_body,
                    signature,
                )
            except PermissionError as exc:
                self._json_response(
                    401,
                    {
                        "error": "invalid_webhook",
                        "message": str(exc),
                    },
                )
                return
            except Exception as exc:
                self._json_response(
                    400,
                    {
                        "error": "webhook_processing_failed",
                        "message": str(exc),
                    },
                )
                return

            self._json_response(
                200,
                result,
            )
            return

        if self.path == (
            "/api/v1/revenue-intelligence/outcome"
        ):
            if not isinstance(body, dict):
                self._json_response(
                    400,
                    {
                        "error": "invalid_request",
                        "message": "Request body must be a JSON object.",
                    },
                )
                return

            required = (
                "decision_id",
                "actual_collection",
                "actual_remaining_exposure",
            )

            missing = [
                field
                for field in required
                if field not in body
            ]

            if missing:
                self._json_response(
                    400,
                    {
                        "error": "invalid_request",
                        "message": (
                            "Missing required fields: "
                            + ", ".join(missing)
                        ),
                    },
                )
                return

            try:
                decision_id = str(body["decision_id"]).strip()

                if not decision_id:
                    raise ValueError(
                        "decision_id must not be empty."
                    )

                actual_collection = float(
                    body["actual_collection"]
                )

                actual_remaining_exposure = float(
                    body["actual_remaining_exposure"]
                )

                if actual_collection < 0:
                    raise ValueError(
                        "actual_collection must be non-negative."
                    )

                if actual_remaining_exposure < 0:
                    raise ValueError(
                        "actual_remaining_exposure must be non-negative."
                    )

                payload = record_revenue_outcome(
                    decision_id=decision_id,
                    actual_collection=actual_collection,
                    actual_remaining_exposure=(
                        actual_remaining_exposure
                    ),
                )

                self._json_response(
                    200,
                    payload,
                )

            except KeyError as exc:
                self._json_response(
                    404,
                    {
                        "error": "outcome_not_found",
                        "message": str(exc),
                    },
                )

            except ValueError as exc:
                self._json_response(
                    400,
                    {
                        "error": "invalid_outcome",
                        "message": str(exc),
                    },
                )

            except Exception:
                self._json_response(
                    500,
                    {
                        "error": "internal_error",
                    },
                )

            return

        # ------------------------------------------------------------
        # EXISTING REVENUE ANALYSIS
        # ------------------------------------------------------------

        # ------------------------------------------------------------
        # REVENEX REAL WEBAUTHN AUTHENTICATION
        # ------------------------------------------------------------
        if self.path == "/api/v1/auth/passkey/register/options":
            try:
                email = str(body.get("email", "")).strip().lower()
                result = registration_options(email)
                self._json_response(200, result)
            except Exception as exc:
                self._json_response(
                    400,
                    {"error": "webauthn_registration_options_failed",
                     "message": str(exc)},
                )
            return

        if self.path == "/api/v1/auth/passkey/register/verify":
            try:
                email = str(body.get("email", "")).strip().lower()
                challenge_id = str(body.get("challenge_id", ""))
                credential = body.get("credential")
                if not isinstance(credential, dict):
                    raise ValueError("credential must be an object")

                result = registration_verify(
                    email,
                    challenge_id,
                    credential,
                )
                self._json_response(200, result)
            except Exception as exc:
                self._json_response(
                    403,
                    {"error": "webauthn_registration_verification_failed",
                     "message": str(exc)},
                )
            return

        if self.path == "/api/v1/auth/passkey/login/options":
            try:
                email = str(body.get("email", "")).strip().lower()
                result = authentication_options(email)
                self._json_response(200, result)
            except Exception as exc:
                self._json_response(
                    400,
                    {"error": "webauthn_authentication_options_failed",
                     "message": str(exc)},
                )
            return

        if self.path == "/api/v1/auth/passkey/login/verify":
            try:
                email = str(body.get("email", "")).strip().lower()
                challenge_id = str(body.get("challenge_id", ""))
                credential = body.get("credential")
                if not isinstance(credential, dict):
                    raise ValueError("credential must be an object")

                result = authentication_verify(
                    email,
                    challenge_id,
                    credential,
                )

                self._json_response(
                    200,
                    result,
                    headers={
                        "Set-Cookie":
                            "revenex_authenticated=true; "
                            "HttpOnly; Path=/; SameSite=Strict"
                    },
                )
            except Exception as exc:
                self._json_response(
                    403,
                    {"error": "webauthn_authentication_verification_failed",
                     "message": str(exc)},
                )
            return

        if self.path == "/api/v1/auth/logout":
            self._json_response(
                200,
                {"authenticated": False},
                headers={
                    "Set-Cookie":
                        "revenex_authenticated=; "
                        "HttpOnly; Path=/; Max-Age=0; SameSite=Strict"
                },
            )
            return

        # REVENEX_WEBAUTHN_ROUTES_V1

        if self.path != (
            "/api/v1/revenue-intelligence/analyze"
        ):
            self._json_response(
                404,
                {
                    "error": "not_found",
                },
            )
            return

        valid, error = validate_request(body)

        if not valid:
            self._json_response(
                400,
                {
                    "error": "invalid_request",
                    "message": error,
                },
            )
            return

        try:
            response = analyze_revenue(
                invoices=body.get(
                    "invoices",
                    [],
                ),
                payments=body.get(
                    "payments",
                    [],
                ),
                decision_id=body.get(
                    "decision_id",
                    "http-decision",
                ),
            )

            payload = response_to_dict(
                response
            )

            self._json_response(
                200,
                payload,
            )

        except (ValueError, TypeError) as exc:
            self._json_response(
                400,
                {
                    "error": "invalid_revenue_state",
                    "message": str(exc),
                },
            )

        except Exception:
            self._json_response(
                500,
                {
                    "error": "internal_error",
                },
            )

    def log_message(
        self,
        format: str,
        *args: Any,
    ) -> None:
        # Keep HTTP logs deterministic and avoid dumping request bodies.
        return


def create_server(
    host: str = "127.0.0.1",
    port: int = 8787,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        RevenueHTTPRequestHandler,
    )


def serve(
    host: str | None = None,
    port: int | None = None,
) -> None:
    import os

    if host is None:
        host = os.getenv("HOST", "127.0.0.1")
    if port is None:
        port = int(os.getenv("PORT", "8787"))

    server = create_server(
        host,
        port,
    )
    print(
        f"REVENEX HTTP server listening on "
        f"http://{host}:{port}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
