from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay_seconds < 0:
            raise ValueError(
                "base_delay_seconds must be >= 0"
            )


@dataclass(frozen=True)
class TimeoutPolicy:
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive"
            )


class CircuitBreaker:
    """
    Deterministic in-memory circuit breaker.

    This does not execute provider operations.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 3,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError(
                "failure_threshold must be >= 1"
            )

        self.failure_threshold = failure_threshold
        self.failures = 0
        self.opened = False
        self._opened_at: float | None = None

    def allow_request(self) -> bool:
        return not self.opened

    def record_success(self) -> None:
        self.failures = 0
        self.opened = False
        self._opened_at = None

    def record_failure(self) -> None:
        self.failures += 1

        if self.failures >= self.failure_threshold:
            self.opened = True
            self._opened_at = monotonic()

    @property
    def is_open(self) -> bool:
        return self.opened


@dataclass(frozen=True)
class ProviderGatewayPolicy:
    retry: RetryPolicy = RetryPolicy()
    timeout: TimeoutPolicy = TimeoutPolicy()
    failure_threshold: int = 3
    financial_mutation_allowed: bool = False
    provider_mutation_allowed: bool = False
