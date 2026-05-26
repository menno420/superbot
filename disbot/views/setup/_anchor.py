"""Thin renderer for the setup workspace anchor.

Two public helpers:

* :func:`render_setup_state` — replace the canonical setup anchor with
  ``embed`` + ``view`` (state replacement). Used by hub, final review,
  status snapshot, depth, reset, and delegation flows so admins always
  see the current setup state in a durable, deletable, sharable
  ``#superbot-setup`` message rather than a per-user ephemeral.
* :func:`push_setup_notice` — append a one-shot durable notice into
  the workspace channel (event log). Used for "Apply Recommended
  succeeded", "section X failed", and other post-event records that
  must not overwrite anchor state.

Both helpers fail safely: on any Discord error (missing perms, anchor
not fetchable, channel deleted between calls) they swallow the
exception, log at WARNING, and return ``False``. Callers check the
return value and surface a controlled ephemeral fallback.

This module is a *thin* renderer per the implementation guardrails:

* Inputs are ``discord.Guild`` + plain embed/view — no wizard internals.
* It imports only from :mod:`services.setup_session` (channel/message
  id storage) and :mod:`services.setup_channel` (channel ensure).
* It does not import from ``views/setup/wizard.py`` or
  ``views/setup/hub.py`` and owns no setup state.

This split (state replacement vs. event notice) is deliberate. The
anchor must remain the source of truth for "where is setup right
now"; notices accumulate around it as an event trail.
"""

from __future__ import annotations

import logging

import discord

from services import setup_channel, setup_session

logger = logging.getLogger("bot.views.setup.anchor")


async def render_setup_state(
    guild: discord.Guild,
    *,
    embed: discord.Embed,
    view: discord.ui.View | None = None,
) -> bool:
    """Replace the setup workspace anchor with ``embed`` + ``view``.

    Resolves the workspace channel via
    :func:`services.setup_channel.ensure_setup_channel` and the anchor
    message id via the session's ``setup_message_id``. Edits in place
    when the anchor is still fetchable; otherwise posts a new message
    and updates the persisted id so subsequent renders reuse it.

    Returns ``True`` on success, ``False`` when the channel is
    unavailable or every Discord write failed. Never raises — callers
    rely on the boolean to decide whether to surface an ephemeral
    fallback to the user.
    """
    try:
        session = await setup_session.resume_session(guild.id)
    except Exception:
        logger.exception(
            "render_setup_state: resume_session failed (guild=%d)",
            guild.id,
        )
        session = None

    try:
        channel, _was_created = await setup_channel.ensure_setup_channel(
            guild,
            existing_channel_id=(
                session.setup_channel_id if session is not None else None
            ),
            session=session,
        )
    except Exception:
        logger.exception(
            "render_setup_state: ensure_setup_channel failed (guild=%d)",
            guild.id,
        )
        return False
    if channel is None:
        logger.warning(
            "render_setup_state: no workspace channel resolvable (guild=%d)",
            guild.id,
        )
        return False

    if session is None or session.setup_channel_id != channel.id:
        try:
            await setup_session.set_setup_channel_id(guild.id, channel.id)
        except Exception:
            logger.exception(
                "render_setup_state: set_setup_channel_id failed (guild=%d)",
                guild.id,
            )

    existing_id = session.setup_message_id if session is not None else None
    if existing_id is not None:
        try:
            existing_msg = await channel.fetch_message(existing_id)
            await existing_msg.edit(embed=embed, view=view)
            return True
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            logger.info(
                "render_setup_state: anchor %s not fetchable; reposting (guild=%d)",
                existing_id,
                guild.id,
            )
            try:
                await setup_session.set_setup_message_id(guild.id, None)
            except Exception:
                logger.exception(
                    "render_setup_state: clearing stale message id failed",
                )

    try:
        message = await channel.send(embed=embed, view=view)
    except discord.HTTPException:
        logger.exception(
            "render_setup_state: failed to post anchor (guild=%d)",
            guild.id,
        )
        return False

    try:
        await setup_session.set_setup_message_id(guild.id, message.id)
    except Exception:
        logger.exception(
            "render_setup_state: persist message id failed (guild=%d)",
            guild.id,
        )

    return True


async def push_setup_notice(
    guild: discord.Guild,
    *,
    embed: discord.Embed,
) -> bool:
    """Append a one-shot durable notice into the workspace channel.

    Resolves the workspace channel only — does not touch the anchor
    message id. Used for event records (e.g. "Apply Recommended
    succeeded", "section X failed") that must not overwrite canonical
    state.

    Returns ``True`` on success, ``False`` on any failure.
    """
    try:
        session = await setup_session.resume_session(guild.id)
    except Exception:
        logger.exception(
            "push_setup_notice: resume_session failed (guild=%d)",
            guild.id,
        )
        session = None

    try:
        channel, _was_created = await setup_channel.ensure_setup_channel(
            guild,
            existing_channel_id=(
                session.setup_channel_id if session is not None else None
            ),
            session=session,
        )
    except Exception:
        logger.exception(
            "push_setup_notice: ensure_setup_channel failed (guild=%d)",
            guild.id,
        )
        return False
    if channel is None:
        return False

    try:
        await channel.send(embed=embed)
        return True
    except discord.HTTPException:
        logger.exception(
            "push_setup_notice: send failed (guild=%d)",
            guild.id,
        )
        return False


__all__ = [
    "push_setup_notice",
    "render_setup_state",
]
