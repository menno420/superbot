from __future__ import annotations

import time


def check_cooldown(last_ts: int, cooldown_seconds: int) -> tuple[bool, int]:
    """
    Check whether a unix-timestamp cooldown has expired.

    Returns (on_cooldown: bool, remaining_seconds: int).
    remaining_seconds is 0 when not on cooldown.
    """
    elapsed = int(time.time()) - last_ts
    if elapsed < cooldown_seconds:
        return True, cooldown_seconds - elapsed
    return False, 0


def format_remaining(seconds: int) -> str:
    """Human-readable representation of a cooldown duration, e.g. '1h 30m' or '45s'."""
    if seconds <= 0:
        return "0s"
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    parts: list[str] = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s and not h:
        parts.append(f"{s}s")
    return " ".join(parts)
