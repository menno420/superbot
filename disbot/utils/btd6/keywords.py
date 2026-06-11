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


__all__ = ["BTD6_CONTEXT_KEYWORDS", "has_btd6_context"]
