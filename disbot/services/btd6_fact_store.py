"""Single writer for ``btd6_facts`` (M3A).

Parsers and the M3B fetch loop call :func:`store_fact` /
:func:`store_facts`; nothing else may write to the table. The
``test_no_ai_factual_writes`` pin (M4) asserts no AI code path
reaches this module directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_fact_store")


@dataclass(frozen=True)
class FactWriteResult:
    fact_id: int
    fact_type: str
    entity_kind: str
    entity_key: str
    version: int


async def store_fact(
    *,
    source_id: int,
    fact_type: str,
    entity_kind: str,
    entity_key: str,
    body_json: dict[str, Any],
    game_version: str | None = None,
    confidence: float = 1.0,
    version: int = 1,
) -> FactWriteResult:
    if not fact_type or not entity_kind or not entity_key:
        raise ValueError(
            "fact_type, entity_kind, and entity_key must be non-empty",
        )
    if not isinstance(body_json, dict):
        raise TypeError("body_json must be a dict")

    fact_id = await btd6_db.upsert_fact(
        source_id=source_id,
        fact_type=fact_type,
        entity_kind=entity_kind,
        entity_key=entity_key,
        body_json=body_json,
        game_version=game_version,
        confidence=confidence,
        version=version,
    )
    return FactWriteResult(
        fact_id=fact_id,
        fact_type=fact_type,
        entity_kind=entity_kind,
        entity_key=entity_key,
        version=version,
    )


async def store_facts(
    facts: list[dict[str, Any]],
    *,
    default_source_id: int | None = None,
) -> list[FactWriteResult]:
    """Bulk-write a list of fact dicts. Each dict must carry
    ``fact_type``, ``entity_kind``, ``entity_key``, ``body_json`` and
    either ``source_id`` or rely on ``default_source_id``."""
    results: list[FactWriteResult] = []
    for raw in facts:
        source_id = raw.get("source_id", default_source_id)
        if source_id is None:
            raise ValueError("fact missing source_id and no default supplied")
        results.append(await store_fact(
            source_id=int(source_id),
            fact_type=str(raw["fact_type"]),
            entity_kind=str(raw["entity_kind"]),
            entity_key=str(raw["entity_key"]),
            body_json=raw.get("body_json") or {},
            game_version=raw.get("game_version"),
            confidence=float(raw.get("confidence", 1.0)),
            version=int(raw.get("version", 1)),
        ))
    return results


__all__ = ["FactWriteResult", "store_fact", "store_facts"]
