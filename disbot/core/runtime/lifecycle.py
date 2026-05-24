"""Process lifecycle state machine for SuperBot — LP-2.

Owns the canonical state for "is this process accepting commands? draining?
restarting?" so callers do not pass around module-level booleans. Replaces
the legacy ``_shutting_down: bool`` in ``bot1.py``.

This module deliberately exposes a minimal API: callers ask for the
current phase, request a transition, or read recent events. The actual
exec / exit happens in ``bot1.py``; this module records intent and does
nothing else.

Phases
------
STARTING
    Initial state before ``on_ready`` fires. Commands admitted (no
    behaviour change versus the pre-LP-2 ``_shutting_down=False``).
RUNNING
    ``on_ready`` fired; commands accepted normally.
DRAINING
    Shutdown or restart requested; new commands rejected; in-flight
    commands still running.
SHUTTING_DOWN
    Cleanup in progress (``bot1.main`` finally block).
RESTARTING
    Cleanup complete, awaiting exec / respawn. Reserved for LP-3.
STOPPED
    Terminal: cleanup done, process about to exit.
FAILED_STARTUP
    Terminal: startup raised before ``RUNNING``. Reserved for LP-5 +.

Idempotency
-----------
``request_shutdown`` and ``request_restart`` coalesce: a second call
while a request is already pending is a no-op and returns ``False`` so
the caller can tell whether its request was the one that took effect.
A restart request while a plain shutdown is pending also coalesces and
does *not* upgrade the kind — the first intent wins.
"""

from __future__ import annotations

import enum
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


