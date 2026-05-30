"""Channel-name classifier — pure text heuristics, no I/O.

Given a Discord channel name, :func:`classify_channel_name` returns the
opinionated "this looks like a …" tags that match it (log / mod-log /
bot-command / admin / game / welcome / …).  The result is a *suggestion*
only — it never reads or writes anything.

This lives in ``utils/`` because it is needed by both ``views/`` (the
setup wizard's server-scan panel renders the tags) and ``services/``
(channel recommendation, cleanup profiling, and cog-routing all score
channels by these tags).  A function needed by both layers belongs in
``utils/`` — keeping it in ``views/`` forced three services to import
``views.setup.scan_panel`` (the zero-tolerance ``services/ → views/``
boundary breach tracked as arch-fix-1).

Tests pin the patterns directly against this module so the name
heuristics stay stable independent of any UI surface.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Channel classifier
# ---------------------------------------------------------------------------


# Each tag's pattern set is anchored at word boundaries so "general" doesn't
# match "general-store" by accident.  Multiple patterns per tag widen the
# match — e.g. both "log" and "audit" suggest a log channel.
_NAME_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "likely_log": (
        re.compile(r"\blogs?\b"),
        re.compile(r"\baudit\b"),
        re.compile(r"\bmod[-_]?logs?\b"),
        re.compile(r"\bbot[-_]?logs?\b"),
    ),
    "likely_mod_log": (
        re.compile(r"\bmod[-_]?logs?\b"),
        re.compile(r"\bmoderation[-_]?logs?\b"),
        re.compile(r"\bstaff[-_]?logs?\b"),
    ),
    "likely_bot_cmd": (
        re.compile(r"\bbot[-_]?(?:cmd|cmds|commands?|spam)\b"),
        re.compile(r"\bcmds?\b"),
        re.compile(r"\bcommands?\b"),
    ),
    "likely_admin": (
        re.compile(r"\badmin\b"),
        re.compile(r"\bowner\b"),
        re.compile(r"\bstaff[-_]?only\b"),
    ),
    "likely_mod": (
        re.compile(r"\bmods?\b"),
        re.compile(r"\bmoderation\b"),
        re.compile(r"\bstaff\b"),
    ),
    "likely_proof": (
        re.compile(r"\bproofs?\b"),
        re.compile(r"\bevidence\b"),
    ),
    "likely_counting": (
        re.compile(r"\bcounting\b"),
        re.compile(r"\bcount\b"),
    ),
    "likely_mining": (
        re.compile(r"\bmining\b"),
        re.compile(r"\bmine\b"),
    ),
    "likely_game": (
        re.compile(r"\bgames?\b"),
        re.compile(r"\bbet(?:s|ting)?\b"),
        re.compile(r"\bcasino\b"),
        re.compile(r"\bblackjack\b"),
        re.compile(r"\brps\b"),
        re.compile(r"\bdeathmatch\b"),
        re.compile(r"\btournament\b"),
    ),
    "likely_general": (
        re.compile(r"\bgeneral\b"),
        re.compile(r"\blobby\b"),
        re.compile(r"\bchat\b"),
    ),
    "likely_welcome": (
        re.compile(r"\bwelcome\b"),
        re.compile(r"\bintro\b"),
        re.compile(r"\bgreetings?\b"),
    ),
}


def classify_channel_name(name: str) -> tuple[str, ...]:
    """Return the classifier tags that match ``name`` (lowercased).

    A channel can match multiple tags (a ``mod-log`` channel matches
    ``likely_log`` AND ``likely_mod_log``).  Returned tags are sorted
    for deterministic embed output.
    """
    if not name:
        return ()
    lowered = name.lower()
    tags = [
        tag
        for tag, patterns in _NAME_PATTERNS.items()
        if any(p.search(lowered) for p in patterns)
    ]
    return tuple(sorted(tags))


__all__ = ["classify_channel_name"]
