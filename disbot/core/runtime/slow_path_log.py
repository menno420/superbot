"""Slow-path ring buffer — Phase S3.2 / O-3.

State class: **process-local runtime** — see ``docs/architecture.md``
§"State classification".

Records the N most recent observations from the S3.1 latency
instrumentation that exceed a configurable ``threshold_ms``.
Complements the Prometheus histograms:

  * Histograms answer "the p99 went up" (aggregate timeseries).
  * Slow-path log answers "and here's what the slow calls actually
    were" (concrete entries with kind, name, duration).

The buffer is bounded — recording costs O(1) memory + O(1) time, so
the helper is safe to call from every hot-path observation site
without throttling.

Surfaced via ``!platform slow`` (Phase S3.2 admin command).  Listed
in the diagnostics registry so ``!platform runtime`` summary
includes the slow-path entry count + threshold.

Public surface:
    maybe_record(kind, name, duration_ms, **extra)  → None
    snapshot()                                       → list[SlowPathEntry]
    configure(*, capacity=, threshold_ms=)           → None
    threshold_ms()                                    → float
    capacity()                                        → int
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SlowPathEntry:
    """One recorded slow observation."""

    timestamp: float  # epoch seconds (time.time())
    kind: str  # "command" | "interaction" | "db_query"
    name: str  # cog/command, prefix, or query_name
    duration_ms: float
    extra: dict[str, Any] = field(default_factory=dict)


# Module-level state — single ring buffer + configuration.
_DEFAULT_CAPACITY = 200
_DEFAULT_THRESHOLD_MS = 500.0

_buffer: deque[SlowPathEntry] = deque(maxlen=_DEFAULT_CAPACITY)
_threshold_ms: float = _DEFAULT_THRESHOLD_MS


def maybe_record(
    kind: str,
    name: str,
    duration_ms: float,
    **extra: Any,
) -> None:
    """Append a slow-path entry if ``duration_ms`` exceeds the threshold.

    Cheap no-op when the call is fast — most observations skip the
    deque append entirely, so the helper can be wired into every
    hot-path observation site without affecting throughput.
    """
    if duration_ms < _threshold_ms:
        return
    _buffer.append(
        SlowPathEntry(
            timestamp=time.time(),
            kind=kind,
            name=name,
            duration_ms=duration_ms,
            extra=dict(extra) if extra else {},
        ),
    )


def snapshot() -> list[SlowPathEntry]:
    """Return a list copy of the current buffer for read-only inspection."""
    return list(_buffer)


def configure(
    *,
    capacity: int | None = None,
    threshold_ms: float | None = None,
) -> None:
    """Reconfigure the buffer.  Existing entries are preserved when the
    capacity is unchanged, dropped when it shrinks.
    """
    global _buffer, _threshold_ms
    if threshold_ms is not None:
        _threshold_ms = threshold_ms
    if capacity is not None and capacity != _buffer.maxlen:
        # deque(maxlen=N) replaces the buffer with a new one truncated
        # to the new bound.  Preserve as many recent entries as fit.
        _buffer = deque(_buffer, maxlen=capacity)


def threshold_ms() -> float:
    """Return the current slow-path threshold in milliseconds."""
    return _threshold_ms


def capacity() -> int:
    """Return the ring buffer's maximum size."""
    return _buffer.maxlen or 0


# ---------------------------------------------------------------------------
# Test surface
# ---------------------------------------------------------------------------


def _reset_for_tests() -> None:
    """Wipe the buffer and restore defaults.  Tests call from setup/teardown."""
    global _buffer, _threshold_ms
    _buffer = deque(maxlen=_DEFAULT_CAPACITY)
    _threshold_ms = _DEFAULT_THRESHOLD_MS


# ---------------------------------------------------------------------------
# Diagnostics registration — Phase S1.3 surface
# ---------------------------------------------------------------------------

from services import diagnostics_service as _diag  # noqa: E402


def _diagnostics_snapshot() -> dict[str, object]:
    return {
        "count": len(_buffer),
        "threshold_ms": _threshold_ms,
        "capacity": capacity(),
    }


_diag.register("slow_path", _diagnostics_snapshot)
