"""Read-only diagnostics surface for the AI gateway.

The gateway updates an in-process :class:`DiagnosticsCollector` on
every call. The AI Cog (Module 2) and ``services.ai_diagnostics_service``
read snapshots to render ``/ai status`` and ``/ai diagnostics``.

A snapshot is a :class:`AIDiagnosticsSnapshot` (defined in
:mod:`core.runtime.ai.contracts`). The collector lives here so the
gateway's update path and the cog's read path agree on the same
in-memory representation.
"""

from __future__ import annotations

import threading

from core.runtime.ai.contracts import AIDiagnosticsSnapshot
from core.runtime.ai.feature_flags import ai_default_provider, ai_enabled


class DiagnosticsCollector:
    """Counts requests and failures observed by the gateway.

    Thread-safe via a coarse lock — call counts are negligible
    compared to the cost of an LLM round-trip.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests = 0
        self._failures = 0
        self._last_provider_active = ai_default_provider()
        self._last_error_type: str | None = None
        self._last_fallback_reason: str | None = None
        self._degraded = False

    def record_request(self, *, provider_active: str) -> None:
        with self._lock:
            self._requests += 1
            self._last_provider_active = provider_active

    def record_failure(
        self,
        *,
        provider_active: str,
        error_type: str,
        fallback_reason: str,
    ) -> None:
        with self._lock:
            self._failures += 1
            self._last_provider_active = provider_active
            self._last_error_type = error_type
            self._last_fallback_reason = fallback_reason
            self._degraded = True

    def record_success(self, *, provider_active: str) -> None:
        with self._lock:
            self._last_provider_active = provider_active
            self._degraded = False

    def snapshot(self) -> AIDiagnosticsSnapshot:
        with self._lock:
            return AIDiagnosticsSnapshot(
                provider_requested=ai_default_provider(),
                provider_active=self._last_provider_active,
                model="",  # populated by the cog from routing on demand
                enabled=ai_enabled(),
                redaction_enabled=True,
                degraded=self._degraded,
                last_error_type=self._last_error_type,
                last_fallback_reason=self._last_fallback_reason,
                requests_observed=self._requests,
                failures_observed=self._failures,
            )


_DEFAULT_COLLECTOR: DiagnosticsCollector | None = None


def get_default_collector() -> DiagnosticsCollector:
    """Process-wide singleton collector. Lazy-initialised."""
    global _DEFAULT_COLLECTOR
    if _DEFAULT_COLLECTOR is None:
        _DEFAULT_COLLECTOR = DiagnosticsCollector()
    return _DEFAULT_COLLECTOR


def reset_default_collector() -> None:
    """Test seam — drop the process-wide collector so tests start fresh."""
    global _DEFAULT_COLLECTOR
    _DEFAULT_COLLECTOR = None
