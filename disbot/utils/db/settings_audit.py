"""Settings mutation audit — DB CRUD primitives (S4).

Owns the read/write surface for ``settings_mutation_audit`` (migration
029) and the combined-transaction write that lands both the legacy
``guild_settings`` row and the audit row atomically.

Higher-level callers route through
:class:`services.settings_mutation.SettingsMutationPipeline`; nothing
outside this module + the pipeline issues raw SQL against the audit
table.

Transaction model:
The pipeline calls :func:`set_value_with_audit`, which opens a single
asyncpg transaction so the KV upsert + audit insert land atomically.
Read primitives are autocommit.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.settings_audit")


# ---------------------------------------------------------------------------
# Mutation primitive — used only by SettingsMutationPipeline
# ---------------------------------------------------------------------------


async def set_value_with_audit(
    *,
    guild_id: int,
    subsystem: str,
    name: str,
    settings_key: str,
    prev_value_raw: str | None,
    new_value_raw: str,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    mutation_type: str = "set_value",
) -> None:
    """Atomic write: upsert the ``guild_settings`` row + insert one audit row.

    Both statements run inside a single asyncpg transaction.  If either
    fails the entire mutation is rolled back; the pipeline only
    invalidates caches and emits events after this returns
    successfully.

    Args:
        guild_id: Discord guild snowflake.
        subsystem: Owning subsystem name (``SUBSYSTEMS`` key).
        name: ``SettingSpec.name`` (unique within the subsystem).
        settings_key: Canonical key from :mod:`utils.settings_keys`
            (the legacy KV row's ``key`` column).
        prev_value_raw: The previous raw KV value, or ``None`` if no
            row existed before this mutation.
        new_value_raw: The new raw KV value (already serialized to a
            string by the pipeline).
        actor_id: Discord snowflake of the actor, or ``None`` for
            ``actor_type='system'`` writes.
        actor_type: One of ``user`` / ``moderator`` / ``admin`` /
            ``system`` / ``backfill`` (matches the CHECK constraint
            in migration 029).
        mutation_id: Caller-generated UUID for cross-pipeline
            correlation.  Same value lands in the audit row.
        mutation_type: ``set_value`` for v1.  Reserved to extend in
            S6 when ``reset_value`` lands.
    """
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO guild_settings (guild_id, key, value)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, key)
            DO UPDATE SET value = EXCLUDED.value
            """,
            guild_id,
            settings_key,
            new_value_raw,
        )
        await conn.execute(
            """
            INSERT INTO settings_mutation_audit
                (mutation_id, guild_id, subsystem, name, settings_key,
                 prev_value_raw, new_value_raw,
                 actor_id, actor_type, mutation_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            mutation_id,
            guild_id,
            subsystem,
            name,
            settings_key,
            prev_value_raw,
            new_value_raw,
            actor_id,
            actor_type,
            mutation_type,
        )


# ---------------------------------------------------------------------------
# Read primitives — diagnostic / future !platform consistency surface
# ---------------------------------------------------------------------------


async def count_for_guild(guild_id: int) -> int:
    """Return the audit row count for ``guild_id``.

    Used by the future ``_collect_settings_mutation`` collector in
    :mod:`services.platform_consistency` (deferred to a follow-up PR,
    matching the S1 / S2 / S2.5 / S3 deferred-collector precedent).
    """
    row = await pool.get().fetchrow(
        "SELECT COUNT(*) AS n FROM settings_mutation_audit WHERE guild_id = $1",
        guild_id,
    )
    return int(row["n"]) if row else 0


async def count_total() -> int:
    """Return the total audit row count across all guilds."""
    row = await pool.get().fetchrow(
        "SELECT COUNT(*) AS n FROM settings_mutation_audit",
    )
    return int(row["n"]) if row else 0


async def list_recent_for_guild(
    guild_id: int,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` most recent audit rows for ``guild_id``."""
    rows = await pool.get().fetch(
        """
        SELECT id, mutation_id, guild_id, subsystem, name, settings_key,
               prev_value_raw, new_value_raw,
               actor_id, actor_type, mutation_type, at
        FROM settings_mutation_audit
        WHERE guild_id = $1
        ORDER BY at DESC
        LIMIT $2
        """,
        guild_id,
        limit,
    )
    return [dict(r) for r in rows]


async def list_recent_for_key(
    settings_key: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` most recent audit rows for ``settings_key``.

    Useful for "show me every mutation that touched WARN_THRESHOLD
    across all guilds".
    """
    rows = await pool.get().fetch(
        """
        SELECT id, mutation_id, guild_id, subsystem, name, settings_key,
               prev_value_raw, new_value_raw,
               actor_id, actor_type, mutation_type, at
        FROM settings_mutation_audit
        WHERE settings_key = $1
        ORDER BY at DESC
        LIMIT $2
        """,
        settings_key,
        limit,
    )
    return [dict(r) for r in rows]


__all__ = [
    "count_for_guild",
    "count_total",
    "list_recent_for_guild",
    "list_recent_for_key",
    "set_value_with_audit",
]
