"""Resource provisioning audit — DB CRUD primitives (S4.5).

Owns the read/write surface for ``resource_provisioning_audit``
(migration 030).  Inserts are append-only; the audit row is written
by :class:`services.resource_provisioning.ResourceProvisioningPipeline`
after each provisioning attempt — success, decline, or failure.

Unlike :mod:`utils.db.settings_audit`, this module does NOT bundle a
"write target row + audit row in one transaction" primitive: the
"target row" for resource provisioning is the ``subsystem_bindings``
row, which is owned by :class:`services.binding_mutation.BindingMutationPipeline`
and written through its own atomic primitives.  The provisioning
pipeline writes the audit row *after* `BindingMutationPipeline.set_binding`
returns, sharing the same ``mutation_id`` so a join on that column
reconstructs the full provisioning sequence.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.resource_provisioning_audit")


async def insert_audit(
    *,
    mutation_id: str,
    guild_id: int,
    subsystem: str,
    binding_name: str,
    kind: str,
    mode: str,
    outcome: str,
    created: bool,
    resource_id: int | None,
    suggested_name: str | None,
    custom_name: str | None,
    actor_id: int | None,
    actor_type: str,
    mutation_type: str = "provision",
    error_message: str | None = None,
) -> int:
    """Insert a single audit row and return its ``id``.

    Args:
        mutation_id: Caller-generated UUID for cross-pipeline correlation.
        guild_id: Discord guild snowflake.
        subsystem: Owning subsystem name.
        binding_name: ``BindingSpec.name`` the provisioning targeted.
        kind: ``ResourceKind`` value (``channel``/``role``/``category``/
            ``thread``).
        mode: ``use_existing`` or ``create``.
        outcome: ``success`` / ``permission_blocked`` / ``discord_failed``
            / ``binding_failed`` / ``declined``.
        created: ``True`` iff the pipeline created a new Discord resource.
        resource_id: Newly created or reused snowflake, ``None`` for
            ``declined`` / ``permission_blocked`` / ``discord_failed``
            outcomes that never produced a resource.
        suggested_name: ``ProvisioningHint.suggested_name`` value
            (informational; recorded for forensics).
        custom_name: Operator-supplied override, if any.
        actor_id: Discord snowflake of the actor; ``None`` for
            ``actor_type='system'`` writes.
        actor_type: One of ``user`` / ``moderator`` / ``admin`` /
            ``system`` / ``backfill``.
        mutation_type: ``provision`` for v1.
        error_message: Short description for failure outcomes
            (``permission_blocked`` / ``discord_failed`` /
            ``binding_failed``).  ``None`` on ``success`` / ``declined``.

    Returns:
        The newly-inserted row's ``id`` column (BIGSERIAL).
    """
    row = await pool.get().fetchrow(
        """
        INSERT INTO resource_provisioning_audit
            (mutation_id, guild_id, subsystem, binding_name, kind, mode,
             outcome, created, resource_id, suggested_name, custom_name,
             actor_id, actor_type, mutation_type, error_message)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                $12, $13, $14, $15)
        RETURNING id
        """,
        mutation_id,
        guild_id,
        subsystem,
        binding_name,
        kind,
        mode,
        outcome,
        created,
        resource_id,
        suggested_name,
        custom_name,
        actor_id,
        actor_type,
        mutation_type,
        error_message,
    )
    return int(row["id"])


async def count_for_guild(guild_id: int) -> int:
    """Return the audit row count for ``guild_id``."""
    row = await pool.get().fetchrow(
        "SELECT COUNT(*) AS n FROM resource_provisioning_audit WHERE guild_id = $1",
        guild_id,
    )
    return int(row["n"]) if row else 0


async def count_by_outcome(guild_id: int) -> dict[str, int]:
    """Return an ``outcome -> count`` histogram for ``guild_id``."""
    rows = await pool.get().fetch(
        """
        SELECT outcome, COUNT(*)::int AS n
        FROM resource_provisioning_audit
        WHERE guild_id = $1
        GROUP BY outcome
        """,
        guild_id,
    )
    return {r["outcome"]: int(r["n"]) for r in rows}


async def list_recent_for_guild(
    guild_id: int,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` most recent audit rows for ``guild_id``."""
    rows = await pool.get().fetch(
        """
        SELECT id, mutation_id, guild_id, subsystem, binding_name, kind,
               mode, outcome, created, resource_id, suggested_name,
               custom_name, actor_id, actor_type, mutation_type,
               error_message, at
        FROM resource_provisioning_audit
        WHERE guild_id = $1
        ORDER BY at DESC
        LIMIT $2
        """,
        guild_id,
        limit,
    )
    return [dict(r) for r in rows]


__all__ = [
    "count_by_outcome",
    "count_for_guild",
    "insert_audit",
    "list_recent_for_guild",
]
