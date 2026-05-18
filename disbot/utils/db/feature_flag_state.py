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
    "get_global_override",
    "get_guild_override",
    "list_global_overrides",
    "list_guild_overrides",
]
