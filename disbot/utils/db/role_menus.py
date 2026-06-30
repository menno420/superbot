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

from collections.abc import Sequence

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
    card_template: str | None = None,
    card_text: str | None = None,
    show_counts: bool = False,
) -> int:
    """Insert a new (unposted) menu; return its generated ``menu_id``.

    ``message_id`` is left NULL until the menu message is posted — the caller
    sends the message, then calls :func:`set_menu_message`. ``card_template`` /
    ``card_text`` (migration 089) are NULL unless the menu carries a banner card.
    ``show_counts`` (migration 103) toggles the member-facing live sign-up counter.
    """
    row = await pool.fetchone(
        """INSERT INTO role_menus
               (guild_id, channel_id, title, description, style, mode, max_roles,
                theme, card_template, card_text, show_counts)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
           RETURNING menu_id""",
        (
            guild_id,
            channel_id,
            title,
            description,
            style,
            mode,
            max_roles,
            theme,
            card_template,
            card_text,
            show_counts,
        ),
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


async def set_menu_location(menu_id: int, channel_id: int, message_id: int) -> None:
    """Record a menu's posted channel + message together (the repost/move flow).

    Reposting a saved menu sends a fresh message — possibly in a different
    channel — so both columns move in step (``set_menu_message`` only updates the
    message id, which would leave ``channel_id`` pointing at the old location).
    """
    await pool.execute(
        "UPDATE role_menus SET channel_id=$2, message_id=$3 WHERE menu_id=$1",
        (menu_id, channel_id, message_id),
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
    card_template: str | None = None,
    card_text: str | None = None,
    show_counts: bool = False,
) -> None:
    """Edit a menu's presentation/behaviour fields in place (plan §4.6a).

    The caller re-renders and edits the existing message afterward, so the
    posted menu and the row stay in step without a repost. ``card_template`` /
    ``card_text`` are overwritten too (``None`` clears the banner card).
    ``show_counts`` toggles the live sign-up counter (migration 103).
    """
    await pool.execute(
        """UPDATE role_menus
              SET title=$2, description=$3, style=$4, mode=$5, max_roles=$6, theme=$7,
                  card_template=$8, card_text=$9, show_counts=$10
            WHERE menu_id=$1""",
        (
            menu_id,
            title,
            description,
            style,
            mode,
            max_roles,
            theme,
            card_template,
            card_text,
            show_counts,
        ),
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


async def replace_options(
    menu_id: int,
    options: Sequence[tuple[int, str | None, str | None]],
) -> None:
    """Replace a menu's full option list in one transaction (PR 2 builder).

    ``options`` is an ordered sequence of ``(role_id, emoji, label)`` — the index
    becomes the stored ``position``, so the caller controls display order by
    ordering the sequence. The builder always re-sends the whole list on
    create/edit, so a transactional delete + bulk-insert is simpler and safer
    than diffing against :func:`add_option` / :func:`remove_option` (and a
    concurrent reader never sees a half-applied list). Mirrors
    ``command_access.set_channels``.
    """
    deduped: list[tuple[int, str | None, str | None]] = []
    seen: set[int] = set()
    for role_id, emoji, label in options:
        rid = int(role_id)
        if rid in seen:
            continue
        seen.add(rid)
        deduped.append((rid, emoji, label))

    async with pool.get().acquire() as conn, conn.transaction():
        await conn.execute(
            "DELETE FROM role_menu_options WHERE menu_id=$1",
            menu_id,
        )
        if deduped:
            await conn.executemany(
                """INSERT INTO role_menu_options
                       (menu_id, role_id, emoji, label, position)
                   VALUES ($1, $2, $3, $4, $5)""",
                [
                    (menu_id, rid, emoji, label, pos)
                    for pos, (rid, emoji, label) in enumerate(deduped)
                ],
            )


async def list_posted_menus() -> list[dict]:
    """Every menu that has been posted (``message_id`` set), across all guilds.

    Used by the boot re-attach loop to re-bind a persistent view to each live
    menu message (PR 2).
    """
    return await pool.fetchall(
        "SELECT * FROM role_menus WHERE message_id IS NOT NULL",
    )


# ---------------------------------------------------------------------------
# Pickup analytics (PR 5, plan §10) — aggregate (guild, role) counters
# ---------------------------------------------------------------------------


async def record_pickup(guild_id: int, role_id: int) -> None:
    """Tally one self-assignment of ``role_id`` (UPSERT increment)."""
    await pool.execute(
        """INSERT INTO role_menu_pickup_stats
               (guild_id, role_id, picked, last_picked_at)
           VALUES ($1, $2, 1, now())
           ON CONFLICT (guild_id, role_id) DO UPDATE
             SET picked = role_menu_pickup_stats.picked + 1,
                 last_picked_at = now()""",
        (guild_id, role_id),
    )


async def record_removal(guild_id: int, role_id: int) -> None:
    """Tally one self-removal of ``role_id`` (UPSERT increment)."""
    await pool.execute(
        """INSERT INTO role_menu_pickup_stats (guild_id, role_id, removed)
           VALUES ($1, $2, 1)
           ON CONFLICT (guild_id, role_id) DO UPDATE
             SET removed = role_menu_pickup_stats.removed + 1""",
        (guild_id, role_id),
    )


async def get_pickup_stats(guild_id: int) -> list[dict]:
    """Per-role pickup/removal tallies for a guild, most-picked first."""
    return await pool.fetchall(
        "SELECT role_id, picked, removed, last_picked_at "
        "FROM role_menu_pickup_stats WHERE guild_id=$1 "
        "ORDER BY picked DESC, removed DESC",
        (guild_id,),
    )


async def delete_pickup_stats_for_guild(guild_id: int) -> int:
    """Delete every pickup-stat row for a departed guild (teardown)."""
    rows = await pool.fetchall(
        "DELETE FROM role_menu_pickup_stats WHERE guild_id=$1 RETURNING role_id",
        (guild_id,),
    )
    return len(rows)


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
