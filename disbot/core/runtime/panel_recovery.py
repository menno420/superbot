"""Panel-recovery helper — Phase S2.3.

State class: stateless utility (no module-level mutable state).

Sub-panels frequently need to "return to the parent panel" after
applying their action.  The naive pattern — edit the parent's message
in place — fails silently when:

  * the parent message was deleted (mod cleanup, channel purge),
  * the bot lost permission to edit it,
  * the channel itself was deleted between action start and restore.

The original ``views/channels/{restrict,delete,create}_panel.py``
code path was::

    try:
        await self.manager_message.edit(embed=..., view=...)
    except Exception:
        pass

which left the user staring at the sub-panel's "Returning to the
management panel…" footer with no actual panel restored.

This helper centralises the recovery so every panel system uses the
same discipline:

  1. Try to edit the parent message in place (the happy path).
  2. On ``discord.NotFound`` (parent deleted) → send a fresh panel as
     a new message in the same channel.
  3. On any other ``discord.HTTPException`` → log with context.

No silent ``except Exception: pass`` anywhere.

Public surface:
    restore_parent_or_send_fresh(*, parent_message, channel, embed, view)
        → discord.Message | None  (the message that now hosts the panel)
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.runtime.panel_recovery")


async def restore_parent_or_send_fresh(
    *,
    parent_message: discord.Message | None,
    channel: discord.abc.Messageable | None = None,
    embed: discord.Embed,
    view: discord.ui.View,
) -> discord.Message | None:
    """Edit the parent panel in place, or send a fresh panel on failure.

    Args:
        parent_message: The original parent-panel message to edit.  May
            be None if the parent was never bound (treated as
            "send fresh" directly into ``channel``).
        channel: Fallback channel to send a fresh panel into when the
            parent is missing or unrecoverable.  If omitted, derived
            from ``parent_message.channel`` when possible.
        embed: The parent panel's new embed.
        view: The parent panel's fresh view instance.

    Returns:
        The ``discord.Message`` that now hosts the panel (either the
        edited parent or the newly-sent fresh one), or ``None`` if
        recovery completely failed (e.g. no parent + no channel, or
        the channel itself rejects sends).

    The caller is responsible for binding ``view.message`` to the
    returned Message if the view's ``on_timeout`` needs the reference.
    """
    fallback_channel = channel
    if fallback_channel is None and parent_message is not None:
        fallback_channel = parent_message.channel

    if parent_message is None:
        return await _send_fresh(fallback_channel, embed, view)

    try:
        await parent_message.edit(embed=embed, view=view)
    except discord.NotFound:
        logger.debug(
            "panel_recovery: parent message %s was deleted — sending fresh",
            parent_message.id,
        )
        return await _send_fresh(fallback_channel, embed, view)
    except discord.Forbidden as exc:
        logger.warning(
            "panel_recovery: cannot edit parent message %s (Forbidden): %s",
            parent_message.id,
            exc,
        )
        return None
    except discord.HTTPException as exc:
        logger.error(
            "panel_recovery: HTTPException editing parent message %s: %s",
            parent_message.id,
            exc,
            exc_info=True,
        )
        return None
    return parent_message


async def _send_fresh(
    channel: discord.abc.Messageable | None,
    embed: discord.Embed,
    view: discord.ui.View,
) -> discord.Message | None:
    if channel is None:
        logger.warning("panel_recovery: no fallback channel — cannot recover")
        return None
    try:
        return await channel.send(embed=embed, view=view)
    except discord.Forbidden as exc:
        logger.warning(
            "panel_recovery: cannot send fresh panel (Forbidden): %s",
            exc,
        )
        return None
    except discord.HTTPException as exc:
        logger.error(
            "panel_recovery: send fresh panel failed: %s",
            exc,
            exc_info=True,
        )
        return None
