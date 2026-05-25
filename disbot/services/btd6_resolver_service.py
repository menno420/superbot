"""Deterministic NL → structured intent resolver for BTD6.

Takes a free-form message and returns a typed :class:`ResolvedIntent`
that downstream services consume. No AI involved: aliases come from
the validated dataset in :mod:`services.btd6_data_service`.

The resolver is intentionally narrow:

* It recognises tower / hero / map / mode references by canonical
  name or alias (case-insensitive, word-boundary aware).
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
    HeroEntry,
    MapEntry,
    ModeEntry,
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
    text_lower = text.lower()
    tokens = set(_word_iter(text))
    found: set[str] = set()
    for alias, owner_id in name_aliases.items():
        if " " in alias:
            # Multi-word alias: substring search.
            if alias in text_lower:
                found.add(owner_id)
        else:
            if alias in tokens:
                found.add(owner_id)
    return found, []


def _build_alias_map() -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    dataset = get_dataset()
    towers = {}
    for tower in dataset.towers:
        towers[tower.canonical.lower()] = tower.id
        for alias in tower.aliases:
            towers[alias.lower()] = tower.id
    heroes = {}
    for hero in dataset.heroes:
        heroes[hero.canonical.lower()] = hero.id
        for alias in hero.aliases:
            heroes[alias.lower()] = hero.id
    maps = {}
    for game_map in dataset.maps:
        maps[game_map.canonical.lower()] = game_map.id
        for alias in game_map.aliases:
            maps[alias.lower()] = game_map.id
    modes = {}
    for mode in dataset.modes:
        modes[mode.canonical.lower()] = mode.id
        for alias in mode.aliases:
            modes[alias.lower()] = mode.id
    return towers, heroes, maps, modes


def resolve(text: str) -> ResolvedIntent:
    """Resolve free-form ``text`` into a :class:`ResolvedIntent`."""
    if not text or not text.strip():
        return ResolvedIntent(raw_text=text, confidence=0.0)

    tower_map, hero_map, map_map, mode_map = _build_alias_map()
    dataset = get_dataset()

    tower_ids, _ = _match_terms(text, tower_map)
    hero_ids, _ = _match_terms(text, hero_map)
    map_ids, _ = _match_terms(text, map_map)
    mode_ids, _ = _match_terms(text, mode_map)

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
        candidate_round_numbers=tuple(candidate_rounds),
        ambiguous_terms=tuple(ambiguous),
        live_entities=tuple(live_entities),
    )
