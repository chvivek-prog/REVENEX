"""
REVENEX Stage 49 — Production Security Controls.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityPolicy:
    max_request_bytes: int = 2_000_000
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


DEFAULT_SECURITY_POLICY = SecurityPolicy()


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self' http://127.0.0.1:*"
    ),
}


FORBIDDEN_MUTATION_FIELDS = frozenset({
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
})


def security_headers() -> dict[str, str]:
    return dict(SECURITY_HEADERS)


def validate_request_size(
    content_length: int,
    policy: SecurityPolicy = DEFAULT_SECURITY_POLICY,
) -> tuple[bool, str]:
    if content_length < 0:
        return False, "Invalid content length."

    if content_length > policy.max_request_bytes:
        return False, "Request body exceeds configured limit."

    return True, ""


def contains_forbidden_mutation_fields(
    body: object,
) -> bool:
    if not isinstance(body, dict):
        return False

    return bool(
        FORBIDDEN_MUTATION_FIELDS.intersection(
            body.keys()
        )
    )


def validate_safety_policy(
    policy: SecurityPolicy = DEFAULT_SECURITY_POLICY,
) -> tuple[bool, str]:
    if not policy.read_only:
        return (
            False,
            "Production intelligence API must remain read-only.",
        )

    if policy.execution_allowed:
        return False, "Execution must remain disabled."

    if policy.automatic_action:
        return False, "Automatic action must remain disabled."

    if policy.financial_mutation:
        return False, "Financial mutation must remain disabled."

    if policy.provider_mutation:
        return False, "Provider mutation must remain disabled."

    return True, ""
