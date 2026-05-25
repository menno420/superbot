"""Ninja Kiwi /btd6/races parsers (M3B).

Three parsers share this module:

* :func:`parse_races_index` — ``/btd6/races`` (model ``_btd6race``):
  the directory of race events with leaderboard / metadata URLs.
* :func:`parse_race_metadata` — ``/btd6/races/<raceID>/metadata``
  (model ``_btd6challengedocument``): race rules, restrictions,
  bloon modifiers. Body carries ``id="n/a"``, so the parser needs
  ``path_params["raceID"]`` to compose a stable ``entity_key``.
* :func:`parse_race_leaderboard` — ``/btd6/races/<raceID>/leaderboard``
  (model ``_btd6raceleaderboard``): per-rank score rows. PR2 is
  page-1-only; ``next``/``maxPages`` are read but never followed.

Per the plan, the model name ``_btd6challengedocument`` is shared with
boss / odyssey-maps / challenge metadata; each parser emits a distinct
``fact_type`` so downstream grounding can filter cleanly.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

_SOURCE_INDEX = "nk_btd6_races"
_SOURCE_METADATA = "nk_btd6_races_metadata"
_SOURCE_LEADERBOARD = "nk_btd6_races_leaderboard"


def parse_races_index(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse ``/btd6/races`` into one fact per race event."""
    env = unwrap(payload, _SOURCE_INDEX)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        race_id = entry.get("id")
        if not isinstance(race_id, str) or not race_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.races_index",
                "entity_kind": "btd6_race",
                "entity_key": race_id,
                "body_json": {
                    "id": race_id,
                    "name": entry.get("name"),
                    "start_ms": entry.get("start"),
                    "end_ms": entry.get("end"),
                    "total_scores": entry.get("totalScores"),
                    "leaderboard_url": entry.get("leaderboard"),
                    "metadata_url": entry.get("metadata"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_race_metadata(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse a single race metadata document.

    Body's ``id`` is ``"n/a"`` and ``createdAt`` is ``0``; the real id
    comes from ``path_params["raceID"]``. Without that, the parser
    cannot compose a stable entity_key and returns no facts.
    """
    env = unwrap(payload, _SOURCE_METADATA)
    body = env.body
    if not isinstance(body, dict):
        return []
    race_id = (path_params or {}).get("raceID")
    if not race_id:
        return []
    body_json = {**body, "race_id": race_id}
    return [
        {
            "fact_type": "btd6.race_metadata",
            "entity_kind": "btd6_race",
            "entity_key": race_id,
            "body_json": body_json,
            "game_version": body.get("gameVersion") or game_version,
        },
    ]


def parse_race_leaderboard(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse one page of race-leaderboard rows.

    ``entity_key`` is composed as ``"<raceID>_rank_<n>"`` using the
    1-based row index (the API returns rows in score order). Ties
    still emit distinct entity_keys because each occupies a different
    position in the page. Profile URLs are stored verbatim — never
    auto-expanded.
    """
    env = unwrap(payload, _SOURCE_LEADERBOARD)
    body = env.body
    if not isinstance(body, list):
        return []
    race_id = (path_params or {}).get("raceID")
    if not race_id:
        return []
    facts: list[dict[str, Any]] = []
    for rank, row in enumerate(body, start=1):
        if not isinstance(row, dict):
            continue
        facts.append(
            {
                "fact_type": "btd6.race_leaderboard",
                "entity_kind": "btd6_race_leaderboard_row",
                "entity_key": f"{race_id}_rank_{rank}",
                "body_json": {
                    "race_id": race_id,
                    "rank": rank,
                    "display_name": row.get("displayName"),
                    "score": row.get("score"),
                    "score_parts": row.get("scoreParts"),
                    "submission_time_ms": row.get("submissionTime"),
                    "profile_url": row.get("profile"),
                },
                "game_version": game_version,
            },
        )
    return facts


btd6_source_parser.register(ParserAdapter(_SOURCE_INDEX, parse_races_index))
btd6_source_parser.register(ParserAdapter(_SOURCE_METADATA, parse_race_metadata))
btd6_source_parser.register(ParserAdapter(_SOURCE_LEADERBOARD, parse_race_leaderboard))


__all__ = [
    "parse_race_leaderboard",
    "parse_race_metadata",
    "parse_races_index",
]
