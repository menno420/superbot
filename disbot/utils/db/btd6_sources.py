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
from datetime import datetime
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
        f" ORDER BY trust_tier, source_key LIMIT ${len(args) - 1} OFFSET ${len(args)}"
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
    """Insert one ``btd6_source_audit`` row; returns the new id.

    ``old_value`` and ``new_value`` are passed as dicts; the JSONB codec
    on the connection handles encoding. Pre-encoding via ``json.dumps``
    here would double-wrap them.
    """
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
        old_value,
        new_value,
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
    # body_json is passed as a dict; the JSONB codec on the connection
    # (utils.db.codec.init_connection) handles json.dumps on the wire.
    # Don't pre-encode here — doing so double-wraps the value and the
    # row reads back as a JSON string instead of a dict.
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
        body_json,
        game_version,
        confidence,
        version,
    )
    return int(row["id"])


async def get_latest_fact(
    fact_type: str | None,
    entity_kind: str,
    entity_key: str,
) -> dict[str, Any] | None:
    """Newest fact for an entity, optionally filtered by ``fact_type``.

    ``fact_type=None`` matches any fact_type for the (entity_kind,
    entity_key) pair — useful when a caller has the entity but doesn't
    know which fact_type carries the answer (e.g. index vs metadata).
    """
    if fact_type is None:
        row = await pool.get().fetchrow(
            """
            SELECT f.id, f.source_id, f.fact_type, f.entity_kind, f.entity_key,
                   f.body_json, f.game_version, f.fetched_at, f.validated_at,
                   f.confidence, f.version, r.source_key, r.trust_tier
            FROM btd6_facts f
            JOIN btd6_source_registry r ON r.id = f.source_id
            WHERE f.entity_kind = $1
              AND f.entity_key = $2
            ORDER BY f.fetched_at DESC, f.version DESC
            LIMIT 1
            """,
            entity_kind,
            entity_key,
        )
    else:
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


async def latest_fact_per_entity_kind(
    kinds: list[str],
) -> dict[str, dict[str, Any]]:
    """For each entity_kind, the single newest fact row.

    One round-trip via DISTINCT ON. Kinds absent from ``btd6_facts``
    are absent from the returned dict (no ``None`` placeholders).
    Empty ``kinds`` returns ``{}`` without hitting the DB.
    """
    if not kinds:
        return {}
    rows = await pool.get().fetch(
        """
        SELECT DISTINCT ON (entity_kind)
               id, source_id, fact_type, entity_kind, entity_key,
               body_json, game_version, fetched_at, validated_at,
               confidence, version
        FROM btd6_facts
        WHERE entity_kind = ANY($1::text[])
        ORDER BY entity_kind, fetched_at DESC, version DESC
        """,
        kinds,
    )
    return {row["entity_kind"]: dict(row) for row in rows}


async def aggregate_facts_by_entity_kind() -> list[dict[str, Any]]:
    """One row per entity_kind in ``btd6_facts`` with count + max(fetched_at).

    Stable SQL ordering (by entity_kind) so unit tests can assert
    deterministic shape; UI consumers re-order by useful-first.
    """
    rows = await pool.get().fetch(
        "SELECT entity_kind, COUNT(*)::int AS fact_count, "
        "MAX(fetched_at) AS last_fetched_at "
        "FROM btd6_facts "
        "GROUP BY entity_kind "
        "ORDER BY entity_kind",
    )
    return [dict(r) for r in rows]


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


async def list_ct_tiles_for_event(
    ct_id: str,
    *,
    limit: int = 256,
) -> list[dict[str, Any]]:
    """All ``btd6_ct_tile`` facts for one Contested Territory event.

    Tiles are stored with ``entity_key = "{ct_id}_tile_{tile_id}"`` (see
    :mod:`services.parsers.ninjakiwi_ct`). A CT map has 169 tiles, and
    several events can be stored at once, so a plain
    :func:`search_facts` (which only filters ``fact_type`` / ``entity_kind``
    and orders by ``fetched_at``) could silently drop tiles. Scoping by
    the ``entity_key`` prefix returns exactly this event's tiles. The
    newest version of each tile is kept via ``DISTINCT ON (entity_key)``.
    """
    safe_limit = max(1, int(limit))
    rows = await pool.get().fetch(
        """
        SELECT DISTINCT ON (entity_key)
               id, source_id, fact_type, entity_kind, entity_key,
               body_json, game_version, fetched_at, validated_at,
               confidence, version
        FROM btd6_facts
        WHERE entity_kind = 'btd6_ct_tile'
          AND entity_key LIKE $1 || '_tile_%'
        ORDER BY entity_key, fetched_at DESC, version DESC
        LIMIT $2
        """,
        ct_id,
        safe_limit,
    )
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
                f"(f.entity_kind = ${len(args) - 1} AND f.entity_key = ${len(args)})",
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


