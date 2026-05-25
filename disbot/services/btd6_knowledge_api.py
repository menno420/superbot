"""Stable BTD6 read interface for the AI surface (M3A).

Callers (``services.btd6_ai_service``, the BTD6 cog, future M4
strategy reviews) read facts through this module instead of
poking the DB or fixture provider directly. When ``btd6_facts``
is empty (M3A default), :class:`BTD6KnowledgeAPI` falls back to
the existing deterministic fixtures so the cog keeps responding
end-to-end. M3B populates the DB and the fixture path becomes the
outage fallback.

Returned :class:`FactBundle` always carries source / freshness /
confidence metadata so the AI surface can cite responsibly.
"""

from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass
from typing import Any

from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_knowledge_api")


@dataclass(frozen=True)
class FactBundle:
    """One fact + its provenance."""

    fact_type: str
    entity_kind: str
    entity_key: str
    body: dict[str, Any]
    source_key: str | None
    source_trust_tier: int | None
    source_url: str | None
    game_version: str | None
    fetched_at: _dt.datetime | None
    validated_at: _dt.datetime | None
    freshness_status: str  # 'fresh' | 'stale' | 'unknown' | 'fixture_fallback'
    confidence: float


_FIXTURE_STATUS = "fixture_fallback"


# ---------------------------------------------------------------------------
# Public read API
# ---------------------------------------------------------------------------


async def get_tower(name: str) -> FactBundle | None:
    return await _resolve("tower", "tower", name)


async def get_upgrade(name: str) -> FactBundle | None:
    return await _resolve("upgrade", "upgrade", name)


async def get_hero(name: str) -> FactBundle | None:
    return await _resolve("hero", "hero", name)


async def get_map(name: str) -> FactBundle | None:
    return await _resolve("map", "map", name)


async def get_mode(name: str) -> FactBundle | None:
    return await _resolve("mode", "mode", name)


async def get_round(round_id: int) -> FactBundle | None:
    return await _resolve("round", "round", str(int(round_id)))


async def get_patch_notes() -> FactBundle | None:
    from services import btd6_patch_service

    note = await btd6_patch_service.latest()
    if note is None:
        return None
    return FactBundle(
        fact_type="patch",
        entity_kind="patch_note",
        entity_key=str(note.get("version", "")),
        body={
            "version": note.get("version"),
            "published_at": note.get("published_at"),
            "body": note.get("body"),
        },
        source_key=None,
        source_trust_tier=None,
        source_url=None,
        game_version=str(note.get("version", "")) or None,
        fetched_at=note.get("published_at"),
        validated_at=None,
        freshness_status="fresh" if note.get("published_at") else "unknown",
        confidence=1.0,
    )


async def get_sources() -> list[dict[str, Any]]:
    """Return the source registry rows as plain dicts."""
    from services import btd6_source_registry

    return await btd6_source_registry.list_all()


async def search_facts(
    *,
    fact_type: str | None = None,
    entity_kind: str | None = None,
    limit: int = 25,
) -> list[FactBundle]:
    rows = await btd6_db.search_facts(
        fact_type=fact_type,
        entity_kind=entity_kind,
        limit=limit,
    )
    out: list[FactBundle] = []
    for row in rows:
        source = await btd6_db.get_source(int(row["source_id"]))
        out.append(_bundle_from_row(row, source))
    return out


async def compare_entities(
    fact_type: str,
    entity_kind: str,
    keys: list[str],
) -> list[FactBundle]:
    """Return one FactBundle per key (in order); missing keys are skipped."""
    out: list[FactBundle] = []
    for key in keys:
        bundle = await _resolve(fact_type, entity_kind, key)
        if bundle is not None:
            out.append(bundle)
    return out


# ---------------------------------------------------------------------------
# Resolution + fallback
# ---------------------------------------------------------------------------


