"""Ninja Kiwi /btd6/odyssey parsers (M3B).

Three parsers share this module:

* :func:`parse_odyssey_index` — ``/btd6/odyssey`` (model
  ``_btd6odyssey``): the directory of odyssey events with per-
  difficulty metadata URLs (metadata_easy / _medium / _hard).
* :func:`parse_odyssey_metadata` — ``/btd6/odyssey/<id>/<difficulty>``
  (model ``_btd6odysseymetadata``): boat capacity, starting health,
  available towers/powers, rewards. Body's ``id`` is the odyssey id
  but does not include difficulty; the parser composites
  ``<odysseyID>_<difficulty>`` using ``path_params``.
* :func:`parse_odyssey_maps` — ``/btd6/odyssey/<id>/<difficulty>/maps``
  (model ``_btd6challengedocument``): per-stage map documents. Body
  is a list; each stage has ``id="n/a"`` so the parser composites a
  stage-indexed key using path_params + 1-based stage index.
"""

from __future__ import annotations

from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter, unwrap

_SOURCE_INDEX = "nk_btd6_odyssey"
_SOURCE_METADATA = "nk_btd6_odyssey_diff"
_SOURCE_MAPS = "nk_btd6_odyssey_diff_maps"


def parse_odyssey_index(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — body carries id
) -> list[dict[str, Any]]:
    """Parse ``/btd6/odyssey`` into one fact per odyssey event."""
    env = unwrap(payload, _SOURCE_INDEX)
    body = env.body
    if not isinstance(body, list):
        return []
    facts: list[dict[str, Any]] = []
    for entry in body:
        if not isinstance(entry, dict):
            continue
        odyssey_id = entry.get("id")
        if not isinstance(odyssey_id, str) or not odyssey_id:
            continue
        facts.append(
            {
                "fact_type": "btd6.odyssey_index",
                "entity_kind": "btd6_odyssey",
                "entity_key": odyssey_id,
                "body_json": {
                    "id": odyssey_id,
                    "name": entry.get("name"),
                    "description": entry.get("description"),
                    "start_ms": entry.get("start"),
                    "end_ms": entry.get("end"),
                    "metadata_easy_url": entry.get("metadata_easy"),
                    "metadata_medium_url": entry.get("metadata_medium"),
                    "metadata_hard_url": entry.get("metadata_hard"),
                },
                "game_version": game_version,
            },
        )
    return facts


def parse_odyssey_metadata(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse one ``/btd6/odyssey/<id>/<difficulty>`` metadata document.

    Body returns the odyssey id but no difficulty marker, so the
    parser needs ``path_params["difficulty"]`` to compose a unique
    entity_key. ``isExtreme`` is preserved verbatim; ``_availableTowers``
    keeps its per-tower max + isHero structure for downstream filtering.
    """
    env = unwrap(payload, _SOURCE_METADATA)
    body = env.body
    if not isinstance(body, dict):
        return []
    odyssey_id = body.get("id") or (path_params or {}).get("odysseyID")
    difficulty = (path_params or {}).get("difficulty")
    if not odyssey_id or not difficulty:
        return []
    entity_key = f"{odyssey_id}_{difficulty}"
    body_json = {
        **body,
        "odyssey_id": odyssey_id,
        "difficulty": difficulty,
    }
    return [
        {
            "fact_type": "btd6.odyssey_metadata",
            "entity_kind": "btd6_odyssey_difficulty",
            "entity_key": entity_key,
            "body_json": body_json,
            "game_version": game_version,
        },
    ]


def parse_odyssey_maps(
    payload: Any,
    *,
    game_version: str | None = None,
    path_params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse ``/btd6/odyssey/<id>/<difficulty>/maps`` into stage facts.

    Body is a list of challenge documents; each stage has
    ``id="n/a"`` and ``createdAt=0``. ``entity_key`` is composed as
    ``"<odysseyID>_<difficulty>_stage_<n>"`` where n is the 1-based
    position in the list. ``_towers`` is ``null`` for these stages
    (towers are governed by the parent metadata document).
    """
    env = unwrap(payload, _SOURCE_MAPS)
    body = env.body
    if not isinstance(body, list):
        return []
    odyssey_id = (path_params or {}).get("odysseyID")
    difficulty = (path_params or {}).get("difficulty")
    if not odyssey_id or not difficulty:
        return []
    facts: list[dict[str, Any]] = []
    for stage_index, stage in enumerate(body, start=1):
        if not isinstance(stage, dict):
            continue
        entity_key = f"{odyssey_id}_{difficulty}_stage_{stage_index}"
        body_json = {
            **stage,
            "odyssey_id": odyssey_id,
            "difficulty": difficulty,
            "stage_index": stage_index,
        }
        facts.append(
            {
                "fact_type": "btd6.odyssey_maps",
                "entity_kind": "btd6_odyssey_stage",
                "entity_key": entity_key,
                "body_json": body_json,
                "game_version": game_version,
            },
        )
    return facts


btd6_source_parser.register(ParserAdapter(_SOURCE_INDEX, parse_odyssey_index))
btd6_source_parser.register(ParserAdapter(_SOURCE_METADATA, parse_odyssey_metadata))
btd6_source_parser.register(ParserAdapter(_SOURCE_MAPS, parse_odyssey_maps))


__all__ = [
    "parse_odyssey_index",
    "parse_odyssey_maps",
    "parse_odyssey_metadata",
]
