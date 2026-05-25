"""Ninja Kiwi /btd6/challenges parsers (M3B).

Three parsers share this module:

* :func:`parse_challenge_filters` — ``/btd6/challenges``
  (model ``_btd6challengetype``): filter directory (newest /
  trending / daily).
* :func:`parse_challenge_list` — ``/btd6/challenges/filter/<filter>``
  (model ``_btd6challenge``): user/auto challenges matching the
  filter. ``creator`` is nullable. The filter context is recorded by
  the fetcher snapshot, not in the fact body.
* :func:`parse_challenge_metadata` —
  ``/btd6/challenges/challenge/<challengeID>``
  (model ``_btd6challengedocument``): full single-challenge document.
  Unlike race / boss / odyssey-maps metadata, the body's ``id`` IS
  the real challenge id; the parser uses it directly.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

_SOURCE_FILTERS = "nk_btd6_challenges"
_SOURCE_LIST = "nk_btd6_challenges_filter"
_SOURCE_METADATA = "nk_btd6_challenges_one"


def parse_challenge_filters(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse the challenge filter directory into fact rows."""
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
                "fact_type": "btd6.challenge_filter_index",
                "entity_kind": "btd6_challenge_filter",
                "entity_key": filter_type,
                "body_json": {
                    "filter_type": filter_type,
                    "challenges_url": entry.get("challenges"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_challenge_list(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse one ``/btd6/challenges/filter/<filter>`` page.

    Each entry has nullable ``creator``. ``entity_key`` is the
    challenge id; the filter that produced the row is recorded in
    ``btd6_source_snapshots`` by the fetcher.
    """
    env = unwrap(payload, _SOURCE_LIST)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        challenge_id = entry.get("id")
        if not isinstance(challenge_id, str) or not challenge_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.challenge_list",
                "entity_kind": "btd6_challenge",
                "entity_key": challenge_id,
                "body_json": {
                    "id": challenge_id,
                    "name": entry.get("name"),
                    "created_at_ms": entry.get("createdAt"),
                    "creator_url": entry.get("creator"),
                    "metadata_url": entry.get("metadata"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_challenge_metadata(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse a single challenge metadata document.

    Body's ``id`` IS the real challenge id; ``path_params["challengeID"]``
    is used as a fallback if the body unexpectedly returns ``"n/a"``
    (defensive — current daily captures carry the real id).
    """
    env = unwrap(payload, _SOURCE_METADATA)
    body = env.body
    if not isinstance(body, dict):
        return []
    body_id = body.get("id")
    if not isinstance(body_id, str) or not body_id or body_id == "n/a":
        body_id = (path_params or {}).get("challengeID")
    if not body_id:
        return []
    body_json = {**body, "challenge_id": body_id}
    return [
        {
            "fact_type": "btd6.challenge_metadata",
            "entity_kind": "btd6_challenge",
            "entity_key": body_id,
            "body_json": body_json,
            "game_version": body.get("gameVersion") or game_version,
        },
    ]


btd6_source_parser.register(ParserAdapter(_SOURCE_FILTERS, parse_challenge_filters))
btd6_source_parser.register(ParserAdapter(_SOURCE_LIST, parse_challenge_list))
btd6_source_parser.register(ParserAdapter(_SOURCE_METADATA, parse_challenge_metadata))


__all__ = [
    "parse_challenge_filters",
    "parse_challenge_list",
    "parse_challenge_metadata",
]
