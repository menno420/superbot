"""BTD6 source / fact / patch-notes DB primitives (M3A).

The only module that touches the BTD6 source schema. Writes flow
through :mod:`services.btd6_source_mutation` and
:mod:`services.btd6_fact_store`; reads route through the typed
``services.btd6_source_registry`` / ``services.btd6_knowledge_api``.

BTD6 facts are global (not guild-scoped) so there is no
``delete_for_guild`` hook.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.btd6_sources")


# ---------------------------------------------------------------------------
# btd6_source_registry
# ---------------------------------------------------------------------------


async def get_source_by_key(source_key: str) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT id, source_key, source_name, source_owner, source_kind,
               trust_tier, base_url, path_template, full_url,
               cache_policy_key, enabled, notes, created_at, created_by,
               updated_at, updated_by
        FROM btd6_source_registry
        WHERE source_key = $1
        """,
        source_key,
    )
    return dict(row) if row else None


async def get_source(source_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT id, source_key, source_name, source_owner, source_kind,
               trust_tier, base_url, path_template, full_url,
               cache_policy_key, enabled, notes
        FROM btd6_source_registry
        WHERE id = $1
        """,
        source_id,
    )
    return dict(row) if row else None


_LIST_SOURCES_MAX_LIMIT = 200


async def list_sources(
    *,
    trust_tier: int | None = None,
    enabled: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Bounded list of source registry rows.

    ``limit`` and ``offset`` are required to be sane integers. The hard
    cap is :data:`_LIST_SOURCES_MAX_LIMIT` so callers cannot accidentally
    request unbounded paging. Callers that need the full registry must
    page explicitly.
    """
    safe_limit = max(1, min(int(limit), _LIST_SOURCES_MAX_LIMIT))
    safe_offset = max(0, int(offset))
    sql = (
        "SELECT id, source_key, source_name, source_owner, source_kind, "
        "trust_tier, base_url, path_template, full_url, enabled, notes "
        "FROM btd6_source_registry"
    )
    args: list[Any] = []
    clauses: list[str] = []
    if trust_tier is not None:
        args.append(trust_tier)
        clauses.append(f"trust_tier = ${len(args)}")
    if enabled is not None:
        args.append(enabled)
        clauses.append(f"enabled = ${len(args)}")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    args.append(safe_limit)
    args.append(safe_offset)
    sql += (
        " ORDER BY trust_tier, source_key "
        f"LIMIT ${len(args) - 1} OFFSET ${len(args)}"
    )
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


async def list_sources_with_freshness(
    *,
    enabled: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Per-source freshness aggregate (PR-D).

    Joins ``btd6_source_registry`` with the latest
    ``btd6_facts.fetched_at`` per source. Returns each source row
    enriched with ``last_fetched_at`` (nullable) and ``fact_count``
    so callers can bucket freshness without a second query.

    Tier-1 sources with no facts (recently enabled but never
    fetched) appear with ``last_fetched_at = NULL`` and
    ``fact_count = 0``.
    """
    safe_limit = max(1, min(int(limit), _LIST_SOURCES_MAX_LIMIT))
    safe_offset = max(0, int(offset))
    sql = (
        "SELECT r.id, r.source_key, r.source_name, r.source_owner, "
        "r.source_kind, r.trust_tier, r.base_url, r.path_template, "
        "r.full_url, r.enabled, r.notes, "
        "facts.last_fetched_at, facts.fact_count "
        "FROM btd6_source_registry r "
        "LEFT JOIN ("
        "  SELECT source_id, "
        "         MAX(fetched_at) AS last_fetched_at, "
        "         COUNT(*) AS fact_count "
        "  FROM btd6_facts GROUP BY source_id"
        ") facts ON facts.source_id = r.id"
    )
    args: list[Any] = []
    if enabled is not None:
        args.append(enabled)
        sql += f" WHERE r.enabled = ${len(args)}"
    args.append(safe_limit)
    args.append(safe_offset)
    sql += (
        " ORDER BY r.trust_tier, r.source_key "
        f"LIMIT ${len(args) - 1} OFFSET ${len(args)}"
    )
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


async def upsert_source(
    *,
    source_key: str,
    source_name: str,
    source_owner: str,
    source_kind: str,
    trust_tier: int,
    base_url: str | None,
    path_template: str | None,
    full_url: str | None,
    cache_policy_key: str | None,
    enabled: bool,
    notes: str,
    updated_by: int | None,
) -> int:
    row = await pool.get().fetchrow(
        """
        INSERT INTO btd6_source_registry (
            source_key, source_name, source_owner, source_kind,
            trust_tier, base_url, path_template, full_url,
            cache_policy_key, enabled, notes, created_at, created_by,
            updated_at, updated_by
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
            NOW(), $12, NOW(), $12
        )
        ON CONFLICT (source_key) DO UPDATE SET
            source_name      = EXCLUDED.source_name,
            source_owner     = EXCLUDED.source_owner,
            source_kind      = EXCLUDED.source_kind,
            trust_tier       = EXCLUDED.trust_tier,
            base_url         = EXCLUDED.base_url,
            path_template    = EXCLUDED.path_template,
            full_url         = EXCLUDED.full_url,
            cache_policy_key = EXCLUDED.cache_policy_key,
            enabled          = EXCLUDED.enabled,
            notes            = EXCLUDED.notes,
            updated_at       = NOW(),
            updated_by       = EXCLUDED.updated_by
        RETURNING id
        """,
        source_key,
        source_name,
        source_owner,
        source_kind,
        trust_tier,
        base_url,
        path_template,
        full_url,
        cache_policy_key,
        enabled,
        notes,
        updated_by,
    )
    return int(row["id"])


# ---------------------------------------------------------------------------
# btd6_source_audit
# ---------------------------------------------------------------------------


async def record_source_audit(
    *,
    source_key: str,
    action: str,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    actor_id: int | None,
    guild_id: int | None,
    reason: str | None,
) -> int:
    """Insert one ``btd6_source_audit`` row; returns the new id."""
    import json

    row = await pool.get().fetchrow(
        """
        INSERT INTO btd6_source_audit (
            actor_id, guild_id, source_key, action, old_value, new_value,
            reason, created_at
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, NOW())
        RETURNING id
        """,
        actor_id,
        guild_id,
        source_key,
        action,
        json.dumps(old_value) if old_value is not None else None,
        json.dumps(new_value) if new_value is not None else None,
        reason,
    )
    return int(row["id"])


async def list_source_audit(
    source_key: str | None = None,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if source_key:
        rows = await pool.get().fetch(
            """
            SELECT id, actor_id, guild_id, source_key, action,
                   old_value, new_value, reason, created_at
            FROM btd6_source_audit
            WHERE source_key = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            source_key,
            int(limit),
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT id, actor_id, guild_id, source_key, action,
                   old_value, new_value, reason, created_at
            FROM btd6_source_audit
            ORDER BY created_at DESC
            LIMIT $1
            """,
            int(limit),
        )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# btd6_facts
# ---------------------------------------------------------------------------


async def upsert_fact(
    *,
    source_id: int,
    fact_type: str,
    entity_kind: str,
    entity_key: str,
    body_json: dict[str, Any],
    game_version: str | None,
    confidence: float = 1.0,
    version: int = 1,
) -> int:
    import json

    row = await pool.get().fetchrow(
        """
        INSERT INTO btd6_facts (
            source_id, fact_type, entity_kind, entity_key, body_json,
            game_version, fetched_at, validated_at, confidence, version
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, NOW(), NOW(), $7, $8)
        ON CONFLICT (fact_type, entity_kind, entity_key, version)
        DO UPDATE SET
            body_json    = EXCLUDED.body_json,
            game_version = EXCLUDED.game_version,
            fetched_at   = NOW(),
            validated_at = NOW(),
            confidence   = EXCLUDED.confidence
        RETURNING id
        """,
        source_id,
        fact_type,
        entity_kind,
        entity_key,
        json.dumps(body_json),
        game_version,
        confidence,
        version,
    )
    return int(row["id"])


async def get_latest_fact(
    fact_type: str,
    entity_kind: str,
    entity_key: str,
) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT f.id, f.source_id, f.fact_type, f.entity_kind, f.entity_key,
               f.body_json, f.game_version, f.fetched_at, f.validated_at,
               f.confidence, f.version, r.source_key, r.trust_tier
        FROM btd6_facts f
        JOIN btd6_source_registry r ON r.id = f.source_id
        WHERE f.fact_type = $1
          AND f.entity_kind = $2
          AND f.entity_key = $3
        ORDER BY f.version DESC
        LIMIT 1
        """,
        fact_type,
        entity_kind,
        entity_key,
    )
    return dict(row) if row else None


async def search_facts(
    *,
    fact_type: str | None = None,
    entity_kind: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    sql = (
        "SELECT id, source_id, fact_type, entity_kind, entity_key, "
        "body_json, game_version, fetched_at, validated_at, confidence, "
        "version FROM btd6_facts"
    )
    args: list[Any] = []
    clauses: list[str] = []
    if fact_type is not None:
        args.append(fact_type)
        clauses.append(f"fact_type = ${len(args)}")
    if entity_kind is not None:
        args.append(entity_kind)
        clauses.append(f"entity_kind = ${len(args)}")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    args.append(int(limit))
    sql += f" ORDER BY fetched_at DESC LIMIT ${len(args)}"
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


async def fetch_facts_for_intent(
    queries: list[tuple[str | None, str, str]],
    *,
    overall_limit: int = 50,
) -> list[dict[str, Any]]:
    """Batch fact lookup joined with the source registry (M3 grounding).

    ``queries`` is a list of ``(fact_type, entity_kind, entity_key)``
    tuples. ``fact_type`` may be ``None`` to match any fact_type for
    the given ``(entity_kind, entity_key)`` pair.

    Returns rows joined with ``btd6_source_registry`` so callers see
    ``source_key``, ``source_name``, ``trust_tier``, and ``source_kind``
    alongside the fact row. Ordering is deterministic:
    ``trust_tier ASC, fetched_at DESC, version DESC`` so Tier-1
    official_api facts win over Tier-2 patch_notes / webpage rows, and
    the latest fetched / latest version wins within a tier.
    """
    if not queries:
        return []
    clauses: list[str] = []
    args: list[Any] = []
    for fact_type, entity_kind, entity_key in queries:
        if fact_type is None:
            args.extend([entity_kind, entity_key])
            clauses.append(
                f"(f.entity_kind = ${len(args) - 1} "
                f"AND f.entity_key = ${len(args)})",
            )
        else:
            args.extend([fact_type, entity_kind, entity_key])
            clauses.append(
                f"(f.fact_type = ${len(args) - 2} "
                f"AND f.entity_kind = ${len(args) - 1} "
                f"AND f.entity_key = ${len(args)})",
            )
    args.append(int(overall_limit))
    sql = f"""
        SELECT f.id, f.source_id, f.fact_type, f.entity_kind, f.entity_key,
               f.body_json, f.game_version, f.fetched_at, f.validated_at,
               f.confidence, f.version,
               r.source_key, r.source_name, r.trust_tier, r.source_kind
        FROM btd6_facts f
        JOIN btd6_source_registry r ON r.id = f.source_id
        WHERE {" OR ".join(clauses)}
        ORDER BY r.trust_tier ASC, f.fetched_at DESC, f.version DESC
        LIMIT ${len(args)}
    """
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# btd6_patch_notes
# ---------------------------------------------------------------------------


async def upsert_patch_note(
    *,
    source_id: int,
    version: str,
    published_at: Any | None,
    body: str,
) -> int:
    row = await pool.get().fetchrow(
        """
        INSERT INTO btd6_patch_notes (
            source_id, version, published_at, body
        ) VALUES ($1, $2, $3, $4)
        ON CONFLICT (version) DO UPDATE SET
            body         = EXCLUDED.body,
            published_at = EXCLUDED.published_at
        RETURNING id
        """,
        source_id,
        version,
        published_at,
        body,
    )
    return int(row["id"])


async def latest_patch_note() -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT id, source_id, version, published_at, body
        FROM btd6_patch_notes
        ORDER BY published_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
    )
    return dict(row) if row else None
