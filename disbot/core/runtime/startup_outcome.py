"""Startup outcome recorder — PR-01b.

A tiny sync module that records whether each phase of startup
(``command_surface_ledger`` / ``settings_registry`` / ``customization_catalogue``
/ ``resource_provisioning_catalogue``) built successfully.  Each phase
in ``bot1.py`` already runs under its own ``try/except`` and continues
on failure; the recorder turns that previously-invisible state into an
observable record that the readiness snapshot can read sync.

Public surface:

    StartupOutcome           — frozen dataclass per recorded phase
    record_success(name)     — called inside a try block
    record_failure(name, exc) — called inside an except clause
    all_outcomes()           — sorted tuple of every recorded outcome
    reset_for_tests()        — clears the recorder state (pytest fixture)

The recorder is process-local, sync-only, and never raises.  It does
not register a diagnostics provider on its own — ``platform_consistency``
composes the outcomes into the readiness snapshot whose provider name
is ``"platform_readiness"``.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

# Canonical phase names recorded by bot1.py at startup.  Code that
# adds a new phase must add its name here so the readiness snapshot
# can distinguish "phase ran and succeeded" from "phase did not run
# (unknown)" — the latter would be a regression that the
# orchestrator never reached the recorder.
KNOWN_PHASES: tuple[str, ...] = (
    "command_surface_ledger",
    "settings_registry",
    "customization_catalogue",
    "resource_provisioning_catalogue",
)


@dataclass(frozen=True)
class StartupOutcome:
    """One recorded phase outcome.

    ``error`` is ``None`` on success and a short ``type:message``
    string on failure (so the snapshot dict view is safe to serialise
    without leaking long stack traces).
    """

    name: str
    success: bool
    error: str | None
    recorded_at: datetime.datetime


_RECORDED: dict[str, StartupOutcome] = {}


def record_success(name: str) -> None:
    """Record a successful phase run.

    Overwrites any prior record for the same name so a hot-reload
    rebuild flips the state back to success.  Never raises.
    """
    _RECORDED[name] = StartupOutcome(
        name=name,
        success=True,
        error=None,
        recorded_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


def record_failure(name: str, exc: BaseException) -> None:
    """Record a failed phase run.

    Stores a short ``type:message`` summary; never holds the
    exception traceback.  Never raises.
    """
    summary = f"{type(exc).__name__}: {exc}"
    # Cap the summary so a multi-line message does not bloat the
    # snapshot dict view.
    if len(summary) > 200:
        summary = summary[:197] + "..."
    _RECORDED[name] = StartupOutcome(
        name=name,
        success=False,
        error=summary,
        recorded_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


def all_outcomes() -> tuple[StartupOutcome, ...]:
    """Return every recorded outcome, sorted by phase name."""
    return tuple(sorted(_RECORDED.values(), key=lambda o: o.name))


def get(name: str) -> StartupOutcome | None:
    """Return the outcome for *name*, or ``None`` if never recorded."""
    return _RECORDED.get(name)


def reset_for_tests() -> None:
    """Clear every recorded outcome.

    Test isolation hook — call from a ``pytest.fixture(autouse=True)``
    so module-level state does not leak between cases.
    """
    _RECORDED.clear()


__all__ = [
    "KNOWN_PHASES",
    "StartupOutcome",
    "all_outcomes",
    "get",
    "record_failure",
    "record_success",
    "reset_for_tests",
]
