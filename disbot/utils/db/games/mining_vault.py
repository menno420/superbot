"""mining_vault CRUD — a player's safe stash, separate from the active inventory.

Brainstorm §7.5 "Vault (inventory cap + safe stash)": deposited items live here,
out of ``mining_inventory``, in a protected store.  The shape mirrors
``mining_inventory`` exactly (guild-scoped; ``user_id`` ``TEXT`` to match its
legacy column type; one row per item; quantity clamped ``>= 0``) so a deposit /
withdraw is a symmetric pair of inventory deltas (``-qty`` on one table,
``+qty`` on the other).

RS02 (Q-0071): the write primitive takes an optional ``conn`` so
``services/mining_workflow.py`` can debit the inventory and credit the vault
inside ONE transaction — neither leg ever commits alone (the move can never
duplicate or vanish the items).  Reads (``get_vault``) stay free for panels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

_UPSERT_VAULT_SQL = """INSERT INTO mining_vault (user_id, guild_id, item_name, quantity)
           VALUES ($1, $2, $3, GREATEST(0, $4))
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET quantity = GREATEST(0, mining_vault.quantity + $4)"""


async def get_vault(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """The player's vault contents for a guild — ``{item_name: quantity}``.

    Zero-quantity rows (a fully-withdrawn item) are filtered out so callers see
    only what is actually stored.
    """
    rows = await pool.fetchall(
        "SELECT item_name, quantity FROM mining_vault WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["item_name"]: r["quantity"] for r in rows if r["quantity"] > 0}


async def update_vault_item(
    user_id: str,
    guild_id: int,
    item_name: str,
    delta: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Add or subtract *delta* of *item_name* in the vault for *(user, guild)*.

    Clamps to 0 on both INSERT and UPDATE (mirrors
    :func:`utils.db.games.mining.update_mining_item`).  With *conn* given the
    upsert runs on that connection so the caller's transaction owns commit.
    """
    await pool.execute(
        _UPSERT_VAULT_SQL,
        (user_id, guild_id, item_name, delta),
        conn=conn,
    )
