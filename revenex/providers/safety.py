
from __future__ import annotations


PROVIDER_SAFETY_BOUNDARY = {
    "provider_mutation": False,
    "financial_mutation": False,
    "automatic_action": False,
    "execution_allowed": False,
    "human_approval_required": True,
    "sandbox_preferred": True,
}


def assert_provider_read_only() -> None:
    if any(
        PROVIDER_SAFETY_BOUNDARY[key]
        for key in (
            "provider_mutation",
            "financial_mutation",
            "automatic_action",
            "execution_allowed",
        )
    ):
        raise RuntimeError(
            "REVENEX provider safety boundary violated."
        )
