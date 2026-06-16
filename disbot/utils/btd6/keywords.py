"""Curated BTD6 context keywords — shared by the task router and the
answer-faithfulness guard.

Promoted verbatim from :mod:`services.ai_task_router` so the router's
fast-path hint and the natural-language stage's general-path leak guard read
**one** list (no drift). The router imports :data:`BTD6_CONTEXT_KEYWORDS` back
as its private ``_BTD6_KEYWORDS`` — the values are identical, so the router's
keyword tests are unaffected.

Curated to avoid over-routing: bare ``event`` / ``active`` / ``leaderboard``
are deliberately absent (they would over-route server events, "is the bot
active", XP leaderboards). ``paragon`` is deliberately excluded — it is
legitimate English ("a paragon of virtue"), so a bare substring would
over-trigger; paragon questions usually name a tower or a (multi-word) paragon
proper name, which the entity matcher / name index covers. ``obyn`` and
``desperado`` are explicit because the entity-alias matcher provably misses
them (the bare 4-char alias is length-filtered; single-word tower names are
skipped as too generic).
"""

from __future__ import annotations

import re

# The "in ABR" qualifier (BUG-0010): one cue shared by the grounding round
# legs and the round-cash workflow so they can never drift. "abr" is a
# distinctive token; "alternate bloons( rounds)" is the spelled form.
ABR_CUE_RE = re.compile(r"\babr\b|\balternate\s+bloons?\b", re.IGNORECASE)

# A paragon "degree" named in a query (BUG-0015): "degree 67", "deg 67", or the
# shorthand "d67" players type. Only paragons have degrees (1-100), so a match
# is only acted on when a paragon is also in scope — the router routes a degree
# token + a paragon reference, and the grounding leg surfaces the exact
# per-degree stats. One cue shared by both so they can never drift (the
# ABR_CUE_RE pattern). The "d67" shorthand is digit-boundary guarded so a round
# ("r67"), a version ("v55"), or a mid-token "d" ("5d6", "add 7") never match;
# the digit run is capped at 3 and range-checked to 1-100 by degree_in_text.
DEGREE_CUE_RE = re.compile(
    r"\bdegrees?\s*-?\s*(\d{1,3})\b"  # "degree 67", "degree-67", "degrees 67"
    r"|\bdeg\.?\s*(\d{1,3})\b"  # "deg 67", "deg.67", "deg67"
    r"|\bd(\d{1,3})\b",  # the bare "d67" shorthand
    re.IGNORECASE,
)


def degree_in_text(text: str) -> int | None:
    """The paragon degree (1-100) named in ``text``, or None.

    Recognises "degree 67", "deg 67", and the "d67" shorthand players use.
    A degree runs 1-100, so out-of-range values (a stray "d255", "degree 0")
    return None rather than reading as a degree. Callers gate on a paragon also
    being in scope — "d67" alone is ambiguous, "d67 dart paragon" is not.
    """
    for match in DEGREE_CUE_RE.finditer(text or ""):
        raw = next((group for group in match.groups() if group is not None), None)
        if raw is None:
            continue
        value = int(raw)
        if 1 <= value <= 100:  # a paragon degree is 1..100 (paragon_math.MAX_DEGREE)
            return value
    return None


BTD6_CONTEXT_KEYWORDS: tuple[str, ...] = (
    "btd6",
    "bloons",
    "bloon",
    "moab",
    "ddt",
    "bfb",
    "zomg",
    "tower",
    "hero",
    "monkey",
    "chimps",
    "round ",
    "freeplay",
    "deflation",
    "apopalypse",
    # "impop" covers "impoppable" too (substring match) AND the shorthand
    # players actually type ("cost on impop") — the live despos question
    # (BUG-0003, 2026-06-11) carried no other BTD6 cue and went unrouted.
    "impop",
    "half cash",
    # Symmetry with "half cash" (asymmetry surfaced 2026-06-11: a reply
    # naming the Double Cash mode had no routable question form).
    "double cash",
    "2x cash",
    "primary only",
    "military only",
    "magic only",
    "support only",
    "boss bloon",
    "boss event",
    "current boss",
    "current race",
    "current event",
    "what boss",
    "what race",
    "what odyssey",
    "active boss",
    "active race",
    "ninja kiwi",
    "ninjakiwi",
    "odyssey",
    "contested territory",
    "race ",
    "banned hero",
    "banned tower",
    "obyn",
    "desperado",
    # The Desperado shorthand players use ("despo(s)") — distinctive, never
    # ordinary English; also a towers.json alias so grounding resolves it.
    "despo",
    # Farm-economy questions ("how much money does a 420 farm make", "what
    # does banana central cost") carried no other cue (live miss 2026-06-11).
    # "farm" alone is too collision-prone (mining/harvest chat) — the router
    # rescues it behind a money cue; "banana" is distinctive enough bare.
    "banana",
)


def has_btd6_context(text: str) -> bool:
    """True when ``text`` contains any curated BTD6 context keyword.

    Case-insensitive substring scan — the same test the router uses for its
    fast-path. The answer guard uses it to decide whether a
    ``GENERAL_NL_ANSWER`` reply that happens to name a BTD6 entity is actually
    BTD6-themed (vs ordinary chat that merely shares a word with a hero name,
    e.g. "Benjamin Franklin"). Distinctive multi-word BTD6 names trigger the
    guard on their own and do not depend on this predicate.
    """
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in BTD6_CONTEXT_KEYWORDS)


__all__ = [
    "ABR_CUE_RE",
    "BTD6_CONTEXT_KEYWORDS",
    "DEGREE_CUE_RE",
    "degree_in_text",
    "has_btd6_context",
]
