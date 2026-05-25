"""Ninja Kiwi /btd6/ct parsers (M3B, new module).

Two parsers share this module:

* :func:`parse_ct_index` — ``/btd6/ct`` (model ``_btd6ct``): the
  directory of Contested Territory events with their tiles and
  leaderboard URLs (player and team).
* :func:`parse_ct_tiles` — ``/btd6/ct/<ctID>/tiles`` (model
  ``_btd6cttile``): per-tile attributes for one CT event. Tile type
  strings of the form ``"Relic - <name>"`` are split into a normalised
  ``type="Relic"`` field with a separate ``relic_name`` so downstream
  filtering can match on either.

CT leaderboards (player / team / group) are intentionally NOT parsed
here — their parser scope is not approved in PR2 (no fixtures
captured). The corresponding registry rows stay disabled.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

_SOURCE_INDEX = "nk_btd6_ct"
_SOURCE_TILES = "nk_btd6_ct_tiles"

_RELIC_PREFIX = "Relic - "


def parse_ct_index(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse ``/btd6/ct`` into one fact per CT event.

    Each event keeps its tiles / leaderboard_player / leaderboard_team
    URLs verbatim — the parser does not follow them.
    """
    env = unwrap(payload, _SOURCE_INDEX)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        ct_id = entry.get("id")
        if not isinstance(ct_id, str) or not ct_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.ct_index",
                "entity_kind": "btd6_ct",
                "entity_key": ct_id,
                "body_json": {
                    "id": ct_id,
                    "start_ms": entry.get("start"),
                    "end_ms": entry.get("end"),
                    "total_scores_player": entry.get("totalScores_player"),
                    "total_scores_team": entry.get("totalScores_team"),
                    "tiles_url": entry.get("tiles"),
                    "leaderboard_player_url": entry.get("leaderboard_player"),
                    "leaderboard_team_url": entry.get("leaderboard_team"),
                },
                "game_version": game_version,
            },
        )
    return facts


def _split_tile_type(raw: Any) -> tuple[str | None, str | None]:
    """Split a tile type string into ``(type, relic_name)``.

    ``"Relic - Abilitized"`` → ``("Relic", "Abilitized")``.
    ``"Banner"`` → ``("Banner", None)``. Non-strings → ``(None, None)``.
    """
    if not isinstance(raw, str):
        return None, None
    if raw.startswith(_RELIC_PREFIX):
        return "Relic", raw[len(_RELIC_PREFIX):].strip() or None
    return raw, None


def parse_ct_tiles(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse ``/btd6/ct/<ctID>/tiles`` into one fact per tile.

    ``entity_key`` is composed as ``"<ctID>_tile_<tileID>"`` so the
    same tile coordinate can repeat across different CT events without
    collision. ``type`` is normalised: any ``"Relic - <name>"`` string
    becomes ``type="Relic"`` plus ``relic_name="<name>"``. Other
    types (Regular, Banner, TeamStart, TeamFirstCapture) carry
    ``relic_name=None``.
    """
    env = unwrap(payload, _SOURCE_TILES)
    body = env.body
    if not isinstance(body, dict):
        return []
    ct_id = body.get("id") or (path_params or {}).get("ctID")
    if not isinstance(ct_id, str) or not ct_id:
        return []
    tiles = body.get("tiles")
    if not isinstance(tiles, list):
        return []
    facts: list[dict[str, Any]] = []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        tile_id = tile.get("id")
        if not isinstance(tile_id, str) or not tile_id:
            continue
        tile_type, relic_name = _split_tile_type(tile.get("type"))
        facts.append(
            {
                "fact_type": "btd6.ct_tiles",
                "entity_kind": "btd6_ct_tile",
                "entity_key": f"{ct_id}_tile_{tile_id}",
                "body_json": {
                    "ct_id": ct_id,
                    "tile_id": tile_id,
                    "type": tile_type,
                    "relic_name": relic_name,
                    "game_type": tile.get("gameType"),
                },
                "game_version": game_version,
            },
        )
    return facts


btd6_source_parser.register(ParserAdapter(_SOURCE_INDEX, parse_ct_index))
btd6_source_parser.register(ParserAdapter(_SOURCE_TILES, parse_ct_tiles))


__all__ = ["parse_ct_index", "parse_ct_tiles"]
