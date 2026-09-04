from __future__ import annotations

import hashlib
import hmac


class WebhookVerifier:
    """
    Deterministic webhook signature verifier.

    The verifier only authenticates an event.
    It never performs a financial or provider mutation.
    """

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("Webhook secret is required")
        self._secret = secret.encode("utf-8")

    def sign(self, payload: bytes) -> str:
        return hmac.new(
            self._secret,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        expected = self.sign(payload)

        return hmac.compare_digest(
            expected,
            str(signature),
        )
