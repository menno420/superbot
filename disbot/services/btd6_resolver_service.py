"""Deterministic NL → structured intent resolver for BTD6.

Takes a free-form message and returns a typed :class:`ResolvedIntent`
that downstream services consume. No AI involved: aliases come from
the validated dataset in :mod:`services.btd6_data_service`.

The resolver is intentionally narrow:

* It recognises tower / hero / map / mode / bloon references by
  canonical name or alias (case-insensitive, word-boundary aware).
* It extracts an integer round number when the text mentions
  ``round <N>`` or ``r<N>``.
* It computes a confidence score in ``[0.0, 1.0]`` based on how
  many entities matched and how unambiguous the match was.
* It surfaces ambiguous matches when two different aliases share a
  prefix (e.g. operator typed ``"bom"`` matching both bomb and a
  hypothetical boomerang abbreviation).

Higher layers decide what to do with the intent — the resolver is
read-only and never calls a provider.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from services.btd6_data_service import (
    BloonEntry,
    HeroEntry,
    MapEntry,
    ModeEntry,
    RelicEntry,
    RoundEntry,
    TowerEntry,
    get_dataset,
    get_round,
)
from services.btd6_resolver_vocabulary import resolve_live_entities

_ROUND_PATTERNS = (
    re.compile(r"\bround\s+(\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\br\s*(\d{1,3})\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ResolvedIntent:
    """Structured view of what the user appears to be asking about."""

    raw_text: str
    confidence: float
    towers: tuple[TowerEntry, ...] = ()
    heroes: tuple[HeroEntry, ...] = ()
    maps: tuple[MapEntry, ...] = ()
    modes: tuple[ModeEntry, ...] = ()
    rounds: tuple[RoundEntry, ...] = ()
    bloons: tuple[BloonEntry, ...] = ()
    # Contested Territory relics named in the text (Camo Trap, SMS, …).
    ct_relics: tuple[RelicEntry, ...] = ()
    ambiguous_terms: tuple[str, ...] = ()
    candidate_round_numbers: tuple[int, ...] = field(default_factory=tuple)
    # PR-E: live Ninja Kiwi entities (races, bosses, CT, odyssey,
    # challenges, events, leaderboards). Each entry carries the
    # parser-produced ``entity_kind`` only — the entity_key is
    # resolved downstream against the latest fact envelope per kind.
    live_entities: tuple[Any, ...] = ()


def _word_iter(text: str) -> list[str]:
    """Lowercase tokens for whole-word matching, with punctuation stripped."""
    return re.findall(r"[a-z0-9_]+", text.lower())


def _match_terms(
    text: str,
    name_aliases: dict[str, str],
) -> tuple[set[str], list[str]]:
    """Return matching ids and any ambiguous-prefix terms.

    ``name_aliases`` maps each lowercase alias / canonical token to
    its owner id. Multi-word aliases are matched as a substring;
    single-word aliases are matched on word boundaries.
    """
    found, _terms = _match_terms_collect(text, name_aliases)
    return found, []


def _match_terms_collect(
    text: str,
    name_aliases: dict[str, str],
) -> tuple[set[str], list[str]]:
    """Like :func:`_match_terms` but also returns the matched alias strings.

    The matched surface terms let the caller mask them out of the text
    (see relic-vs-fixture precedence in :func:`resolve`).

    Single-word aliases also match their naive plural (``alias + "s"``):
    multi-word names get plural tolerance for free from substring matching
    ("dart monkeys" contains "dart monkey"), but a single-word token like
    "despos" matched nothing even with a "despo" alias on record (BUG-0003,
    2026-06-11). Only the known-alias+s direction is tried, so no new
    surface terms are invented.
    """
    text_lower = text.lower()
    tokens = set(_word_iter(text))
    found: set[str] = set()
    terms: list[str] = []
    for alias, owner_id in name_aliases.items():
        hit = (
            (alias in text_lower)
            if " " in alias
            else (alias in tokens or f"{alias}s" in tokens)
        )
        if hit:
            found.add(owner_id)
            terms.append(alias)
    return found, terms


def _build_alias_map() -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    dataset = get_dataset()
    towers = {}
    for tower in dataset.towers:
        towers[tower.id] = tower.id
        towers[tower.canonical.lower()] = tower.id
        for alias in tower.aliases:
            towers[alias.lower()] = tower.id
    heroes = {}
    for hero in dataset.heroes:
        heroes[hero.id] = hero.id
        heroes[hero.canonical.lower()] = hero.id
        for alias in hero.aliases:
            heroes[alias.lower()] = hero.id
    maps = {}
    for game_map in dataset.maps:
        maps[game_map.id] = game_map.id
        maps[game_map.canonical.lower()] = game_map.id
        for alias in game_map.aliases:
            maps[alias.lower()] = game_map.id
    modes = {}
    for mode in dataset.modes:
        modes[mode.id] = mode.id
        modes[mode.canonical.lower()] = mode.id
        for alias in mode.aliases:
            modes[alias.lower()] = mode.id
    bloons = {}
    for bloon in dataset.bloons:
        bloons[bloon.id] = bloon.id
        bloons[bloon.canonical.lower()] = bloon.id
        for alias in bloon.aliases:
            bloons[alias.lower()] = bloon.id
    return towers, heroes, maps, modes, bloons


def _build_relic_alias_map() -> dict[str, str]:
    """Surface term (canonical / abbrev / alias) → relic id."""
    relics: dict[str, str] = {}
    for relic in get_dataset().ct_relics:
        relics[relic.canonical.lower()] = relic.id
        if relic.abbrev:
            relics[relic.abbrev.lower()] = relic.id
        for alias in relic.aliases:
            relics[alias.lower()] = relic.id
    return relics


def _mask_terms(text: str, terms: list[str]) -> str:
    """Blank out ``terms`` (longest first) from ``text``, case-insensitively.

    Used so a matched relic phrase (e.g. ``"camo trap"`` or ``"super
    monkey storm"``) cannot also trip the nested fixture match (the camo
    *bloon* / the Super Monkey *tower*).
    """
    masked = text
    for term in sorted(terms, key=len, reverse=True):
        masked = re.sub(re.escape(term), " ", masked, flags=re.IGNORECASE)
    return masked


def resolve(text: str) -> ResolvedIntent:
    """Resolve free-form ``text`` into a :class:`ResolvedIntent`."""
    if not text or not text.strip():
        return ResolvedIntent(raw_text=text, confidence=0.0)

    tower_map, hero_map, map_map, mode_map, bloon_map = _build_alias_map()
    dataset = get_dataset()

    # Resolve CT relics first, then mask the matched phrases out of the text
    # used for fixture matching so e.g. "camo trap" / "super monkey storm"
    # don't also match the camo bloon / Super Monkey tower.
    relic_ids, relic_terms = _match_terms_collect(text, _build_relic_alias_map())
    fixture_text = _mask_terms(text, relic_terms) if relic_terms else text

    tower_ids, _ = _match_terms(fixture_text, tower_map)
    hero_ids, _ = _match_terms(fixture_text, hero_map)
    map_ids, _ = _match_terms(fixture_text, map_map)
    mode_ids, _ = _match_terms(fixture_text, mode_map)
    bloon_ids, _ = _match_terms(fixture_text, bloon_map)

    candidate_rounds: list[int] = []
    rounds: list[RoundEntry] = []
    for pattern in _ROUND_PATTERNS:
        for match in pattern.finditer(text):
            try:
                value = int(match.group(1))
            except ValueError:
                continue
            if 1 <= value <= 200 and value not in candidate_rounds:
                candidate_rounds.append(value)
                entry = get_round(value)
                if entry is not None:
                    rounds.append(entry)

    # PR-E: live NK entity vocabulary.
    live_entities, ambiguous = resolve_live_entities(text)

    matched_count = (
        len(tower_ids)
        + len(hero_ids)
        + len(map_ids)
        + len(mode_ids)
        + len(bloon_ids)
        + len(relic_ids)
        + len(candidate_rounds)
        + len(live_entities)
    )
    # Confidence model: linear scale up to 3 matched entities, capped at 1.0.
    confidence = min(1.0, matched_count / 3.0) if matched_count else 0.0

    return ResolvedIntent(
        raw_text=text,
        confidence=confidence,
        towers=tuple(t for t in dataset.towers if t.id in tower_ids),
        heroes=tuple(h for h in dataset.heroes if h.id in hero_ids),
        maps=tuple(m for m in dataset.maps if m.id in map_ids),
        modes=tuple(m for m in dataset.modes if m.id in mode_ids),
        rounds=tuple(rounds),
        bloons=tuple(b for b in dataset.bloons if b.id in bloon_ids),
        ct_relics=tuple(r for r in dataset.ct_relics if r.id in relic_ids),
        candidate_round_numbers=tuple(candidate_rounds),
        ambiguous_terms=tuple(ambiguous),
        live_entities=tuple(live_entities),
    )
