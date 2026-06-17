"""Startup outcome recorder — PR-01b + LP-7.

A tiny sync module that records whether each phase of startup
(``command_surface_ledger`` / ``settings_registry`` / ``customization_catalogue``
/ ``resource_provisioning_catalogue``) built successfully.  Each phase
in ``bot1.py`` already runs under its own ``try/except`` and continues
on failure; the recorder turns that previously-invisible state into an
observable record that the readiness snapshot can read sync.

LP-7 extends the recorder with per-phase timing
(``started_at`` / ``duration_ms``), free-form ``metadata``, a
``record_phase`` context manager, and ``summary_status`` so the
:mod:`services.webhook_reporter` can post a deterministic
startup-summary embed (green / yellow / red) before the bot connects
to Discord — operators see the boot outcome immediately rather than
waiting for ``on_ready``.

Public surface:

    StartupOutcome           — frozen dataclass per recorded phase
    SummaryStatus            — enum: OK / DEGRADED / FAILED / EMPTY
    record_success(name)     — called inside a try block
    record_failure(name, exc) — called inside an except clause
    record_phase(name)       — context manager that times the phase
                                and records success/failure
    all_outcomes()           — sorted tuple of every recorded outcome
    summary_status(outcomes) — derive overall status from outcomes
    reset_for_tests()        — clears the recorder state (pytest fixture)

The recorder is process-local, sync-only, and never raises.  It does
not register a diagnostics provider on its own — ``platform_consistency``
composes the outcomes into the readiness snapshot whose provider name
is ``"platform_readiness"``.
"""

from __future__ import annotations

import contextlib
import datetime
import enum
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

# Canonical phase names recorded by bot1.py at startup.  Code that
# adds a new phase must add its name here so the readiness snapshot
# can distinguish "phase ran and succeeded" from "phase did not run
# (unknown)" — the latter would be a regression that the
# orchestrator never reached the recorder.
KNOWN_PHASES: tuple[str, ...] = (
    "command_surface_ledger",
    "command_manifest",
    "settings_registry",
    "customization_catalogue",
    "resource_provisioning_catalogue",
)


class SummaryStatus(str, enum.Enum):
    """Derived overall status of a collection of startup outcomes."""

    OK = "ok"  # every recorded phase succeeded
    DEGRADED = "degraded"  # at least one failure, at least one success
    FAILED = "failed"  # every recorded phase failed
    EMPTY = "empty"  # no outcomes recorded


@dataclass(frozen=True)
class StartupOutcome:
    """One recorded phase outcome.

    ``error`` is ``None`` on success and a short ``type:message``
    string on failure (so the snapshot dict view is safe to serialise
    without leaking long stack traces).

    LP-7 fields (all optional for backwards compatibility):

    * ``started_at`` — UTC timestamp captured by the caller when the
      phase began. ``None`` for outcomes recorded without timing
      (legacy callers, hot reloads).
    * ``duration_ms`` — derived from ``started_at`` and ``recorded_at``
      when both are present; ``None`` otherwise.
    * ``metadata`` — caller-supplied free-form payload (e.g. cog count,
      table counts). Always present as a dict; defaults to empty so
      consumers don't need ``or {}`` guards.
    """

    name: str
    success: bool
    error: str | None
    recorded_at: datetime.datetime
    started_at: datetime.datetime | None = None
    duration_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


_RECORDED: dict[str, StartupOutcome] = {}


def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _duration_ms(
    started_at: datetime.datetime | None,
    recorded_at: datetime.datetime,
) -> float | None:
    if started_at is None:
        return None
    delta = recorded_at - started_at
    return max(0.0, delta.total_seconds() * 1000.0)


