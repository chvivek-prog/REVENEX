
from __future__ import annotations

RAZORPAY_COVERAGE = {
    "customers": True,
    "orders": True,
    "payments": True,
    "payment_links": True,
    "invoices": True,
    "subscriptions": True,
    "refunds": True,
    "settlements": True,
    "disputes": True,
    "payouts": True,
    "webhooks": True,
    "reconciliation": True,
    "read_only": True,
    "financial_mutation": False,
    "provider_mutation": False,
}


def coverage_summary() -> dict:
    total = 0
    covered = 0

    for key, value in RAZORPAY_COVERAGE.items():
        if key in {
            "read_only",
            "financial_mutation",
            "provider_mutation",
        }:
            continue

        total += 1
        covered += int(bool(value))

    return {
        "provider": "razorpay",
        "covered_capabilities": covered,
        "total_capabilities": total,
        "coverage_percent": (
            round((covered / total) * 100, 2)
            if total
            else 0.0
        ),
        "read_only": True,
        "financial_mutation": False,
        "provider_mutation": False,
    }
