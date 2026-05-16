"""Governance table CRUD: subsystem_visibility, cleanup_policies, audit.

All mutations should route through ``governance.writes.GovernanceMutationPipeline``
in production code so the audit log + cache invalidation + event emit
happen atomically.  These primitives are the implementation hooks the
pipeline calls into.
"""

from __future__ import annotations

from utils.db import pool

# ---------------------------------------------------------------------------
# subsystem_visibility — per-scope (guild/category/channel) tri-state overrides
# ---------------------------------------------------------------------------


async def get_subsystem_visibility(
    guild_id: int,
    scope_type: str,
    scope_id: int,
) -> dict[str, bool | None]:
    """Subsystem→enabled mapping for a scope. Missing rows = not in dict."""
    rows = await pool.get().fetch(
        "SELECT subsystem, enabled FROM subsystem_visibility"
        " WHERE guild_id=$1 AND scope_type=$2 AND scope_id=$3",
        guild_id,
        scope_type,
        scope_id,
    )
    return {r["subsystem"]: r["enabled"] for r in rows}


async def get_all_visibility_for_guild(guild_id: int):
    """Fetch all visibility rows for a guild (all scopes) in one query."""
    return await pool.get().fetch(
        "SELECT scope_type, scope_id, subsystem, enabled"
        " FROM subsystem_visibility WHERE guild_id=$1",
        guild_id,
    )


async def get_visibility_override(
    guild_id: int,
    scope_type: str,
    scope_id: int,
    subsystem: str,
) -> bool | None:
    """Return the enabled value for a specific override, or None.

    Used by GovernanceMutationPipeline to read the prior value before
    writing, so the governance audit log captures both before and after
    state.
    """
    row = await pool.get().fetchrow(
        """SELECT enabled FROM subsystem_visibility
           WHERE guild_id = $1 AND scope_type = $2
             AND scope_id = $3 AND subsystem = $4""",
        guild_id,
        scope_type,
        scope_id,
        subsystem,
    )
    return (
        bool(row["enabled"]) if row is not None and row["enabled"] is not None else None
    )


async def set_subsystem_visibility(
    guild_id: int,
    scope_type: str,
    scope_id: int,
    subsystem: str,
    enabled: bool | None,
) -> None:
    """Upsert a visibility override. enabled=None clears (inherit)."""
    await pool.get().execute(
        """INSERT INTO subsystem_visibility
               (guild_id, scope_type, scope_id, subsystem, enabled)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (guild_id, scope_type, scope_id, subsystem)
           DO UPDATE SET enabled = EXCLUDED.enabled""",
        guild_id,
        scope_type,
        scope_id,
        subsystem,
        enabled,
    )


# ---------------------------------------------------------------------------
# cleanup_policies — per-scope cleanup behaviour overrides
# ---------------------------------------------------------------------------


async def get_cleanup_policy(
    guild_id: int,
    scope_type: str,
    scope_id: int,
) -> dict | None:
    """Cleanup policy for a scope, or None if no row exists."""
    row = await pool.get().fetchrow(
        "SELECT delete_invalid_commands, delete_failed_commands, delete_after_seconds"
        " FROM cleanup_policies WHERE guild_id=$1 AND scope_type=$2 AND scope_id=$3",
        guild_id,
        scope_type,
        scope_id,
    )
    return dict(row) if row else None


async def get_all_cleanup_for_guild(guild_id: int) -> list[dict]:
    """All cleanup policy rows for a guild (every scope)."""
    rows = await pool.get().fetch(
        "SELECT scope_type, scope_id, delete_invalid_commands,"
        " delete_failed_commands, delete_after_seconds"
        " FROM cleanup_policies WHERE guild_id=$1",
        guild_id,
    )
    return [dict(r) for r in rows]


async def set_cleanup_policy(
    guild_id: int,
    scope_type: str,
    scope_id: int,
    delete_invalid_commands: bool = True,
    delete_failed_commands: bool = True,
    delete_after_seconds: int = 5,
) -> None:
    await pool.get().execute(
        """INSERT INTO cleanup_policies
               (guild_id, scope_type, scope_id,
                delete_invalid_commands, delete_failed_commands,
                delete_after_seconds)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (guild_id, scope_type, scope_id)
           DO UPDATE SET
               delete_invalid_commands = EXCLUDED.delete_invalid_commands,
               delete_failed_commands  = EXCLUDED.delete_failed_commands,
               delete_after_seconds    = EXCLUDED.delete_after_seconds""",
        guild_id,
        scope_type,
        scope_id,
        delete_invalid_commands,
        delete_failed_commands,
        delete_after_seconds,
    )


# ---------------------------------------------------------------------------
# Governance audit log (append-only)
# ---------------------------------------------------------------------------


async def write_governance_audit(
    guild_id: int,
    actor_id: int,
    action: str,
    scope_type: str | None,
    scope_id: int | None,
    subsystem: str | None,
    new_value: dict | None,
    old_value: dict | None = None,
    mutation_id: str | None = None,
) -> None:
    """Append a row to governance_audit_log (fire-and-forget; non-blocking)."""
    await pool.get().execute(
        """INSERT INTO governance_audit_log
               (guild_id, actor_id, action, scope_type, scope_id,
                subsystem, old_value, new_value)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        guild_id,
        actor_id,
        action,
        scope_type,
        scope_id,
        subsystem,
        old_value,  # asyncpg JSONB codec handles encoding
        new_value,  # asyncpg JSONB codec handles encoding
    )
