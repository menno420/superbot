"""In-memory sliding-window rate limiter for the public bot site (stdlib only).

A **copy** of the dashboard's proven limiter (``dashboard/ratelimit.py``), kept as
its own module so the two web services share **no** import (plan §2.2 — one data
artifact, independent presentation, no shared package). The bot site has exactly one
write surface — the public, no-login ``/submit`` intake — so this caps abusive bursts
on it without a third-party dependency or a shared store (a single process per Railway
service is the deploy shape).

It is a coarse abuse-brake, **not** a security boundary: every submission still lands
``status='pending'`` (never auto-public) and is moderation-gated before it reaches
GitHub or any public surface (plan §2.3 / §4.2). State is per-process and best-effort;
a restart simply forgives outstanding counters.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """Allow at most ``max_events`` per ``window_seconds`` for each key."""

    def __init__(self, max_events: int, window_seconds: float) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, *, now: float | None = None) -> bool:
        """Record a hit for ``key``; return ``True`` if it is within the limit.

        A rejected call does **not** consume budget, so a client that backs off
        recovers as soon as the window slides past its earlier hits.
        """
        moment = time.monotonic() if now is None else now
        hits = self._hits[key]
        cutoff = moment - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.max_events:
            return False
        hits.append(moment)
        return True

    def reset(self) -> None:
        """Clear all recorded hits (used by tests and on demand)."""
        self._hits.clear()