async def _resolve(
    fact_type: str,
    entity_kind: str,
    entity_key: str,
) -> FactBundle | None:
    try:
        row = await btd6_db.get_latest_fact(fact_type, entity_kind, entity_key)
    except Exception as exc:  # noqa: BLE001 — fallback path
        logger.debug(
            "btd6_knowledge_api: DB lookup failed for %s/%s/%s (%s); "
            "falling back to fixtures",
            fact_type,
            entity_kind,
            entity_key,
            exc,
        )
        row = None

    if row is not None:
        source = await btd6_db.get_source(int(row["source_id"]))
        return _bundle_from_row(row, source)

    return await _fixture_fallback(fact_type, entity_kind, entity_key)


def _bundle_from_row(
    row: dict[str, Any],
    source: dict[str, Any] | None,
) -> FactBundle:
    fetched_at = row.get("fetched_at")
    freshness = "fresh"
    if isinstance(fetched_at, _dt.datetime):
        now = _dt.datetime.now(_dt.timezone.utc)
        # If the row came back without tzinfo, treat it as UTC — the
        # DB layer always writes ``NOW()`` which Postgres returns as
        # an aware timestamp, so naive values are an artefact of the
        # test stub rather than a meaningful local time.
        age = now - (
            fetched_at
            if fetched_at.tzinfo
            else fetched_at.replace(tzinfo=_dt.timezone.utc)
        )
        if age.total_seconds() > 7 * 24 * 3600:
            freshness = "stale"
    elif fetched_at is None:
        freshness = "unknown"
    return FactBundle(
        fact_type=str(row["fact_type"]),
        entity_kind=str(row["entity_kind"]),
        entity_key=str(row["entity_key"]),
        body=dict(row.get("body_json") or {}),
        source_key=(source or {}).get("source_key"),
        source_trust_tier=(source or {}).get("trust_tier"),
        source_url=(source or {}).get("full_url") or (source or {}).get("base_url"),
        game_version=row.get("game_version"),
        fetched_at=row.get("fetched_at"),
        validated_at=row.get("validated_at"),
        freshness_status=freshness,
        confidence=float(row.get("confidence") or 1.0),
    )


async def _fixture_fallback(
    fact_type: str,
    entity_kind: str,
    entity_key: str,
) -> FactBundle | None:
    """Read from the existing deterministic fixture providers.

    M3A keeps the cog responsive while ``btd6_facts`` is empty. The
    fallback returns a :class:`FactBundle` with
    ``freshness_status='fixture_fallback'`` so downstream renderers
    can mark the answer as fixture-sourced.
    """
    try:
        from services import btd6_data_service
    except Exception as exc:  # noqa: BLE001
        logger.debug("btd6_knowledge_api: fixture module unavailable (%s)", exc)
        return None

    record: Any = None
    try:
        if entity_kind == "tower":
            record = btd6_data_service.get_tower(entity_key)
        elif entity_kind == "hero":
            record = btd6_data_service.get_hero(entity_key)
        elif entity_kind == "map":
            record = btd6_data_service.get_map(entity_key)
        elif entity_kind == "mode":
            record = btd6_data_service.get_mode(entity_key)
        elif entity_kind == "round":
            try:
                record = btd6_data_service.get_round(int(entity_key))
            except (TypeError, ValueError):
                record = None
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "btd6_knowledge_api: fixture lookup raised for %s/%s/%s: %s",
            fact_type,
            entity_kind,
            entity_key,
            exc,
        )
        record = None

    if record is None:
        return None

    if hasattr(record, "__dict__"):
        body = {k: v for k, v in vars(record).items() if not k.startswith("_")}
    elif isinstance(record, dict):
        body = dict(record)
    else:
        body = {"value": str(record)}

    return FactBundle(
        fact_type=fact_type,
        entity_kind=entity_kind,
        entity_key=entity_key,
        body=body,
        source_key="fixture",
        source_trust_tier=1,
        source_url=None,
        game_version=None,
        fetched_at=None,
        validated_at=None,
        freshness_status=_FIXTURE_STATUS,
        confidence=0.9,
    )


__all__ = [
    "FactBundle",
    "compare_entities",
    "get_hero",
    "get_map",
    "get_mode",
    "get_patch_notes",
    "get_round",
    "get_sources",
    "get_tower",
    "get_upgrade",
    "search_facts",
]
