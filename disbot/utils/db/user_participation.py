"""Per-user participation — DB read primitives (Phase 2c, PR-8).

Owns the read surface for the four participation tables shipped in
migration 027.  Writes ship with
:class:`services.participation_mutation.ParticipationMutationPipeline`
in PR-9.

The four tables are intentionally separated — see
:mod:`core.runtime.participation_schema` for the structural rationale.
Each table has its own dedicated read primitive here; nothing combines
them into a single "user settings" blob.

Public surface:

* :func:`get_participation`   — single-row read on ``user_participation``.
* :func:`get_subscription`    — single-row read on ``user_subscriptions``.
* :func:`get_preference`      — single-row read on ``user_preferences``.
* :func:`get_visibility`      — single-row read on ``user_visibility_overrides``.
* :func:`list_for_user`       — bundle reader returning every row for
  one ``(user, guild)`` pair across the four tables.  Used by the
  ``core.runtime.user_config`` cache loader.
* :func:`delete_for_guild`    — guild-leave teardown; deletes every
  row whose ``guild_id`` matches.  Per the consistency-ledger
  retention policy, **per-guild participation rows ARE deleted on
  guild leave** so the same user's participation in other guilds is
  preserved.

Status / visibility literals (mirror migration 027 CHECK constraints):

  user_participation.state         IN ('opted_in', 'opted_out')
  user_visibility_overrides.visibility IN ('public', 'hidden')
"""

from __future__ import annotations

import json
import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.user_participation")

# Mirror migration 027 CHECK constraints.  Alignment tests pin these.
PARTICIPATION_STATES: frozenset[str] = frozenset({"opted_in", "opted_out"})
VISIBILITY_STATES: frozenset[str] = frozenset({"public", "hidden"})


def _deserialise(raw: Any | None) -> Any | None:
    """Decode a JSONB value (accepts str or already-decoded dict/list)."""
    if raw is None or isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        logger.warning(
            "user_participation: failed to JSON-decode preference value; returning raw",
        )
        return raw


# ---------------------------------------------------------------------------
# Single-row reads
# ---------------------------------------------------------------------------


async def get_participation(
    user_id: int,
    guild_id: int,
    subsystem: str,
) -> dict[str, Any] | None:
    """Return the participation row, or ``None`` for a missing row.

    Missing-row semantics (consumed by the typed accessor in
    :mod:`utils.user_config_accessors`): caller interprets ``None`` as
    ``ParticipationState.NOT_SET``.
    """
    row = await pool.get().fetchrow(
        """
        SELECT user_id, guild_id, subsystem, state, set_at, set_by
        FROM user_participation
        WHERE user_id = $1 AND guild_id = $2 AND subsystem = $3
        """,
        user_id,
        guild_id,
        subsystem,
    )
    return dict(row) if row else None


async def get_subscription(
    user_id: int,
    guild_id: int,
    subsystem: str,
    topic: str,
) -> dict[str, Any] | None:
    """Return the subscription row, or ``None`` for missing.

    Missing-row semantics: caller interprets ``None`` as the schema's
    declared default for that topic.
    """
    row = await pool.get().fetchrow(
        """
        SELECT user_id, guild_id, subsystem, topic, enabled, set_at, set_by
        FROM user_subscriptions
        WHERE user_id = $1 AND guild_id = $2
          AND subsystem = $3 AND topic = $4
        """,
        user_id,
        guild_id,
        subsystem,
        topic,
    )
    return dict(row) if row else None


async def get_preference(
    user_id: int,
    guild_id: int,
    key: str,
) -> dict[str, Any] | None:
    """Return the preference row with value JSON-decoded, or ``None``."""
    row = await pool.get().fetchrow(
        """
        SELECT user_id, guild_id, key, value, set_at, set_by
        FROM user_preferences
        WHERE user_id = $1 AND guild_id = $2 AND key = $3
        """,
        user_id,
        guild_id,
        key,
    )
    if row is None:
        return None
    out = dict(row)
    out["value"] = _deserialise(out.get("value"))
    return out


async def get_visibility(
    user_id: int,
    guild_id: int,
    subsystem: str,
) -> dict[str, Any] | None:
    """Return the visibility override, or ``None`` for missing."""
    row = await pool.get().fetchrow(
        """
        SELECT user_id, guild_id, subsystem, visibility, set_at, set_by
        FROM user_visibility_overrides
        WHERE user_id = $1 AND guild_id = $2 AND subsystem = $3
        """,
        user_id,
        guild_id,
        subsystem,
    )
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Bundle reader used by the runtime cache loader
# ---------------------------------------------------------------------------


