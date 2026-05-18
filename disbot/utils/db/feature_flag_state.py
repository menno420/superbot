"""Feature flag state — DB read primitives (Phase 2d, PR-2).

Owns the read surface for ``feature_flag_global_overrides`` and
``feature_flag_guild_overrides``.  The evaluator
(:mod:`core.runtime.feature_flags`) calls these primitives behind a
TTL-bounded cache.  Writes do not exist in this PR — they ship with
:class:`services.rollout_mutation.RolloutMutationPipeline` in PR-3.

State class (per ``docs/architecture.md`` §"State classification"):

  **authoritative persistent** — the DB row is the canonical override
  for a flag.  Evaluator cache rows are derived state that may be
  invalidated at any time.

Public surface:

* :func:`get_global_override` — single-row read.
* :func:`get_guild_override` — single-row read scoped to a guild.
* :func:`delete_for_guild` — purge ALL per-guild overrides for one
  guild (called from ``guild_lifecycle.teardown``).  Global rows are
  never touched here.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.feature_flag_state")


async def get_global_override(flag_name: str) -> dict[str, Any] | None:
    """Return the global override row for ``flag_name``, or ``None``.

    The returned dict carries ``state`` (str), ``rollout_percent``
    (int | None), ``set_by`` (int | None), ``set_at``
    (:class:`datetime`).  Callers convert ``state`` into the typed
    enum at the layer above (the evaluator).
    """
    row = await pool.get().fetchrow(
        """
        SELECT flag_name, state, rollout_percent, set_by, set_at
        FROM feature_flag_global_overrides
        WHERE flag_name = $1
        """,
        flag_name,
    )
    return dict(row) if row else None


async def get_guild_override(
    flag_name: str,
    guild_id: int,
) -> dict[str, Any] | None:
    """Return the per-guild override row, or ``None`` when absent."""
    row = await pool.get().fetchrow(
        """
        SELECT flag_name, guild_id, state, set_by, set_at
        FROM feature_flag_guild_overrides
        WHERE flag_name = $1 AND guild_id = $2
        """,
        flag_name,
        guild_id,
    )
    return dict(row) if row else None


async def list_global_overrides() -> list[dict[str, Any]]:
    """Return every global override row.

    Used by the diagnostics provider so ``!platform flags`` can render
    the global state alongside the declarations.
    """
    rows = await pool.get().fetch(
        """
        SELECT flag_name, state, rollout_percent, set_by, set_at
        FROM feature_flag_global_overrides
        ORDER BY flag_name
        """,
    )
    return [dict(r) for r in rows]


async def list_guild_overrides(guild_id: int) -> list[dict[str, Any]]:
    """Return every per-guild override row for ``guild_id``."""
    rows = await pool.get().fetch(
        """
        SELECT flag_name, guild_id, state, set_by, set_at
        FROM feature_flag_guild_overrides
        WHERE guild_id = $1
        ORDER BY flag_name
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def upsert_global_with_audit(
    *,
    flag_name: str,
    state: str,
    rollout_percent: int | None,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_state: str | None,
    prev_rollout_percent: int | None,
    mutation_type: str,
) -> None:
    """Atomic: upsert feature_flag_global_overrides + write audit row.

    Wraps both statements in a single asyncpg transaction so partial
    failures roll back.  Called only from
    :class:`services.rollout_mutation.RolloutMutationPipeline`.
    """
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO feature_flag_global_overrides
                (flag_name, state, rollout_percent, set_by, set_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (flag_name) DO UPDATE SET
                state = EXCLUDED.state,
                rollout_percent = EXCLUDED.rollout_percent,
                set_by = EXCLUDED.set_by,
                set_at = NOW()
            """,
            flag_name,
            state,
            rollout_percent,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO feature_flag_audit
                (mutation_id, flag_name, scope, guild_id,
                 prev_state, new_state,
                 prev_rollout_percent, new_rollout_percent,
                 actor_id, actor_type, mutation_type)
            VALUES ($1, $2, 'global', NULL,
                    $3, $4, $5, $6, $7, $8, $9)
            """,
            mutation_id,
            flag_name,
            prev_state,
            state,
            prev_rollout_percent,
            rollout_percent,
            actor_id,
            actor_type,
            mutation_type,
        )


async def upsert_guild_with_audit(
    *,
    flag_name: str,
    guild_id: int,
    state: str,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_state: str | None,
) -> None:
    """Atomic: upsert feature_flag_guild_overrides + audit row."""
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO feature_flag_guild_overrides
                (flag_name, guild_id, state, set_by, set_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (flag_name, guild_id) DO UPDATE SET
                state = EXCLUDED.state,
                set_by = EXCLUDED.set_by,
                set_at = NOW()
            """,
            flag_name,
            guild_id,
            state,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO feature_flag_audit
                (mutation_id, flag_name, scope, guild_id,
                 prev_state, new_state,
                 actor_id, actor_type, mutation_type)
            VALUES ($1, $2, 'guild', $3, $4, $5, $6, $7, 'set_state')
            """,
            mutation_id,
            flag_name,
            guild_id,
            prev_state,
            state,
            actor_id,
            actor_type,
        )


async def get_audit_count(
    *,
    flag_name: str | None = None,
    guild_id: int | None = None,
) -> int:
    """Return audit-row count, optionally filtered by flag and/or guild.

    Used by tests + diagnostics to assert audit rows landed.
    """
    if flag_name is not None and guild_id is not None:
        sql = (
            "SELECT COUNT(*)::int AS n FROM feature_flag_audit "
            "WHERE flag_name = $1 AND guild_id = $2"
        )
        row = await pool.get().fetchrow(sql, flag_name, guild_id)
    elif flag_name is not None:
        sql = "SELECT COUNT(*)::int AS n FROM feature_flag_audit WHERE flag_name = $1"
        row = await pool.get().fetchrow(sql, flag_name)
    elif guild_id is not None:
        sql = "SELECT COUNT(*)::int AS n FROM feature_flag_audit WHERE guild_id = $1"
        row = await pool.get().fetchrow(sql, guild_id)
    else:
        row = await pool.get().fetchrow(
            "SELECT COUNT(*)::int AS n FROM feature_flag_audit",
        )
    return int(row["n"]) if row else 0


async def delete_for_guild(guild_id: int) -> int:
    """Delete every per-guild override for ``guild_id``; preserve globals.

    Phase 2 retention policy: the GLOBAL overrides row survives every
    guild leave (it's not scoped to a single guild).  This primitive
    touches only ``feature_flag_guild_overrides``.  Returns the row
    count parsed from asyncpg's ``"DELETE N"`` status string; ``0`` on
    any parse failure.
    """
    result = await pool.get().execute(
        "DELETE FROM feature_flag_guild_overrides WHERE guild_id = $1",
        guild_id,
    )
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


__all__ = [
    "delete_for_guild",
    "get_audit_count",
    "get_global_override",
    "get_guild_override",
    "list_global_overrides",
    "list_guild_overrides",
    "upsert_global_with_audit",
    "upsert_guild_with_audit",
]