class Phase(enum.Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DRAINING = "DRAINING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    RESTARTING = "RESTARTING"
    STOPPED = "STOPPED"
    FAILED_STARTUP = "FAILED_STARTUP"


_DRAINING_PHASES: frozenset[Phase] = frozenset(
    {Phase.DRAINING, Phase.SHUTTING_DOWN, Phase.RESTARTING, Phase.STOPPED},
)
_ADMITTING_PHASES: frozenset[Phase] = frozenset(
    {Phase.STARTING, Phase.RUNNING},
)


@dataclass(frozen=True)
class LifecycleEvent:
    """One transition or request recorded in the ring buffer."""

    name: str
    phase: Phase
    at: float  # ``time.monotonic()`` seconds
    actor: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PendingShutdown:
    """The shutdown / restart request currently in flight, if any."""

    kind: str  # "shutdown" or "restart"
    reason: str
    actor: str | None
    requested_at: float
    grace_seconds: float | None


_EVENT_BUFFER_SIZE = 128

_phase: Phase = Phase.STARTING
_pending: PendingShutdown | None = None
_events: deque[LifecycleEvent] = deque(maxlen=_EVENT_BUFFER_SIZE)


def get_phase() -> Phase:
    """Return the current lifecycle phase."""
    return _phase


def _publish_phase_gauge(phase: Phase) -> None:
    """Update ``lifecycle_phase`` so exactly one ``phase`` label is 1.0.

    Wrapped in try/except so a missing or partially-initialized metrics
    module never blocks a phase transition — metrics are observability,
    not control plane.
    """
    try:
        from services import metrics as _metrics

        for p in Phase:
            _metrics.lifecycle_phase.labels(phase=p.value).set(
                1.0 if p is phase else 0.0,
            )
    except Exception:  # noqa: BLE001 — metrics are observability only
        pass


def set_phase(phase: Phase, *, reason: str | None = None) -> None:
    """Record a phase transition.

    Intended for the entry point (``bot1.py``) and the lifecycle module
    itself. Cogs should not call this directly — they use
    :func:`request_shutdown` / :func:`request_restart`.
    """
    global _phase
    if _phase == phase:
        return
    _phase = phase
    _record_event(f"phase:{phase.value}", reason=reason)
    _publish_phase_gauge(phase)


def is_shutting_down() -> bool:
    """True if the bot is draining, shutting down, restarting, or stopped.

    Mirrors the semantics of the legacy ``_shutting_down: bool`` in
    ``bot1.py``: any phase past ``RUNNING`` counts as "not accepting new
    work".
    """
    return _phase in _DRAINING_PHASES


def restart_requested() -> bool:
    """True if a restart (rather than a plain shutdown) is pending."""
    return _pending is not None and _pending.kind == "restart"


def can_accept_commands() -> bool:
    """True if new commands may be admitted.

    Returns True only in ``STARTING`` and ``RUNNING``. Every other phase
    — including the terminal ``FAILED_STARTUP`` — rejects new commands.
    """
    return _phase in _ADMITTING_PHASES


def request_shutdown(
    reason: str,
    *,
    actor: str | None = None,
    grace_seconds: float | None = None,
) -> bool:
    """Request a graceful shutdown.

    Returns ``True`` if this call established the pending request,
    ``False`` if a request was already in flight (coalesced).
    """
    global _pending
    if _pending is not None:
        _record_event(
            "shutdown_requested_coalesced",
            reason=reason,
            actor=actor,
        )
        return False
    _pending = PendingShutdown(
        kind="shutdown",
        reason=reason,
        actor=actor,
        requested_at=time.monotonic(),
        grace_seconds=grace_seconds,
    )
    _record_event("shutdown_requested", reason=reason, actor=actor)
    if _phase in (Phase.STARTING, Phase.RUNNING):
        set_phase(Phase.DRAINING, reason=reason)
    return True


def request_restart(
    reason: str,
    *,
    actor: str | None = None,
    grace_seconds: float | None = None,
) -> bool:
    """Request a graceful restart.

    Returns ``True`` if this call established the pending request,
    ``False`` if a request was already in flight (coalesced — even if
    the existing pending intent was a plain ``shutdown``; the first
    intent wins so callers do not race to upgrade the kind).
    """
    global _pending
    if _pending is not None:
        _record_event(
            "restart_requested_coalesced",
            reason=reason,
            actor=actor,
        )
        return False
    _pending = PendingShutdown(
        kind="restart",
        reason=reason,
        actor=actor,
        requested_at=time.monotonic(),
        grace_seconds=grace_seconds,
    )
    _record_event("restart_requested", reason=reason, actor=actor)
    if _phase in (Phase.STARTING, Phase.RUNNING):
        set_phase(Phase.DRAINING, reason=reason)
    return True


def record_close_executing(pending: PendingShutdown) -> None:
    """Record that the close-driver has reached ``bot.close()``.

    Surfaces in :func:`get_recent_events` / :func:`diagnostics_snapshot`
    so operators can distinguish "the lifecycle request was recorded but
    nothing executed it" from "the close-driver actually ran".  The
    pre-existing ``shutdown_requested`` / ``restart_requested`` events
    capture intent; this captures execution.

    ``pending.kind`` is stored under ``metadata`` because
    :class:`LifecycleEvent` does not expose a top-level ``kind`` field —
    metadata is the documented extension point for per-event payload.
    """
    _record_event(
        "close_executing",
        reason=pending.reason,
        actor=pending.actor,
        metadata={"kind": pending.kind},
    )


def get_pending() -> PendingShutdown | None:
    """Return the current pending request, or ``None`` if none."""
    return _pending


def remaining_shutdown_seconds() -> float | None:
    """Seconds left in the grace window.

    Returns ``None`` if no shutdown is pending, or if the pending
    request did not specify a grace window.
    """
    if _pending is None or _pending.grace_seconds is None:
        return None
    elapsed = time.monotonic() - _pending.requested_at
    return max(0.0, _pending.grace_seconds - elapsed)


def get_recent_events(limit: int = 20) -> list[LifecycleEvent]:
    """Return the most recent lifecycle events, newest last.

    ``limit <= 0`` returns an empty list.
    """
    if limit <= 0:
        return []
    return list(_events)[-limit:]


def _record_event(
    name: str,
    *,
    reason: str | None = None,
    actor: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    # Mirror the ring-buffer append into Prometheus so operators can
    # graph event rates by name.  Wrapped in try/except so a missing
    # or partially-initialized metrics module never blocks event
    # recording (observability, not control plane).
    try:
        from services import metrics as _metrics

        _metrics.lifecycle_event_total.labels(event=name).inc()
    except Exception:  # noqa: BLE001 — metrics are observability only
        pass
    _events.append(
        LifecycleEvent(
            name=name,
            phase=_phase,
            at=time.monotonic(),
            actor=actor,
            reason=reason,
            metadata=metadata or {},
        ),
    )


def reset_for_tests() -> None:
    """Reset module state back to ``STARTING`` with no pending request.

    Test-only entry point — production code must not call this.
    """
    global _phase, _pending
    _phase = Phase.STARTING
    _pending = None
    _events.clear()
    _publish_phase_gauge(_phase)


def diagnostics_snapshot() -> dict[str, Any]:
    """LP-6: sync snapshot of current lifecycle state for the
    :mod:`services.diagnostics_service` registry.

    Surfaced via ``!platform lifecycle`` and the
    :func:`services.platform_consistency.collect_report` ``Lifecycle``
    section. Sync by design — no DB or I/O.
    """
    pending = get_pending()
    events = get_recent_events(limit=20)
    return {
        "phase": _phase.value,
        "is_shutting_down": is_shutting_down(),
        "can_accept_commands": can_accept_commands(),
        "restart_requested": restart_requested(),
        "remaining_shutdown_seconds": remaining_shutdown_seconds(),
        "pending": (
            {
                "kind": pending.kind,
                "reason": pending.reason,
                "actor": pending.actor,
                "requested_at_monotonic": pending.requested_at,
                "grace_seconds": pending.grace_seconds,
            }
            if pending
            else None
        ),
        "recent_events": [
            {
                "name": event.name,
                "phase": event.phase.value,
                "at_monotonic": event.at,
                "actor": event.actor,
                "reason": event.reason,
            }
            for event in events
        ],
    }


# Self-register at import time, mirroring the persistent_views and
# core.runtime.tasks registration pattern. Wrapped in try/except so an
# unavailable diagnostics_service (e.g. import order during early test
# bootstrap) never blocks lifecycle import.
try:
    from services import diagnostics_service as _diagnostics_service

    _diagnostics_service.register("lifecycle", diagnostics_snapshot)
except Exception:  # noqa: BLE001 — diagnostics is observability only
    pass

# Initialise the lifecycle_phase gauge so STARTING reads as the current
# phase from process start, before any explicit set_phase() call.
# Without this, Grafana would show "no data" for the gauge until the
# first phase transition (typically the STARTING → RUNNING on_ready).
_publish_phase_gauge(_phase)


__all__ = [
    "LifecycleEvent",
    "PendingShutdown",
    "Phase",
    "can_accept_commands",
    "diagnostics_snapshot",
    "get_pending",
    "get_phase",
    "get_recent_events",
    "is_shutting_down",
    "record_close_executing",
    "remaining_shutdown_seconds",
    "request_restart",
    "request_shutdown",
    "reset_for_tests",
    "restart_requested",
    "set_phase",
]