async def list_for_user(user_id: int, guild_id: int) -> dict[str, list[dict[str, Any]]]:
    """Return every row across the four tables for ``(user, guild)``.

    Shape:

    {
        "participation":         [...],
        "subscriptions":         [...],
        "preferences":           [...],
        "visibility_overrides":  [...],
    }

    Used by ``core.runtime.user_config`` to populate its per-(user,
    guild) cache on miss with a single round trip per table.
    """
    p_rows = await pool.get().fetch(
        """
        SELECT user_id, guild_id, subsystem, state, set_at, set_by
        FROM user_participation
        WHERE user_id = $1 AND guild_id = $2
        """,
        user_id,
        guild_id,
    )
    s_rows = await pool.get().fetch(
        """
        SELECT user_id, guild_id, subsystem, topic, enabled, set_at, set_by
        FROM user_subscriptions
        WHERE user_id = $1 AND guild_id = $2
        """,
        user_id,
        guild_id,
    )
    pref_rows = await pool.get().fetch(
        """
        SELECT user_id, guild_id, key, value, set_at, set_by
        FROM user_preferences
        WHERE user_id = $1 AND guild_id = $2
        """,
        user_id,
        guild_id,
    )
    v_rows = await pool.get().fetch(
        """
        SELECT user_id, guild_id, subsystem, visibility, set_at, set_by
        FROM user_visibility_overrides
        WHERE user_id = $1 AND guild_id = $2
        """,
        user_id,
        guild_id,
    )
    return {
        "participation": [dict(r) for r in p_rows],
        "subscriptions": [dict(r) for r in s_rows],
        "preferences": [
            {**dict(r), "value": _deserialise(dict(r).get("value"))} for r in pref_rows
        ],
        "visibility_overrides": [dict(r) for r in v_rows],
    }


# ---------------------------------------------------------------------------
# Diagnostics helpers
# ---------------------------------------------------------------------------


async def count_rows() -> dict[str, int]:
    """Return per-table row counts across all guilds.

    Used by the participation diagnostics provider.  This is a small
    administrative query; not on any hot path.  Each table has its
    own explicit COUNT statement so the no-dynamic-SQL invariant
    (``tests/unit/invariants/test_no_dynamic_sql.py``) stays clean.
    """
    p_row = await pool.get().fetchrow(
        "SELECT COUNT(*)::int AS n FROM user_participation",
    )
    s_row = await pool.get().fetchrow(
        "SELECT COUNT(*)::int AS n FROM user_subscriptions",
    )
    pref_row = await pool.get().fetchrow(
        "SELECT COUNT(*)::int AS n FROM user_preferences",
    )
    v_row = await pool.get().fetchrow(
        "SELECT COUNT(*)::int AS n FROM user_visibility_overrides",
    )
    return {
        "user_participation": int(p_row["n"]) if p_row else 0,
        "user_subscriptions": int(s_row["n"]) if s_row else 0,
        "user_preferences": int(pref_row["n"]) if pref_row else 0,
        "user_visibility_overrides": int(v_row["n"]) if v_row else 0,
    }


# ---------------------------------------------------------------------------
# Teardown — drop every per-guild row for one guild.  Per the
# retention policy in docs/health/platform-consistency-ledger.md §3, the
# same user's participation in OTHER guilds is preserved.
# ---------------------------------------------------------------------------


def _parse_delete_count(result: str) -> int:
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


async def delete_for_guild(guild_id: int) -> int:
    """Delete every row in the four tables that belongs to ``guild_id``.

    Returns the total deleted-row count across the four tables.
    Runs in one transaction so the four deletes either all succeed
    or all roll back.  Each table has its own explicit DELETE
    statement so the no-dynamic-SQL invariant stays clean.
    """
    async with pool.get().acquire() as conn, conn.transaction():
        r1 = await conn.execute(
            "DELETE FROM user_participation WHERE guild_id = $1",
            guild_id,
        )
        r2 = await conn.execute(
            "DELETE FROM user_subscriptions WHERE guild_id = $1",
            guild_id,
        )
        r3 = await conn.execute(
            "DELETE FROM user_preferences WHERE guild_id = $1",
            guild_id,
        )
        r4 = await conn.execute(
            "DELETE FROM user_visibility_overrides WHERE guild_id = $1",
            guild_id,
        )
    return sum(_parse_delete_count(r) for r in (r1, r2, r3, r4))


# ---------------------------------------------------------------------------
# Atomic write + audit primitives (Phase 2c PR-9)
#
# Every mutation is one transaction: target row UPSERT + audit row INSERT.
# Called only by services.participation_mutation.ParticipationMutationPipeline;
# direct invocation from cog/service code is forbidden by the
# pipeline-write-authority invariant.
# ---------------------------------------------------------------------------


async def upsert_participation_with_audit(
    *,
    user_id: int,
    guild_id: int,
    subsystem: str,
    state: str,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_state: str | None,
) -> None:
    """Atomic: upsert ``user_participation`` row + write audit row."""
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO user_participation
                (user_id, guild_id, subsystem, state, set_at, set_by)
            VALUES ($1, $2, $3, $4, NOW(), $5)
            ON CONFLICT (user_id, guild_id, subsystem) DO UPDATE SET
                state = EXCLUDED.state,
                set_at = NOW(),
                set_by = EXCLUDED.set_by
            """,
            user_id,
            guild_id,
            subsystem,
            state,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO user_participation_audit
                (mutation_id, user_id, guild_id, mutation_type,
                 subsystem, prev_state, new_state,
                 actor_id, actor_type)
            VALUES ($1, $2, $3, 'set_participation', $4, $5, $6, $7, $8)
            """,
            mutation_id,
            user_id,
            guild_id,
            subsystem,
            prev_state,
            state,
            actor_id,
            actor_type,
        )


