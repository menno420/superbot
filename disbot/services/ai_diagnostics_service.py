"""Read-only AI diagnostics surface.

Module 2 (AI Cog) reads from here to render ``/ai status``,
``/ai diagnostics``, and ``/ai providers``. The cog never touches
:mod:`core.runtime.ai.diagnostics` directly — that boundary keeps
the dependency direction clean.
"""

from __future__ import annotations

from core.runtime.ai.contracts import AIDiagnosticsSnapshot, AITask
from core.runtime.ai.diagnostics import get_default_collector
from core.runtime.ai.feature_flags import (
    ai_default_provider,
    ai_enabled,
    setup_advisor_provider,
    task_enabled,
)
from core.runtime.ai.routing import resolve

__all__ = [
    "list_task_routing",
    "snapshot",
    "snapshot_for_cog",
]


def snapshot() -> AIDiagnosticsSnapshot:
    """Return the latest read-only diagnostics snapshot."""
    return get_default_collector().snapshot()


def snapshot_for_cog() -> dict[str, object]:
    """Snapshot in a shape convenient for the AI Cog's embed builder."""
    snap = snapshot()
    return {
        "enabled": snap.enabled,
        "default_provider": ai_default_provider(),
        "setup_advisor_provider": setup_advisor_provider(),
        "provider_active": snap.provider_active,
        "degraded": snap.degraded,
        "last_error_type": snap.last_error_type,
        "last_fallback_reason": snap.last_fallback_reason,
        "requests_observed": snap.requests_observed,
        "failures_observed": snap.failures_observed,
        "redaction_enabled": snap.redaction_enabled,
    }


def list_task_routing() -> list[dict[str, object]]:
    """List how each :class:`AITask` is currently routed.

    Cogs use this to render ``/ai routing`` without invoking any
    provider. Each entry is ``{task, provider, model, timeout,
    enabled}``.
    """
    rows: list[dict[str, object]] = []
    for task in AITask:
        target = resolve(task)
        rows.append(
            {
                "task": task.value,
                "provider": target.provider,
                "model": target.model,
                "timeout_seconds": target.timeout_seconds,
                "enabled": task_enabled(task) and ai_enabled(),
            },
        )
    return rows