def record_success(
    name: str,
    *,
    started_at: datetime.datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record a successful phase run.

    Overwrites any prior record for the same name so a hot-reload
    rebuild flips the state back to success. Never raises.

    LP-7: ``started_at`` enables duration measurement; ``metadata``
    accepts free-form caller context. Both default to backwards-
    compatible no-ops.
    """
    recorded_at = _now()
    _RECORDED[name] = StartupOutcome(
        name=name,
        success=True,
        error=None,
        recorded_at=recorded_at,
        started_at=started_at,
        duration_ms=_duration_ms(started_at, recorded_at),
        metadata=dict(metadata) if metadata else {},
    )


def record_failure(
    name: str,
    exc: BaseException,
    *,
    started_at: datetime.datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record a failed phase run.

    Stores a short ``type:message`` summary; never holds the
    exception traceback. Never raises. LP-7 timing + metadata params
    mirror :func:`record_success`.
    """
    summary = f"{type(exc).__name__}: {exc}"
    # Cap the summary so a multi-line message does not bloat the
    # snapshot dict view.
    if len(summary) > 200:
        summary = summary[:197] + "..."
    recorded_at = _now()
    _RECORDED[name] = StartupOutcome(
        name=name,
        success=False,
        error=summary,
        recorded_at=recorded_at,
        started_at=started_at,
        duration_ms=_duration_ms(started_at, recorded_at),
        metadata=dict(metadata) if metadata else {},
    )


@contextlib.contextmanager
def record_phase(
    name: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Context manager: time a startup phase and record success/failure.

    Replaces the explicit try/except + ``record_success`` /
    ``record_failure`` pattern with a single block; ``started_at`` is
    captured automatically on entry, and the exception (if any) is
    recorded then re-raised so the caller's existing error handling
    continues to apply.

    Usage::

        from core.runtime import startup_outcome

        with startup_outcome.record_phase("db_init"):
            await db.init()
    """
    started_at = _now()
    try:
        yield
    except BaseException as exc:
        record_failure(name, exc, started_at=started_at, metadata=metadata)
        raise
    else:
        record_success(name, started_at=started_at, metadata=metadata)


def all_outcomes() -> tuple[StartupOutcome, ...]:
    """Return every recorded outcome, sorted by phase name."""
    return tuple(sorted(_RECORDED.values(), key=lambda o: o.name))


def get(name: str) -> StartupOutcome | None:
    """Return the outcome for *name*, or ``None`` if never recorded."""
    return _RECORDED.get(name)


def summary_status(
    outcomes: tuple[StartupOutcome, ...] | None = None,
) -> SummaryStatus:
    """Derive the overall :class:`SummaryStatus` from ``outcomes``.

    ``None`` reads the live recorder state. Mapping:

    * no outcomes recorded                        → ``EMPTY``
    * every recorded outcome succeeded            → ``OK``
    * every recorded outcome failed               → ``FAILED``
    * otherwise (mix)                             → ``DEGRADED``
    """
    if outcomes is None:
        outcomes = all_outcomes()
    if not outcomes:
        return SummaryStatus.EMPTY
    successes = sum(1 for o in outcomes if o.success)
    failures = len(outcomes) - successes
    if failures == 0:
        return SummaryStatus.OK
    if successes == 0:
        return SummaryStatus.FAILED
    return SummaryStatus.DEGRADED


# ---------------------------------------------------------------------------
# Extension-load recorder (LP — bot awareness PR3)
#
# A SIBLING of the catalogue-phase recorder above — deliberately *not* a
# KNOWN_PHASES entry.  Cog loading is a separate, higher-cardinality concern
# (one row per extension), and KNOWN_PHASES is pinned by the readiness
# snapshot + smoke-test docs; widening it would churn those contracts.  The
# health snapshot's ``extensions`` adapter reads these outcomes.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtensionLoadOutcome:
    """One cog/extension load result, recorded by ``bot1._load_cogs()``.

    ``error`` is ``None`` on success and a short ``type:message`` string on
    failure (no traceback, mirroring :class:`StartupOutcome`).
    """

    name: str
    success: bool
    error: str | None
    recorded_at: datetime.datetime


_EXTENSIONS: dict[str, ExtensionLoadOutcome] = {}


def record_extension_success(name: str) -> None:
    """Record a successful extension load. Overwrites prior state; never raises."""
    _EXTENSIONS[name] = ExtensionLoadOutcome(
        name=name,
        success=True,
        error=None,
        recorded_at=_now(),
    )


def record_extension_failure(name: str, exc: BaseException) -> None:
    """Record a failed extension load (short ``type:message``; no traceback)."""
    summary = f"{type(exc).__name__}: {exc}"
    if len(summary) > 200:
        summary = summary[:197] + "..."
    _EXTENSIONS[name] = ExtensionLoadOutcome(
        name=name,
        success=False,
        error=summary,
        recorded_at=_now(),
    )


def all_extension_outcomes() -> tuple[ExtensionLoadOutcome, ...]:
    """Every recorded extension outcome, sorted by name."""
    return tuple(sorted(_EXTENSIONS.values(), key=lambda o: o.name))


def reset_for_tests() -> None:
    """Clear every recorded outcome (catalogue phases + extensions).

    Test isolation hook — call from a ``pytest.fixture(autouse=True)``
    so module-level state does not leak between cases.
    """
    _RECORDED.clear()
    _EXTENSIONS.clear()


__all__ = [
    "KNOWN_PHASES",
    "ExtensionLoadOutcome",
    "StartupOutcome",
    "SummaryStatus",
    "all_extension_outcomes",
    "all_outcomes",
    "get",
    "record_extension_failure",
    "record_extension_success",
    "record_failure",
    "record_phase",
    "record_success",
    "reset_for_tests",
    "summary_status",
]