# ---------------------------------------------------------------------------
# btd6_ingestion_runs
# ---------------------------------------------------------------------------


async def insert_ingestion_run(
    *,
    source_key: str,
    status: str,
    triggered_by: str,
    path_params_json: dict[str, Any] | None,
    started_by_user_id: int | None,
) -> int:
    """INSERT a new ingestion run row; returns the new id.

    ``path_params_json`` is passed as a dict; the JSONB codec on the
    connection handles encoding. Pre-encoding via ``json.dumps`` here
    would double-wrap the value.
    """
    row = await pool.get().fetchrow(
        """
        INSERT INTO btd6_ingestion_runs (
            source_key, status, triggered_by,
            path_params_json, started_by_user_id
        ) VALUES ($1, $2, $3, $4::jsonb, $5)
        RETURNING id
        """,
        source_key,
        status,
        triggered_by,
        path_params_json,
        started_by_user_id,
    )
    return int(row["id"])


async def update_ingestion_run(
    run_id: int,
    *,
    status: str,
    finished_at: datetime,
    duration_ms: int,
    fact_count: int | None = None,
    raw_body_hash: str | None = None,
    status_code: int | None = None,
    path_params_hash: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    await pool.get().execute(
        """
        UPDATE btd6_ingestion_runs SET
            status           = $2,
            finished_at      = $3,
            duration_ms      = $4,
            fact_count       = $5,
            raw_body_hash    = $6,
            status_code      = $7,
            path_params_hash = $8,
            error_code       = $9,
            error_message    = $10
        WHERE id = $1
        """,
        run_id,
        status,
        finished_at,
        duration_ms,
        fact_count,
        raw_body_hash,
        status_code,
        path_params_hash,
        error_code,
        error_message,
    )


async def mark_stale_runs_interrupted(
    *,
    older_than_minutes: int = 10,
) -> int:
    """Mark running rows older than the threshold as interrupted.

    Called at supervisor startup to recover rows left in 'running'
    status by a crashed or killed process.
    Returns the count of rows updated.
    """
    result = await pool.get().execute(
        """
        UPDATE btd6_ingestion_runs
        SET status     = 'interrupted',
            error_code = 'supervisor_restart',
            finished_at = now()
        WHERE status = 'running'
          AND started_at < now() - ($1 || ' minutes')::interval
        """,
        str(older_than_minutes),
    )
    return int(result.split()[-1])


async def list_ingestion_runs(
    *,
    source_key: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Most-recent ingestion run rows, newest first.

    Read counterpart to :func:`insert_ingestion_run` /
    :func:`update_ingestion_run`, powering the operator readiness and
    recent-runs surfaces. ``source_key=None`` returns the latest runs
    across all sources; pass a key to scope to one source. Bounded by
    :data:`_LIST_SOURCES_MAX_LIMIT`.
    """
    safe_limit = max(1, min(int(limit), _LIST_SOURCES_MAX_LIMIT))
    sql = (
        "SELECT id, source_key, status, triggered_by, started_at, "
        "finished_at, duration_ms, fact_count, status_code, "
        "error_code, error_message "
        "FROM btd6_ingestion_runs"
    )
    args: list[Any] = []
    if source_key is not None:
        args.append(source_key)
        sql += f" WHERE source_key = ${len(args)}"
    args.append(safe_limit)
    sql += f" ORDER BY started_at DESC, id DESC LIMIT ${len(args)}"
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# btd6_source_snapshots
# ---------------------------------------------------------------------------


async def insert_source_snapshot(
    *,
    source_id: int,
    status_code: int,
    raw_body_hash: str,
    raw_body: str,
) -> None:
    await pool.get().execute(
        """
        INSERT INTO btd6_source_snapshots
            (source_id, status_code, raw_body_hash, raw_body)
        VALUES ($1, $2, $3, $4)
        """,
        source_id,
        status_code,
        raw_body_hash,
        raw_body,
    )
