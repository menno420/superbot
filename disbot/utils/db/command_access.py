"""Command-access policy DB primitives.

Per-guild policy controlling where normal prefix + slash commands are
allowed (PR-1 of the command-access onboarding fix).  Reads return
``None`` when no row exists; the resolver layer
(:mod:`core.runtime.command_access`) treats the absence of a row as
the safe default (``all_channels``).

Two tables back this module:

* ``guild_command_access_policy``        — one row per guild, mode only
* ``guild_command_access_channels``      — child rows for selected
                                            channels (FK with cascade)

Both tables ship in migration ``050_guild_command_access.sql``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.command_access")


KNOWN_MODES: frozenset[str] = frozenset(
    {
        "all_channels",
        "selected_channels",
        "disabled_except_bootstrap",
    },
)


def _validate_mode(mode: str) -> None:
    if mode not in KNOWN_MODES:
        raise ValueError(
            f"mode must be one of {sorted(KNOWN_MODES)}, got {mode!r}",
        )


# ---------------------------------------------------------------------------
# Policy row (mode)
# ---------------------------------------------------------------------------


async def get_policy(guild_id: int) -> dict[str, Any] | None:
    """Return the policy row for ``guild_id`` or ``None`` when unset.

    Absence of a row is the canonical "unconfigured" signal — callers
    must apply their own default rather than synthesising a row here.
    """
    row = await pool.get().fetchrow(
        """
        SELECT mode, updated_by, updated_at, created_at
          FROM guild_command_access_policy
         WHERE guild_id = $1
        """,
        guild_id,
    )
    return dict(row) if row else None


async def set_mode(
    guild_id: int,
    mode: str,
    updated_by: int | None,
) -> None:
    """Upsert the mode for ``guild_id``.

    Preserves ``created_at`` on update; only ``mode``, ``updated_by``,
    and ``updated_at`` move on conflict.
    """
    _validate_mode(mode)
    await pool.get().execute(
        """
        INSERT INTO guild_command_access_policy
            (guild_id, mode, updated_by)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id)
        DO UPDATE SET
            mode       = EXCLUDED.mode,
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW()
        """,
        guild_id,
        mode,
        updated_by,
    )


# ---------------------------------------------------------------------------
# Allowed-channel rows
# ---------------------------------------------------------------------------


async def list_allowed_channels(guild_id: int) -> list[int]:
    """Return the allowed channel ids for ``guild_id`` in stable order.

    Stable ordering keeps UI panes deterministic between renders and
    makes diff-based audit comparisons trivial.
    """
    rows = await pool.get().fetch(
        """
        SELECT channel_id
          FROM guild_command_access_channels
         WHERE guild_id = $1
         ORDER BY channel_id
        """,
        guild_id,
    )
    return [int(r["channel_id"]) for r in rows]


async def add_allowed_channel(
    guild_id: int,
    channel_id: int,
    created_by: int | None,
) -> None:
    """Insert a single allowed channel; idempotent on (guild, channel).

    A policy row must already exist (FK constraint).  The service
    layer is responsible for ensuring ``set_mode`` ran first.
    """
    await pool.get().execute(
        """
        INSERT INTO guild_command_access_channels
            (guild_id, channel_id, created_by)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, channel_id) DO NOTHING
        """,
        guild_id,
        channel_id,
        created_by,
    )


async def remove_allowed_channel(guild_id: int, channel_id: int) -> None:
    """Remove a single allowed channel; no-op when absent."""
    await pool.get().execute(
        """
        DELETE FROM guild_command_access_channels
         WHERE guild_id = $1 AND channel_id = $2
        """,
        guild_id,
        channel_id,
    )


async def replace_allowed_channels(
    guild_id: int,
    channel_ids: Iterable[int],
    created_by: int | None,
) -> None:
    """Atomically replace the allowed-channel set for ``guild_id``.

    Wraps the delete + bulk-insert in a single transaction so a
    concurrent reader never observes a half-applied list.  Dedupes the
    input so callers can pass a list directly without pre-processing.
    """
    desired = sorted({int(cid) for cid in channel_ids})
    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            "DELETE FROM guild_command_access_channels WHERE guild_id = $1",
            guild_id,
        )
        if desired:
            await conn.executemany(
                """
                INSERT INTO guild_command_access_channels
                    (guild_id, channel_id, created_by)
                VALUES ($1, $2, $3)
                """,
                [(guild_id, cid, created_by) for cid in desired],
            )


# ---------------------------------------------------------------------------
# Guild teardown
# ---------------------------------------------------------------------------


async def forget_guild(guild_id: int) -> None:
    """Drop every command-access row for ``guild_id``.

    Called by ``guild_lifecycle.teardown`` when the bot is kicked or
    leaves a guild.  The CASCADE on ``guild_command_access_channels``
    means deleting the policy row sweeps its children, so a single
    delete is sufficient.
    """
    await pool.get().execute(
        "DELETE FROM guild_command_access_policy WHERE guild_id = $1",
        guild_id,
    )


__all__ = [
    "KNOWN_MODES",
    "add_allowed_channel",
    "forget_guild",
    "get_policy",
    "list_allowed_channels",
    "remove_allowed_channel",
    "replace_allowed_channels",
    "set_mode",
]
