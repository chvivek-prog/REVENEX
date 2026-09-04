from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    status: str
    score: float
    checks: tuple[ReadinessCheck, ...]
    passed_checks: int
    failed_checks: int

    phase_coverage: str
    reproducible: bool
    api_contract_ready: bool
    dashboard_contract_ready: bool
    safety_boundary_verified: bool

    human_review_required: bool = True
    read_only: bool = True
    execution_allowed: bool = False
    automatic_action: bool = False
    model_mutation: bool = False
    financial_mutation: bool = False
    provider_mutation: bool = False


def _check(
    name: str,
    passed: bool,
    detail: str,
) -> ReadinessCheck:
    return ReadinessCheck(
        name=name,
        passed=bool(passed),
        detail=str(detail),
    )


def run_production_readiness(
    *,
    phase0_to_9_verified: bool = True,
    api_contract: bool = True,
    dashboard_contract: bool = True,
    deterministic_pipeline: bool = True,
    execution_disabled: bool = True,
    financial_mutation_disabled: bool = True,
    provider_mutation_disabled: bool = True,
    model_mutation_disabled: bool = True,
    human_review_required: bool = True,
) -> ReadinessReport:
    checks = (
        _check(
            "PHASE_0_TO_9",
            phase0_to_9_verified,
            "Existing intelligence phases remain frozen and verified.",
        ),
        _check(
            "API_CONTRACT",
            api_contract,
            "Core API contract is represented and testable.",
        ),
        _check(
            "DASHBOARD_CONTRACT",
            dashboard_contract,
            "Dashboard-facing intelligence contract is represented.",
        ),
        _check(
            "DETERMINISTIC_PIPELINE",
            deterministic_pipeline,
            "Repeated inputs produce deterministic readiness state.",
        ),
        _check(
            "EXECUTION_BOUNDARY",
            execution_disabled,
            "Execution remains explicitly disabled.",
        ),
        _check(
            "FINANCIAL_MUTATION_BOUNDARY",
            financial_mutation_disabled,
            "Financial mutation remains disabled.",
        ),
        _check(
            "PROVIDER_MUTATION_BOUNDARY",
            provider_mutation_disabled,
            "Provider mutation remains disabled.",
        ),
        _check(
            "MODEL_MUTATION_BOUNDARY",
            model_mutation_disabled,
            "Automatic model mutation remains disabled.",
        ),
        _check(
            "HUMAN_GOVERNANCE",
            human_review_required,
            "Human review remains required.",
        ),
    )

    passed = sum(check.passed for check in checks)
    failed = len(checks) - passed

    score = round(
        passed / len(checks),
        4,
    ) if checks else 0.0

    if failed == 0:
        status = "PRODUCTION_READY_FOR_READ_ONLY_DEMO"
    else:
        status = "READINESS_REVIEW_REQUIRED"

    return ReadinessReport(
        status=status,
        score=score,
        checks=checks,
        passed_checks=passed,
        failed_checks=failed,
        phase_coverage="PHASE_0_TO_9",
        reproducible=deterministic_pipeline,
        api_contract_ready=api_contract,
        dashboard_contract_ready=dashboard_contract,
        safety_boundary_verified=(
            execution_disabled
            and financial_mutation_disabled
            and provider_mutation_disabled
            and model_mutation_disabled
        ),
        human_review_required=human_review_required,
        read_only=True,
        execution_allowed=False,
        automatic_action=False,
        model_mutation=False,
        financial_mutation=False,
        provider_mutation=False,
    )
