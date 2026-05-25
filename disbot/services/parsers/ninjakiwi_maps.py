"""Ninja Kiwi /btd6/maps parsers (M3B).

Three parsers share this module by domain:

* :func:`parse_map_filters` — ``/btd6/maps`` (model ``_btd6maptype``):
  the filter directory (newest / trending / mostLiked).
* :func:`parse_map_list` — ``/btd6/maps/filter/<filter>``
  (model ``_btd6map``): user maps that match a filter, paged.
* :func:`parse_map_metadata` — ``/btd6/maps/map/<mapID>``
  (model ``_btd6mapdocument``): full single-map document.

Each parse function returns a list of fact dicts ready for
:func:`services.btd6_fact_store.store_facts`. Epoch milliseconds are
preserved raw (``created_at_ms``); conversion to ``datetime`` happens
at render time. All string fields come from untrusted input and stay
unparsed — no recursive expansion of ``creator`` URLs, no following of
``mapURL`` to download assets.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

# Source keys served by this module — declared up top so the registry
# call near the bottom of the file stays readable.
_SOURCE_FILTERS = "nk_btd6_maps"
_SOURCE_LIST = "nk_btd6_maps_filter"
_SOURCE_METADATA = "nk_btd6_maps_one"


def parse_map_filters(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse the ``/btd6/maps`` filter directory into fact rows.

    One fact per filter entry. ``entity_key`` is the filter name
    (``newest`` / ``trending`` / ``mostLiked``); ``maps_url`` is kept
    verbatim so callers can follow it via the registered list endpoint
    rather than a raw HTTP call.
    """
    env = unwrap(payload, _SOURCE_FILTERS)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        filter_type = entry.get("type")
        if not isinstance(filter_type, str) or not filter_type:
            continue
        facts.append(
            {
                "fact_type": "btd6.map_filter_index",
                "entity_kind": "btd6_map_filter",
                "entity_key": filter_type,
                "body_json": {
                    "filter_type": filter_type,
                    "maps_url": entry.get("maps"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_map_list(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse a ``/btd6/maps/filter/<filter>`` page into fact rows.

    One fact per map entry. ``entity_key`` is the map id; the filter
    that produced the row is recorded in ``btd6_source_snapshots`` by
    the fetcher, not in the fact body. ``next``/``prev`` URLs from the
    envelope are not auto-followed (PR2 is page-1-only).
    """
    env = unwrap(payload, _SOURCE_LIST)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        map_id = entry.get("id")
        if not isinstance(map_id, str) or not map_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.map_list",
                "entity_kind": "btd6_map",
                "entity_key": map_id,
                "body_json": {
                    "name": entry.get("name"),
                    "created_at_ms": entry.get("createdAt"),
                    "id": map_id,
                    "creator_url": entry.get("creator"),
                    "metadata_url": entry.get("metadata"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_map_metadata(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse a ``/btd6/maps/map/<mapID>`` document into one fact row.

    Body is a single object. The body's ``gameVersion`` is preferred
    over the function parameter; play counters may be zero for fresh
    maps. ``mapURL`` is stored as a URL string — assets are never
    downloaded by the parser.
    """
    env = unwrap(payload, _SOURCE_METADATA)
    body = env.body
    if not isinstance(body, dict):
        return []
    map_id = body.get("id")
    if not isinstance(map_id, str) or not map_id:
        return []
    body_game_version = body.get("gameVersion") or game_version
    return [
        {
            "fact_type": "btd6.map_metadata",
            "entity_kind": "btd6_map",
            "entity_key": map_id,
            "body_json": {
                "name": body.get("name"),
                "created_at_ms": body.get("createdAt"),
                "id": map_id,
                "creator_url": body.get("creator"),
                "game_version": body.get("gameVersion"),
                "map": body.get("map"),
                "map_url": body.get("mapURL"),
                "stats": {
                    "plays": body.get("plays"),
                    "wins": body.get("wins"),
                    "restarts": body.get("restarts"),
                    "losses": body.get("losses"),
                    "upvotes": body.get("upvotes"),
                    "plays_unique": body.get("playsUnique"),
                    "wins_unique": body.get("winsUnique"),
                    "losses_unique": body.get("lossesUnique"),
                },
            },
            "game_version": body_game_version,
        },
    ]


btd6_source_parser.register(ParserAdapter(_SOURCE_FILTERS, parse_map_filters))
btd6_source_parser.register(ParserAdapter(_SOURCE_LIST, parse_map_list))
btd6_source_parser.register(ParserAdapter(_SOURCE_METADATA, parse_map_metadata))


__all__ = [
    "parse_map_filters",
    "parse_map_list",
    "parse_map_metadata",
]
