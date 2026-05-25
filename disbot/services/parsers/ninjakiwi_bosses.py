"""Ninja Kiwi /btd6/bosses parsers (M3B).

Three parsers share this module:

* :func:`parse_bosses_index` — ``/btd6/bosses`` (model ``_btd6boss``):
  the directory of boss events with separate standard / elite scoring
  types and leaderboard URLs. The legacy ``scoringType`` field is
  preserved alongside ``normalScoringType`` / ``eliteScoringType``;
  consumers should prefer the latter pair.
* :func:`parse_boss_metadata` —
  ``/btd6/bosses/<bossID>/metadata/<difficulty>`` (model
  ``_btd6challengedocument``): boss-event rules. Body has
  ``id="n/a"`` so ``path_params["bossID"]`` + ``["difficulty"]`` are
  required to compose a stable entity_key.
* :func:`parse_boss_leaderboard` —
  ``/btd6/bosses/<bossID>/leaderboard/<type>/<teamSize>`` (model
  ``_btd6bossleaderboard``): per-rank score rows with mixed
  number / time scoreParts (Boss Tier number + Least Cash number +
  Game Time). Page 1 only.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

_SOURCE_INDEX = "nk_btd6_bosses"
_SOURCE_METADATA = "nk_btd6_bosses_metadata"
_SOURCE_LEADERBOARD = "nk_btd6_bosses_leaderboard"


def parse_bosses_index(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse ``/btd6/bosses`` into one fact per boss event."""
    env = unwrap(payload, _SOURCE_INDEX)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        boss_id = entry.get("id")
        if not isinstance(boss_id, str) or not boss_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.bosses_index",
                "entity_kind": "btd6_boss",
                "entity_key": boss_id,
                "body_json": {
                    "id": boss_id,
                    "name": entry.get("name"),
                    "boss_type": entry.get("bossType"),
                    "boss_type_url": entry.get("bossTypeURL"),
                    "start_ms": entry.get("start"),
                    "end_ms": entry.get("end"),
                    "total_scores_standard": entry.get("totalScores_standard"),
                    "total_scores_elite": entry.get("totalScores_elite"),
                    # scoringType is deprecated; consumers should prefer
                    # normalScoringType / eliteScoringType. Kept verbatim.
                    "scoring_type_deprecated": entry.get("scoringType"),
                    "normal_scoring_type": entry.get("normalScoringType"),
                    "elite_scoring_type": entry.get("eliteScoringType"),
                    "leaderboard_standard_players_1_url":
                        entry.get("leaderboard_standard_players_1"),
                    "leaderboard_elite_players_1_url":
                        entry.get("leaderboard_elite_players_1"),
                    "metadata_standard_url": entry.get("metadataStandard"),
                    "metadata_elite_url": entry.get("metadataElite"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_boss_metadata(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse a boss-event metadata document.

    Body's ``id`` is ``"n/a"`` and ``createdAt=0``; the real id comes
    from ``path_params["bossID"]`` and difficulty from
    ``path_params["difficulty"]``. The body's own ``id`` is preserved
    for completeness.
    """
    env = unwrap(payload, _SOURCE_METADATA)
    body = env.body
    if not isinstance(body, dict):
        return []
    boss_id = (path_params or {}).get("bossID")
    difficulty = (path_params or {}).get("difficulty")
    if not boss_id or not difficulty:
        return []
    entity_key = f"{boss_id}_{difficulty}"
    body_json = {
        **body,
        "boss_id": boss_id,
        "difficulty": difficulty,
    }
    return [
        {
            "fact_type": "btd6.boss_metadata",
            "entity_kind": "btd6_boss_difficulty",
            "entity_key": entity_key,
            "body_json": body_json,
            "game_version": body.get("gameVersion") or game_version,
        },
    ]


def parse_boss_leaderboard(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse one page of boss leaderboard rows.

    ``entity_key`` is composed as
    ``"<bossID>_<type>_<teamSize>_rank_<n>"`` where n is the 1-based
    row index. ``scoreParts`` is preserved verbatim so consumers can
    surface mixed number / time components.
    """
    env = unwrap(payload, _SOURCE_LEADERBOARD)
    body = env.body
    if not isinstance(body, list):
        return []
    boss_id = (path_params or {}).get("bossID")
    type_ = (path_params or {}).get("type")
    team_size = (path_params or {}).get("teamSize")
    if not boss_id or not type_ or not team_size:
        return []
    facts: list[dict[str, Any]] = []
    for rank, row in enumerate(body, start=1):
        if not isinstance(row, dict):
            continue
        facts.append(
            {
                "fact_type": "btd6.boss_leaderboard",
                "entity_kind": "btd6_boss_leaderboard_row",
                "entity_key": f"{boss_id}_{type_}_{team_size}_rank_{rank}",
                "body_json": {
                    "boss_id": boss_id,
                    "type": type_,
                    "team_size": team_size,
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


btd6_source_parser.register(ParserAdapter(_SOURCE_INDEX, parse_bosses_index))
btd6_source_parser.register(ParserAdapter(_SOURCE_METADATA, parse_boss_metadata))
btd6_source_parser.register(ParserAdapter(_SOURCE_LEADERBOARD, parse_boss_leaderboard))


__all__ = [
    "parse_boss_leaderboard",
    "parse_boss_metadata",
    "parse_bosses_index",
]