async def upsert_subscription_with_audit(
    *,
    user_id: int,
    guild_id: int,
    subsystem: str,
    topic: str,
    enabled: bool,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_enabled: bool | None,
) -> None:
    """Atomic: upsert ``user_subscriptions`` row + write audit row."""
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO user_subscriptions
                (user_id, guild_id, subsystem, topic, enabled, set_at, set_by)
            VALUES ($1, $2, $3, $4, $5, NOW(), $6)
            ON CONFLICT (user_id, guild_id, subsystem, topic) DO UPDATE SET
                enabled = EXCLUDED.enabled,
                set_at = NOW(),
                set_by = EXCLUDED.set_by
            """,
            user_id,
            guild_id,
            subsystem,
            topic,
            enabled,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO user_participation_audit
                (mutation_id, user_id, guild_id, mutation_type,
                 subsystem, topic, prev_enabled, new_enabled,
                 actor_id, actor_type)
            VALUES ($1, $2, $3, 'set_subscription', $4, $5, $6, $7, $8, $9)
            """,
            mutation_id,
            user_id,
            guild_id,
            subsystem,
            topic,
            prev_enabled,
            enabled,
            actor_id,
            actor_type,
        )


async def upsert_preference_with_audit(
    *,
    user_id: int,
    guild_id: int,
    key: str,
    value: Any,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_value: Any,
) -> None:
    """Atomic: upsert ``user_preferences`` row + write audit row.

    Both ``value`` and ``prev_value`` are JSON-encoded for the JSONB
    columns.  ``None`` for ``prev_value`` is treated as SQL NULL.
    """
    serialised_new = json.dumps(value, default=str)
    serialised_prev = (
        None if prev_value is None else json.dumps(prev_value, default=str)
    )
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO user_preferences
                (user_id, guild_id, key, value, set_at, set_by)
            VALUES ($1, $2, $3, $4, NOW(), $5)
            ON CONFLICT (user_id, guild_id, key) DO UPDATE SET
                value = EXCLUDED.value,
                set_at = NOW(),
                set_by = EXCLUDED.set_by
            """,
            user_id,
            guild_id,
            key,
            serialised_new,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO user_participation_audit
                (mutation_id, user_id, guild_id, mutation_type,
                 key, prev_value, new_value,
                 actor_id, actor_type)
            VALUES ($1, $2, $3, 'set_preference', $4, $5, $6, $7, $8)
            """,
            mutation_id,
            user_id,
            guild_id,
            key,
            serialised_prev,
            serialised_new,
            actor_id,
            actor_type,
        )


async def upsert_visibility_with_audit(
    *,
    user_id: int,
    guild_id: int,
    subsystem: str,
    visibility: str,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_visibility: str | None,
) -> None:
    """Atomic: upsert ``user_visibility_overrides`` row + write audit row."""
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO user_visibility_overrides
                (user_id, guild_id, subsystem, visibility, set_at, set_by)
            VALUES ($1, $2, $3, $4, NOW(), $5)
            ON CONFLICT (user_id, guild_id, subsystem) DO UPDATE SET
                visibility = EXCLUDED.visibility,
                set_at = NOW(),
                set_by = EXCLUDED.set_by
            """,
            user_id,
            guild_id,
            subsystem,
            visibility,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO user_participation_audit
                (mutation_id, user_id, guild_id, mutation_type,
                 subsystem, prev_visibility, new_visibility,
                 actor_id, actor_type)
            VALUES ($1, $2, $3, 'set_visibility', $4, $5, $6, $7, $8)
            """,
            mutation_id,
            user_id,
            guild_id,
            subsystem,
            prev_visibility,
            visibility,
            actor_id,
            actor_type,
        )


async def get_audit_count(
    *,
    user_id: int | None = None,
    guild_id: int | None = None,
    mutation_type: str | None = None,
) -> int:
    """Return audit-row count, optionally filtered.

    Used by tests + future diagnostics to assert audit rows landed.
    """
    clauses: list[str] = []
    args: list[Any] = []
    if user_id is not None:
        args.append(user_id)
        clauses.append(f"user_id = ${len(args)}")
    if guild_id is not None:
        args.append(guild_id)
        clauses.append(f"guild_id = ${len(args)}")
    if mutation_type is not None:
        args.append(mutation_type)
        clauses.append(f"mutation_type = ${len(args)}")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    row = await pool.get().fetchrow(
        f"SELECT COUNT(*)::int AS n FROM user_participation_audit {where}",
        *args,
    )
    return int(row["n"]) if row else 0


__all__ = [
    "PARTICIPATION_STATES",
    "VISIBILITY_STATES",
    "count_rows",
    "delete_for_guild",
    "get_audit_count",
    "get_participation",
    "get_preference",
    "get_subscription",
    "get_visibility",
    "list_for_user",
    "upsert_participation_with_audit",
    "upsert_preference_with_audit",
    "upsert_subscription_with_audit",
    "upsert_visibility_with_audit",
]
