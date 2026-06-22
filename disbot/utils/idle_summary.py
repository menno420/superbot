"""Idle-game shared helpers — the "while you were away" return-moment (pure).

The satisfying core of any *idle* game is the **return moment**: you come back
and the bot tells you what accrued while you were gone. The accrual math already
lives in each game's pure ``settle()`` (``utils/farm``, ``utils/fishing/energy``,
``utils/mining/energy``); this module only **renders the delta** so the copy is
consistent across every idle surface.

Captured as an idea alongside the idle chicken farm
(``docs/ideas/idle-game-offline-summary-2026-06-22.md``) and built as its first
consumer (the farm panel). It is deliberately game-agnostic — the caller passes
the noun and an optional capped note — so a second idle system reuses it as-is.

Pure functions only (no DB, no Discord), so the formatting is unit-testable.
"""

from __future__ import annotations


def format_duration(seconds: int) -> str:
    """Human-readable elapsed/remaining time — ``now`` / ``45s`` / ``2m 05s`` / ``1h 03m``.

    The one duration formatter for idle surfaces (the farm panel's "fills in" and
    the "while you were away" blurb both use it — the de-duplication the idea
    flagged as the rule-of-three start).
    """
    if seconds <= 0:
        return "now"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60:02d}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60:02d}m"


def summarize_idle_gain(
    gained: int,
    elapsed_seconds: int,
    *,
    noun_singular: str,
    noun_plural: str,
    capped: bool = False,
    capped_note: str | None = None,
) -> str | None:
    """The "while you were away" blurb, or ``None`` when nothing accrued.

    Returns ``None`` for a non-positive *gained* — so a panel only narrates the
    return moment once something has actually accrued since the last action (and
    so rapid re-opens within one accrual tick stay quiet). When *capped* and a
    *capped_note* is given, the note is appended to nudge the player to collect.
    """
    if gained <= 0:
        return None
    noun = noun_singular if gained == 1 else noun_plural
    when = format_duration(elapsed_seconds)
    msg = f"🌙 While you were away (**{when}**) you gained **{gained}** {noun}."
    if capped and capped_note:
        msg = f"{msg} {capped_note}"
    return msg
