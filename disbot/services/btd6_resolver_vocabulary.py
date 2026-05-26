"""BTD6 resolver vocabulary for live Ninja Kiwi entities (PR-E).

The original resolver (towers / heroes / maps / modes / rounds) was
fed from the validated fixture dataset. M3B added live-entity
parsers (races, bosses, contested-territory, odyssey, challenges,
events) that emit ``entity_kind`` values like ``btd6_race``,
``btd6_boss``, ``btd6_ct``, ``btd6_odyssey``, ``btd6_challenge``,
``btd6_event``. Surface terms that map to those kinds live here in
one registry so :mod:`services.btd6_resolver_service` does not grow
its inline term sprawl.

Each entry is a tuple of ``(surface_terms, entity_kind)`` where
``surface_terms`` is a frozen set of lowercased substrings to match
against the message text. Matching is whole-word for single words
and substring for multi-word phrases — mirroring the existing
resolver's ``_match_terms`` semantics.

The ``entity_key`` is *not* known at vocabulary time — the resolver
recognises that the user is talking about a kind of entity (e.g.
"the current race") and emits one or more :class:`LiveEntityMatch`
records. The context service translates those into
:class:`btd6_fact_store.BTD6FactQuery` rows; the actual entity key
comes from the fact store search (``entity_kind`` only — fact_type
left None — picks the newest envelope per kind).

Ambiguous terms — ones that could mean multiple kinds — are
explicitly listed in :data:`_AMBIGUOUS_TERMS` so the resolver can
emit an ``ambiguous_term`` audit row instead of silently picking
one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class LiveEntityMatch:
    """One resolved live-entity intent.

    ``entity_kind`` is the parser-produced kind label (e.g.
    ``btd6_race``). ``matched_term`` is the surface term that
    triggered the match — useful for diagnostics.
    """

    entity_kind: str
    matched_term: str


# Each entry: (surface_terms, entity_kind, fact_type_hint).
# The fact_type_hint is optional and may be None; the context
# service uses fact_type=None to match any fact_type for the kind.
_VOCABULARY: Final[tuple[tuple[frozenset[str], str, str | None], ...]] = (
    (
        frozenset(
            {
                "race",
                "races",
                "racing",
                "time trial",
                "time trials",
                "reversed loop",
            },
        ),
        "btd6_race",
        None,
    ),
    (
        frozenset(
            {
                "boss",
                "bosses",
                "bloonarius",
                "phayze",
                "lych",
                "vortex",
                "dreadbloon",
                "blastapopoulos",
                "diamondback",
            },
        ),
        "btd6_boss",
        None,
    ),
    (
        frozenset(
            {
                "ct",
                "contested territory",
                "contested territories",
            },
        ),
        "btd6_ct",
        None,
    ),
    (
        frozenset(
            {
                "ct tile",
                "ct tiles",
                "contested territory tile",
                "contested territory tiles",
                "relic tile",
                "relic tiles",
            },
        ),
        "btd6_ct_tile",
        None,
    ),
    (
        frozenset(
            {
                "odyssey",
                "odysseys",
                "easy odyssey",
                "medium odyssey",
                "hard odyssey",
                "extreme odyssey",
            },
        ),
        "btd6_odyssey",
        None,
    ),
    (
        frozenset(
            {
                "challenge",
                "challenges",
                "daily challenge",
                "weekly challenge",
                "advanced challenge",
                "rot challenge",
            },
        ),
        "btd6_challenge",
        None,
    ),
    (
        frozenset(
            {
                "event",
                "events",
                "live event",
                "live events",
            },
        ),
        "btd6_event",
        None,
    ),
    (
        frozenset(
            {
                "leaderboard",
                "leaderboards",
                "lb",
                "race leaderboard",
                "boss leaderboard",
            },
        ),
        "btd6_race_leaderboard_row",
        None,
    ),
)


# Terms that overlap multiple kinds — refuse to resolve when these
# appear in isolation to avoid silently picking a kind.
_AMBIGUOUS_TERMS: Final[frozenset[str]] = frozenset(
    {
        # "current" by itself could mean the current race, boss, CT, odyssey,
        # event, challenge — refuse.
        "current",
    },
)


_WORD_RE = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def resolve_live_entities(text: str) -> tuple[list[LiveEntityMatch], list[str]]:
    """Scan ``text`` for vocabulary terms.

    Returns ``(matches, ambiguous_terms)``. ``ambiguous_terms`` is the
    set of recognised-but-ambiguous terms the resolver should refuse
    on. Matches retain their order of vocabulary entry; duplicates
    per ``(entity_kind, matched_term)`` are de-duplicated.
    """
    if not text or not text.strip():
        return [], []
    lower = text.lower()
    tokens = _tokens(text)

    matches: list[LiveEntityMatch] = []
    seen: set[tuple[str, str]] = set()
    for surface_terms, entity_kind, _ft in _VOCABULARY:
        for term in surface_terms:
            if " " in term:
                if term in lower:
                    key = (entity_kind, term)
                    if key not in seen:
                        seen.add(key)
                        matches.append(
                            LiveEntityMatch(
                                entity_kind=entity_kind,
                                matched_term=term,
                            ),
                        )
            elif term in tokens:
                key = (entity_kind, term)
                if key not in seen:
                    seen.add(key)
                    matches.append(
                        LiveEntityMatch(entity_kind=entity_kind, matched_term=term),
                    )

    ambiguous = [t for t in _AMBIGUOUS_TERMS if t in tokens]
    return matches, ambiguous


def known_entity_kinds() -> frozenset[str]:
    """Return every entity_kind the registry can produce."""
    return frozenset(entry[1] for entry in _VOCABULARY)


__all__ = [
    "LiveEntityMatch",
    "known_entity_kinds",
    "resolve_live_entities",
]
