"""Process-local, content-free media (YouTube) diagnostics counters.

State class: **process-local runtime** — see ``docs/architecture.md``
§"State classification".  These counters reset on restart; they are an
operator convenience surface (``!platform media`` + the ``media``
diagnostics provider), not a durable record.

**Content-free contract (P0-2 / Q-0099 follow-up).**  Nothing in this module
ever stores or surfaces provider *content* — no descriptions, titles, channel
names, transcript text, AI summaries, raw provider bodies, video IDs, or the
``YOUTUBE_API_KEY`` value.  It records only:

* **provider-request outcome counters** — how many metadata fetches landed in
  each bounded outcome category;
* **last physical-purge outcome** — row count + timestamp + ok/failed, mirroring
  what ``MediaMaintenanceCog`` already logs (a count, never content).

The outcome taxonomy is the bounded ``YouTubeFetchError.reason`` set plus the
``success``/``timeout`` cases the fetcher does not otherwise classify:

    success | key_missing | private_or_deleted | quota_limited |
    timeout | fetch_error

Unknown categories are folded into ``fetch_error`` so a future reason string can
never blow up the bounded label set.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from services import metrics

# Bounded outcome categories.  ``fetch_error`` is the catch-all so an
# unrecognised reason string can never grow this set unboundedly.
PROVIDER_OUTCOMES: tuple[str, ...] = (
    "success",
    "key_missing",
    "private_or_deleted",
    "quota_limited",
    "timeout",
    "fetch_error",
)

# Maps the bounded ``YouTubeFetchError.reason`` strings to an outcome category.
_REASON_TO_OUTCOME: dict[str, str] = {
    "youtube_api_key_missing": "key_missing",
    "video_private_or_deleted": "private_or_deleted",
    "quota_limited": "quota_limited",
    "fetch_error": "fetch_error",
}

_OUTCOME_COUNTERS: dict[str, int] = {outcome: 0 for outcome in PROVIDER_OUTCOMES}


@dataclass(frozen=True)
class LastPurge:
    """The most recent physical-purge outcome (content-free)."""

    rows: int
    at: datetime
    ok: bool


_LAST_PURGE: LastPurge | None = None


def outcome_for_reason(reason: str) -> str:
    """Map a ``YouTubeFetchError.reason`` to a bounded outcome category."""
    return _REASON_TO_OUTCOME.get(reason, "fetch_error")


def record_provider_outcome(category: str) -> None:
    """Increment the process-local + Prometheus counter for ``category``.

    Unknown categories are folded into ``fetch_error`` to keep the label set
    bounded.
    """
    if category not in _OUTCOME_COUNTERS:
        category = "fetch_error"
    _OUTCOME_COUNTERS[category] += 1
    metrics.youtube_provider_request_total.labels(outcome=category).inc()


def provider_outcome_counters() -> dict[str, int]:
    """Return a copy of the process-local outcome counters."""
    return dict(_OUTCOME_COUNTERS)


def record_purge(rows: int, *, ok: bool) -> None:
    """Record the most recent physical-purge outcome (row count only)."""
    global _LAST_PURGE
    _LAST_PURGE = LastPurge(rows=rows, at=datetime.now(timezone.utc), ok=ok)


def last_purge_snapshot() -> dict[str, object] | None:
    """Return the last purge as a serialisable dict, or ``None`` if never run."""
    if _LAST_PURGE is None:
        return None
    return {
        "rows": _LAST_PURGE.rows,
        "at": _LAST_PURGE.at.isoformat(),
        "ok": _LAST_PURGE.ok,
    }


def snapshot() -> dict[str, object]:
    """Process-local snapshot for the ``media`` diagnostics provider.

    Content-free: outcome counters + last-purge outcome only.
    """
    return {
        "provider_outcomes": provider_outcome_counters(),
        "last_purge": last_purge_snapshot(),
    }


def _reset_for_tests() -> None:
    """Wipe module state.  Tests call this in their setup/teardown fixture."""
    global _LAST_PURGE
    for outcome in _OUTCOME_COUNTERS:
        _OUTCOME_COUNTERS[outcome] = 0
    _LAST_PURGE = None


__all__ = [
    "PROVIDER_OUTCOMES",
    "LastPurge",
    "outcome_for_reason",
    "record_provider_outcome",
    "provider_outcome_counters",
    "record_purge",
    "last_purge_snapshot",
    "snapshot",
]
