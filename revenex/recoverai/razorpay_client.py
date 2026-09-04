from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.razorpay.com/v1"


def _authorization() -> str:
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are required."
        )

    token = base64.b64encode(
        f"{key_id}:{key_secret}".encode()
    ).decode()

    return f"Basic {token}"


def _request(
    method: str,
    path: str,
    payload: dict | None = None,
):
    request = Request(
        BASE_URL + path,
        data=(
            None
            if payload is None
            else json.dumps(payload).encode()
        ),
        method=method,
        headers={
            "Authorization": _authorization(),
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(
                response.read().decode()
            )
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"Razorpay API {exc.code}: {body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Razorpay network error: {exc}"
        ) from exc


def fetch_payment(payment_id: str):
    return _request(
        "GET",
        f"/payments/{payment_id}",
    )


def create_payment_link(
    *,
    amount: int,
    currency: str,
    reference_id: str,
    description: str,
):
    if os.getenv(
        "RECOVERAI_ALLOW_RAZORPAY_TEST_ACTIONS",
        "0",
    ) != "1":
        raise PermissionError(
            "Recovery actions are disabled. "
            "Explicitly enable "
            "RECOVERAI_ALLOW_RAZORPAY_TEST_ACTIONS=1 "
            "for Razorpay Test Mode."
        )

    return _request(
        "POST",
        "/payment_links",
        {
            "amount": int(amount),
            "currency": currency,
            "reference_id": reference_id,
            "description": description,
            "accept_partial": False,
        },
    )
