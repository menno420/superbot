"""Discord message anchor persistence.

An anchor is a (channel_id, message_id) pair stored in the DB that lets the
runtime platform find and edit an existing panel message instead of sending a
new one on every command invocation.

The anchor table enforces one row per (user, channel, subsystem) via a UNIQUE
constraint.  Stale anchors (message deleted) are marked and pruned by GC.

Public surface:
    get(user_id, channel_id, subsystem)           → dict | None
    upsert(user_id, guild_id, channel_id, subsystem, message_id) → dict
    get_by_message_id(message_id)                  → dict | None
    mark_stale(anchor_id)                          → None
    restore_anchors(bot)                           → None  (startup recovery)
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from services import metrics
from utils import db

logger = logging.getLogger("bot.runtime.anchors")

# on_ready fires on every Discord gateway reconnect, not just at process
# start.  Without this guard restore_anchors() would call bot.add_view()
# again for every anchor each reconnect, leaving duplicate view instances
# bound to the same message — discord.py would then dispatch the
# callback once per registered instance.  Guard makes restore a no-op
# on second-and-subsequent calls; reset() is available for tests and
# for the (rare) case where an admin really wants a fresh restore.
_RESTORED_ONCE: bool = False

# Last restoration summary, exposed for admin diagnostics.
# Cleared by reset_restoration_state.
_LAST_RESTORE_STATS: dict[str, int] = {
    "anchors_seen": 0,
    "restored": 0,
    "view_missing": 0,
    "stale": 0,
}


def reset_restoration_state() -> None:
    """Clear the once-only guard so the next restore_anchors() runs again.

    Intended for tests and for an explicit admin command that wants to
    force a fresh restoration pass.  Normal runtime never needs this.
    """
    global _RESTORED_ONCE
    _RESTORED_ONCE = False
    _LAST_RESTORE_STATS.update(
        anchors_seen=0,
        restored=0,
        view_missing=0,
        stale=0,
    )


def last_restore_stats() -> dict[str, int]:
    """Return a snapshot of the most recent ``restore_anchors`` outcome."""
    return dict(_LAST_RESTORE_STATS)


async def get(user_id: int, channel_id: int, subsystem: str) -> dict | None:
    """Return the active anchor for (user, channel, subsystem), or None."""
    return await db.get_panel_anchor(user_id, channel_id, subsystem)


async def upsert(
    user_id: int,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    message_id: int,
) -> dict:
    """Create or replace the anchor, resetting is_stale on conflict."""
    row = await db.upsert_panel_anchor(
        user_id,
        guild_id,
        channel_id,
        subsystem,
        message_id,
    )
    logger.debug(
        "Anchor upserted | subsystem=%s | user=%d | msg=%d",
        subsystem,
        user_id,
        message_id,
    )
    return row


async def get_by_message_id(message_id: int) -> dict | None:
    """Return the anchor for a specific Discord message, or None."""
    return await db.get_panel_anchor_by_message(message_id)


async def mark_stale(anchor_id: str) -> None:
    """Mark an anchor as stale after detecting the Discord message was deleted."""
    await db.mark_panel_anchor_stale(anchor_id)
    logger.debug("Anchor marked stale: %s", anchor_id)


async def restore_anchors(bot: commands.Bot) -> None:
    """Re-attach persistent views to all anchored messages at bot startup.

    Fetches every non-stale anchor from DB and calls bot.add_view() with a
    fresh view instance so button interactions survive a bot restart.
    Messages that no longer exist are marked stale.

    Idempotent: subsequent calls (e.g. when on_ready re-fires after a
    Discord gateway reconnect) are no-ops.  Use ``reset_restoration_state()``
    to force a re-run if needed.
    """
    global _RESTORED_ONCE
    if _RESTORED_ONCE:
        logger.debug(
            "restore_anchors() called again — skipping (already restored).",
        )
        return
    _RESTORED_ONCE = True
    from core.runtime.persistent_views import get_view_class

    anchors = await db.get_all_active_panel_anchors()
    restored = 0
    stale = 0
    view_missing = 0

    for anchor in anchors:
        subsystem = anchor["subsystem"]
        # Help is invoke-and-see, not a stable hub (see help_cog.help_command).
        # Restoring it would either re-attach a HelpPanelView with empty
        # _visible/_page state or require schema work to persist that state.
        # Neither matches the lifecycle — drop the anchor so the user's next
        # !help creates a clean panel via panel_manager.
        if subsystem == "help":
            await mark_stale(str(anchor["anchor_id"]))
            stale += 1
            metrics.anchor_restore_total.labels(
                subsystem=subsystem,
                result="skipped_help",
            ).inc()
            continue
        view_cls = get_view_class(subsystem)
        if view_cls is None:
            # Cog with PersistentView didn't register — leftover anchor.
            # Surface via metric so operators can spot orphaned anchors.
            metrics.anchor_restore_total.labels(
                subsystem=subsystem,
                result="view_missing",
            ).inc()
            view_missing += 1
            logger.warning(
                "Anchor %s for subsystem=%r has no registered PersistentView "
                "class — panel will be unresponsive until the cog loads.",
                anchor["anchor_id"],
                subsystem,
            )
            continue
        try:
            view = view_cls()
            bot.add_view(view, message_id=anchor["message_id"])
            restored += 1
            metrics.anchor_restore_total.labels(
                subsystem=subsystem,
                result="ok",
            ).inc()
        except Exception as exc:
            logger.warning(
                "Could not restore anchor %s (msg=%d subsystem=%s): %s",
                anchor["anchor_id"],
                anchor["message_id"],
                subsystem,
                exc,
            )
            await mark_stale(str(anchor["anchor_id"]))
            stale += 1
            metrics.anchor_restore_total.labels(
                subsystem=subsystem,
                result="restore_failed",
            ).inc()

    _LAST_RESTORE_STATS.update(
        anchors_seen=len(anchors),
        restored=restored,
        view_missing=view_missing,
        stale=stale,
    )
    logger.info(
        "Anchor recovery complete — %d restored, %d view-missing, %d marked stale",
        restored,
        view_missing,
        stale,
    )


async def try_fetch_message(
    bot: commands.Bot,
    channel_id: int,
    message_id: int,
) -> discord.Message | None:
    """Fetch a Discord message, returning None if it no longer exists."""
    channel = bot.get_channel(channel_id)
    if channel is None or not isinstance(channel, discord.abc.Messageable):
        return None
    try:
        return await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None
