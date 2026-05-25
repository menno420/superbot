"""Writer + grounded reader for ``btd6_facts``.

Parsers and the M3B fetch loop call :func:`store_fact` /
:func:`store_facts`; nothing else may write to the table. The
``test_no_ai_factual_writes`` pin (M4) asserts no AI code path
reaches this module directly.

PR3 adds :func:`fetch_for_intent`: a deterministic batched read used
by :mod:`services.btd6_context_service` to surface trusted facts to
the AI gateway. Read paths are independent of the write surface — AI
code may call ``fetch_for_intent`` freely.
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


@dataclass(frozen=True)
class BTD6FactQuery:
    """One bucket of facts to look up.

    ``fact_type`` may be ``None`` to match any fact_type for the
    given ``(entity_kind, entity_key)`` pair — useful when the caller
    has a resolved entity but doesn't yet know which fact_type carries
    the answer.
    """

    fact_type: str | None
    entity_kind: str
    entity_key: str


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
    either ``source_id`` or rely on ``default_source_id``.
    """
    results: list[FactWriteResult] = []
    for raw in facts:
        source_id = raw.get("source_id", default_source_id)
        if source_id is None:
            raise ValueError("fact missing source_id and no default supplied")
        results.append(
            await store_fact(
                source_id=int(source_id),
                fact_type=str(raw["fact_type"]),
                entity_kind=str(raw["entity_kind"]),
                entity_key=str(raw["entity_key"]),
                body_json=raw.get("body_json") or {},
                game_version=raw.get("game_version"),
                confidence=float(raw.get("confidence", 1.0)),
                version=int(raw.get("version", 1)),
            ),
        )
    return results


async def fetch_for_intent(
    queries: list[BTD6FactQuery],
    *,
    per_fact_type_limit: int = 5,
    overall_limit: int = 20,
) -> list[dict[str, Any]]:
    """Read-only batch lookup with deterministic ordering and capping.

    The DB primitive returns rows ordered by ``trust_tier ASC,
    fetched_at DESC, version DESC`` so Tier-1 (official_api) facts win
    over Tier-2 (patch_notes / webpage). After the join, this service
    enforces a per-fact_type cap so one noisy endpoint (e.g. a
    leaderboard with 50 rank rows) cannot crowd out tower-metadata
    facts in the same context. Returns at most ``overall_limit`` rows.

    Empty input → empty output (cheap fast path). Conflicting facts
    are NOT silently reconciled here: callers receive every row that
    matched, in deterministic order, with ``source_name``,
    ``trust_tier``, ``fetched_at``, and ``version`` attached so
    downstream rendering can surface provenance.
    """
    if not queries:
        return []
    # Over-fetch so per-fact_type capping has headroom to skip excess
    # rows from one bucket and still hit overall_limit across buckets.
    raw_rows = await btd6_db.fetch_facts_for_intent(
        [(q.fact_type, q.entity_kind, q.entity_key) for q in queries],
        overall_limit=overall_limit * 4,
    )
    counts: dict[str, int] = {}
    capped: list[dict[str, Any]] = []
    for row in raw_rows:
        fact_type = row["fact_type"]
        if counts.get(fact_type, 0) >= per_fact_type_limit:
            continue
        counts[fact_type] = counts.get(fact_type, 0) + 1
        capped.append(row)
        if len(capped) >= overall_limit:
            break
    return capped


__all__ = [
    "BTD6FactQuery",
    "FactWriteResult",
    "fetch_for_intent",
    "store_fact",
    "store_facts",
]
