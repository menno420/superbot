"""Tests for the dashboard rate limiter (``dashboard/ratelimit.py``).

Stdlib-only and deterministic (an injected ``now``), so these run in CI without
the dashboard's web deps — unlike the ``importorskip``-guarded app smoke test.
"""

from __future__ import annotations

import sys
from pathlib import Path

_DASHBOARD = Path(__file__).resolve().parents[3] / "dashboard"
if str(_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD))

import ratelimit  # noqa: E402


def test_allows_up_to_limit_then_rejects():
    lim = ratelimit.SlidingWindowLimiter(max_events=3, window_seconds=60.0)
    assert lim.allow("k", now=100.0) is True
    assert lim.allow("k", now=100.0) is True
    assert lim.allow("k", now=100.0) is True
    assert lim.allow("k", now=100.0) is False  # 4th within the window → rejected


def test_window_slides():
    lim = ratelimit.SlidingWindowLimiter(max_events=1, window_seconds=10.0)
    assert lim.allow("k", now=0.0) is True
    assert lim.allow("k", now=5.0) is False  # still inside the 10s window
    assert lim.allow("k", now=11.0) is True  # earlier hit aged out


def test_keys_are_independent():
    lim = ratelimit.SlidingWindowLimiter(max_events=1, window_seconds=60.0)
    assert lim.allow("a", now=0.0) is True
    assert lim.allow("b", now=0.0) is True  # different key has its own budget
    assert lim.allow("a", now=0.0) is False


def test_rejected_call_does_not_consume_budget():
    lim = ratelimit.SlidingWindowLimiter(max_events=1, window_seconds=10.0)
    assert lim.allow("k", now=0.0) is True
    assert lim.allow("k", now=1.0) is False
    assert lim.allow("k", now=2.0) is False  # still rejected; no extra consumption
    assert lim.allow("k", now=11.0) is True  # the single hit aged out → allowed


def test_reset_clears_state():
    lim = ratelimit.SlidingWindowLimiter(max_events=1, window_seconds=60.0)
    assert lim.allow("k", now=0.0) is True
    assert lim.allow("k", now=0.0) is False
    lim.reset()
    assert lim.allow("k", now=0.0) is True
