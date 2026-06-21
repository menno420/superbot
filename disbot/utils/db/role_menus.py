"""Role-menu CRUD (reaction-roles overhaul, PR 1 data layer).

The data layer for modern button/dropdown role menus (migration 078). A
``role_menus`` row is one bot-posted message; ``role_menu_options`` rows pair a
role with an optional emoji/label. The PR 2 builder + ``RoleMenuView`` consume
these primitives; the audited write seam (``services.reaction_role_service``)
wraps the *mutating* helpers so menu edits emit ``audit.action_recorded``.

Co-located with the rest of the role DB layer (``utils/db/roles.py`` owns the
legacy ``reaction_roles`` table); kept in its own module because the menu model
is self-contained and its consumer is the new ``views/roles`` menu surface.
"""

from __future__ import annotations

from utils.db import pool

# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------


async def create_menu(
    guild_id: int,
    channel_id: int,
    *,
    title: str,
    description: str | None,
    style: str = "dropdown",
    mode: str = "normal",
    max_roles: int = 0,
    theme: str = "default",
) -> int:
    """Insert a new (unposted) menu; return its generated ``menu_id``.

    ``message_id`` is left NULL until the menu message is posted — the caller
    sends the message, then calls :func:`set_menu_message`.
    """
    row = await pool.fetchone(
        """INSERT INTO role_menus
               (guild_id, channel_id, title, description, style, mode, max_roles, theme)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           RETURNING menu_id""",
        (guild_id, channel_id, title, description, style, mode, max_roles, theme),
    )
    if row is None:  # pragma: no cover — RETURNING always yields a row on INSERT
        raise RuntimeError("create_menu: INSERT ... RETURNING produced no row")
    return int(row["menu_id"])


async def set_menu_message(menu_id: int, message_id: int) -> None:
    """Record the posted message id for a menu (build → post → store)."""
    await pool.execute(
        "UPDATE role_menus SET message_id=$2 WHERE menu_id=$1",
        (menu_id, message_id),
    )


async def update_menu(
    menu_id: int,
    *,
    title: str,
    description: str | None,
    style: str,
    mode: str,
    max_roles: int,
    theme: str,
) -> None:
    """Edit a menu's presentation/behaviour fields in place (plan §4.6a).

    The caller re-renders and edits the existing message afterward, so the
    posted menu and the row stay in step without a repost.
    """
    await pool.execute(
        """UPDATE role_menus
              SET title=$2, description=$3, style=$4, mode=$5, max_roles=$6, theme=$7
            WHERE menu_id=$1""",
        (menu_id, title, description, style, mode, max_roles, theme),
    )


async def get_menu(menu_id: int) -> dict | None:
    """Return a single menu row, or ``None`` if it no longer exists."""
    return await pool.fetchone(
        "SELECT * FROM role_menus WHERE menu_id=$1",
        (menu_id,),
    )


async def get_menu_by_message(guild_id: int, message_id: int) -> dict | None:
    """Resolve the menu bound to a posted message (the listener/edit path)."""
    return await pool.fetchone(
        "SELECT * FROM role_menus WHERE guild_id=$1 AND message_id=$2",
        (guild_id, message_id),
    )


async def list_menus(guild_id: int) -> list[dict]:
    """All menus configured in a guild (newest first)."""
    return await pool.fetchall(
        "SELECT * FROM role_menus WHERE guild_id=$1 ORDER BY menu_id DESC",
        (guild_id,),
    )


async def delete_menu(menu_id: int) -> None:
    """Delete a menu; its options cascade away (FK ON DELETE CASCADE)."""
    await pool.execute("DELETE FROM role_menus WHERE menu_id=$1", (menu_id,))


# ---------------------------------------------------------------------------
# Options (emoji/label ↔ role pairs)
# ---------------------------------------------------------------------------


async def add_option(
    menu_id: int,
    role_id: int,
    *,
    emoji: str | None = None,
    label: str | None = None,
    position: int = 0,
) -> None:
    """Attach (or update) a role option on a menu."""
    await pool.execute(
        """INSERT INTO role_menu_options (menu_id, role_id, emoji, label, position)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (menu_id, role_id)
             DO UPDATE SET emoji=EXCLUDED.emoji,
                           label=EXCLUDED.label,
                           position=EXCLUDED.position""",
        (menu_id, role_id, emoji, label, position),
    )


async def remove_option(menu_id: int, role_id: int) -> None:
    """Detach a role option from a menu."""
    await pool.execute(
        "DELETE FROM role_menu_options WHERE menu_id=$1 AND role_id=$2",
        (menu_id, role_id),
    )


async def get_options(menu_id: int) -> list[dict]:
    """All role options for a menu, in display order."""
    return await pool.fetchall(
        "SELECT role_id, emoji, label, position FROM role_menu_options "
        "WHERE menu_id=$1 ORDER BY position, role_id",
        (menu_id,),
    )


# ---------------------------------------------------------------------------
# Guild teardown
# ---------------------------------------------------------------------------


async def delete_for_guild(guild_id: int) -> int:
    """Delete every menu (and, by cascade, its options) for a departed guild.

    Returns the number of menus removed. Registered in
    ``guild_lifecycle.teardown`` so the new tables never accumulate per-guild
    rows after the bot leaves (architecture INV-I).
    """
    rows = await pool.fetchall(
        "DELETE FROM role_menus WHERE guild_id=$1 RETURNING menu_id",
        (guild_id,),
    )
    return len(rows)
