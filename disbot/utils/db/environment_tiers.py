"""Environment tier mapping — DB read primitives (Phase 2d, PR-2).

Owns the read surface for ``environment_tiers``.  The evaluator
(:mod:`core.runtime.feature_flags`) consults this to resolve flags
whose :class:`RolloutPolicy` carries a ``tier_gate``.

State class (per ``docs/architecture.md`` §"State classification"):

  **authoritative persistent** — the DB row is the single source of
  truth for which guilds are owner/canary/beta/production.

Public surface:

* :func:`get_tier` — return the guild's tier string, or ``None``.
* :func:`list_for_diagnostics` — read every row for ``!platform flags``.
* :func:`delete_for_guild` — single-row delete called from
  ``guild_lifecycle.teardown``.

Writes ship with :class:`services.rollout_mutation.RolloutMutationPipeline`
in PR-3.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.environment_tiers")


async def get_tier(guild_id: int) -> str | None:
    """Return the tier string for ``guild_id``, or ``None`` when unset.

    Missing row → caller treats the guild as ``'production'`` (most
    restrictive default).  The evaluator centralises this defaulting
    so DB-layer callers do not have to know the policy.
    """
    row = await pool.get().fetchrow(
        "SELECT tier FROM environment_tiers WHERE guild_id = $1",
        guild_id,
    )
    return row["tier"] if row else None


async def list_for_diagnostics() -> list[dict[str, Any]]:
    """Return every row, sorted by tier then guild_id.

    Used by the diagnostics provider; not on any hot path.
    """
    rows = await pool.get().fetch(
        """
        SELECT guild_id, tier, set_by, set_at
        FROM environment_tiers
        ORDER BY tier, guild_id
        """,
    )
    return [dict(r) for r in rows]


async def upsert_with_audit(
    *,
    guild_id: int,
    tier: str,
    actor_id: int | None,
    actor_type: str,
    mutation_id: str,
    prev_tier: str | None,
) -> None:
    """Atomic: upsert environment_tiers + write feature_flag_audit row.

    The audit row uses ``flag_name='__environment_tier__'`` so the
    single audit table covers all three Phase 2d event sources
    (state, rollout, tier).  Caller is the RolloutMutationPipeline.
    """
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            """
            INSERT INTO environment_tiers (guild_id, tier, set_by, set_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (guild_id) DO UPDATE SET
                tier = EXCLUDED.tier,
                set_by = EXCLUDED.set_by,
                set_at = NOW()
            """,
            guild_id,
            tier,
            actor_id,
        )
        await conn.execute(
            """
            INSERT INTO feature_flag_audit
                (mutation_id, flag_name, scope, guild_id,
                 prev_tier, new_tier,
                 actor_id, actor_type, mutation_type)
            VALUES ($1, '__environment_tier__', 'guild', $2, $3, $4,
                    $5, $6, 'set_tier')
            """,
            mutation_id,
            guild_id,
            prev_tier,
            tier,
            actor_id,
            actor_type,
        )


async def delete_for_guild(guild_id: int) -> int:
    """Delete the environment_tier row for ``guild_id``.

    Returns the row count parsed from asyncpg's ``"DELETE N"`` status;
    ``0`` on parse failure.  Called from ``guild_lifecycle.teardown``
    so a re-invited guild falls back to PRODUCTION until reassigned.
    """
    result = await pool.get().execute(
        "DELETE FROM environment_tiers WHERE guild_id = $1",
        guild_id,
    )
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


__all__ = [
    "delete_for_guild",
    "get_tier",
    "list_for_diagnostics",
    "upsert_with_audit",
]
