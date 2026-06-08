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
from datetime import datetime
from typing import Any

from services.btd6_source_registry import FreshnessBucket, bucket_freshness
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


@dataclass(frozen=True)
class DataProvenance:
    """Provenance label attached to every live BTD6 fact.

    Assembled from a joined fact row via :func:`extract_provenance`.
    See ``docs/btd6/btd6-provenance-schema.md`` for the full contract.
    """

    source_id: int
    source_key: str
    source_name: str
    source_kind: str
    trust_tier: int
    fetched_at: datetime
    game_version: str | None
    freshness: FreshnessBucket

    @property
    def is_official(self) -> bool:
        return self.trust_tier == 1

    @property
    def label(self) -> str:
        return f"{self.source_name} (tier {self.trust_tier}, {self.freshness})"


def extract_provenance(row: dict[str, Any]) -> DataProvenance:
    """Assemble a :class:`DataProvenance` from a joined fact row.

    Expects the shape returned by
    ``btd6_db.fetch_facts_for_intent`` — i.e. the fact columns plus
    ``source_id``, ``source_key``, ``source_name``, ``source_kind``,
    ``trust_tier`` joined from ``btd6_source_registry``.
    """
    fetched_at: datetime = row["fetched_at"]
    if fetched_at is None:
        raise TypeError(
            "fact row missing fetched_at — column is NOT NULL in btd6_facts",
        )
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at)
    return DataProvenance(
        source_id=int(row["source_id"]),
        source_key=row.get("source_key") or "",
        source_name=row.get("source_name") or "",
        source_kind=row.get("source_kind") or "",
        trust_tier=int(row.get("trust_tier") or 2),
        fetched_at=fetched_at,
        game_version=row.get("game_version"),
        freshness=bucket_freshness(fetched_at),
    )


@dataclass(frozen=True)
class FactRow:
    """Typed wrapper for a fact row with provenance attached.

    Use :meth:`from_row` to lift a raw dict from
    :func:`fetch_for_intent`.  New extraction code should work with
    ``FactRow`` rather than raw dicts.
    """

    fact_id: int
    fact_type: str
    entity_kind: str
    entity_key: str
    body_json: dict[str, Any]
    confidence: float
    version: int
    provenance: DataProvenance

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> FactRow:
        return cls(
            fact_id=int(row["id"]),
            fact_type=row["fact_type"],
            entity_kind=row["entity_kind"],
            entity_key=row["entity_key"],
            body_json=row.get("body_json") or {},
            confidence=float(row.get("confidence") or 1.0),
            version=int(row.get("version") or 1),
            provenance=extract_provenance(row),
        )


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
    "DataProvenance",
    "FactRow",
    "FactWriteResult",
    "extract_provenance",
    "fetch_for_intent",
    "store_fact",
    "store_facts",
]
