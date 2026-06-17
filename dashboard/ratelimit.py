"""In-memory sliding-window rate limiter for the dashboard (stdlib only).

The control panel is a public, live surface. This caps abusive bursts on the two
exposed actions — the OAuth login and the editor POSTs — without a third-party
dependency or a shared store (a single dashboard process is the deploy shape). It
is a coarse abuse-brake, **not** a security boundary: the bot still resolves the
live member and authority-checks every write regardless. State is per-process and
best-effort; a restart simply forgives outstanding counters.
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
