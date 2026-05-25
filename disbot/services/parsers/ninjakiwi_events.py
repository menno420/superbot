"""Ninja Kiwi /btd6/events parser (M3B).

Single parser; the events index is a flat directory of all active and
recent events with no per-id detail endpoint. Detail endpoints live
under /btd6/races, /btd6/bosses, /btd6/odyssey, /btd6/ct — those have
their own domain modules.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

_SOURCE = "nk_btd6_events"

# Event types observed in capture; the parser does not enforce this set
# (Ninja Kiwi may add new types) — it's documented here for grep / docs.
_KNOWN_EVENT_TYPES = (
    "bossRush",
    "ct",
    "bossBloon",
    "raceEvent",
    "odysseyEvent",
    "collectableEvent",
    "socialseason",
)


def parse_events_index(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse ``/btd6/events`` into one fact per event entry.

    ``url`` may be null (events without external links — bossRush, ct,
    collectableEvent, socialseason in current captures). The parser
    keeps the URL verbatim — never followed by the parser itself.
    """
    env = unwrap(payload, _SOURCE)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        event_id = entry.get("id")
        if not isinstance(event_id, str) or not event_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.events_index",
                "entity_kind": "btd6_event",
                "entity_key": event_id,
                "body_json": {
                    "id": event_id,
                    "type": entry.get("type"),
                    "name": entry.get("name"),
                    "start_ms": entry.get("start"),
                    "end_ms": entry.get("end"),
                    "url": entry.get("url"),
                },
                "game_version": game_version,
            },
        )
    return facts


btd6_source_parser.register(ParserAdapter(_SOURCE, parse_events_index))


__all__ = ["parse_events_index"]
