"""Interaction-response helpers for cog button/modal callbacks.

Discord interaction tokens expire 3 seconds after the user clicks.  Any
handler that performs DB I/O, governance resolution, or substantial
rendering before responding risks the user seeing "Interaction Failed".

The standard discord.py pattern is:

    await interaction.response.defer()         # within 3 s
    # ... slow work ...
    await interaction.followup.send(...)       # or edit_original_response

The helpers in this module make that pattern safe and consistent:

- :func:`safe_defer` defers idempotently — if the response is already
  done (an earlier ephemeral reply, for example) defer becomes a no-op
  rather than raising ``InteractionResponded``.
- :func:`safe_followup` chooses ``followup.send`` vs
  ``response.send_message`` based on whether ``defer`` has been called.
- :func:`safe_edit` edits the panel's anchor message regardless of
  whether the handler deferred first.

All three swallow the narrow set of recoverable errors (token expiry,
already-responded) that arise from races (e.g. user dismissed the modal
mid-handler), log them at WARNING, and never raise.  Callers do not
need to wrap their interaction work in try/except blocks for these
specific failure modes.

This module addresses CRIT-2 (no defer in I/O-heavy callbacks) from
the platform-hardening plan.  Adoption across cogs lands in F5.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.runtime.interaction")


async def safe_defer(
    interaction: discord.Interaction,
    *,
    ephemeral: bool = False,
    thinking: bool = False,
) -> bool:
    """Defer the interaction response within the 3-second window.

    Args:
        interaction: the Discord interaction to defer.
        ephemeral: whether the eventual followup should be ephemeral.
        thinking: show the "Bot is thinking..." indicator while deferred.

    Returns:
        ``True`` if the interaction is deferred (or was already done);
        ``False`` if deferral failed (token expired, HTTP error). A
        ``False`` return means subsequent followup attempts will also
        fail — the caller should bail out of the handler.
    """
    if interaction.response.is_done():
        return True
    try:
        await interaction.response.defer(ephemeral=ephemeral, thinking=thinking)
        return True
    except discord.NotFound:
        # 10062 Unknown Interaction — token expired before defer reached Discord.
        logger.warning(
            "safe_defer: interaction token expired (user=%s)",
            getattr(interaction.user, "id", None),
        )
        return False
    except discord.HTTPException as exc:
        logger.warning("safe_defer: HTTP error %s", exc)
        return False


async def safe_followup(
    interaction: discord.Interaction,
    content: str | None = None,
    *,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool = False,
) -> discord.Message | None:
    """Send a response message regardless of deferred state.

    If the interaction has already been responded to or deferred this
    routes through ``interaction.followup.send``; otherwise it uses
    ``interaction.response.send_message`` and fetches the original
    message for the return value.

    Returns the sent message, or ``None`` if delivery failed.
    """
    # dict[str, Any] so **kwargs unpacks into the typed Discord signatures
    # (followup.send / response.send_message / response.edit_message) without
    # mypy demanding the exact type of each value.
    kwargs: dict[str, Any] = {}
    if content is not None:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view
    if ephemeral:
        kwargs["ephemeral"] = True

    try:
        if interaction.response.is_done():
            return await interaction.followup.send(**kwargs)
        await interaction.response.send_message(**kwargs)
        try:
            return await interaction.original_response()
        except discord.HTTPException:
            return None
    except discord.NotFound:
        logger.warning(
            "safe_followup: interaction token expired (user=%s)",
            getattr(interaction.user, "id", None),
        )
        return None
    except discord.HTTPException as exc:
        logger.warning("safe_followup: HTTP error %s", exc)
        return None


async def safe_edit(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
) -> bool:
    """Edit the original message regardless of deferred state.

    If the interaction has been deferred (no response sent yet) this
    uses ``followup.edit_original_response``; otherwise it uses
    ``response.edit_message`` (which only works on component
    interactions before the first response).

    Returns ``True`` on success, ``False`` if the edit failed.
    """
    # dict[str, Any] so **kwargs unpacks into the typed Discord signatures
    # (followup.send / response.send_message / response.edit_message) without
    # mypy demanding the exact type of each value.
    kwargs: dict[str, Any] = {}
    if content is not None:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view

    try:
        if interaction.response.is_done():
            if interaction.message is not None:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    **kwargs,
                )
            else:
                await interaction.edit_original_response(**kwargs)
        else:
            await interaction.response.edit_message(**kwargs)
        return True
    except discord.NotFound:
        logger.warning(
            "safe_edit: message or interaction missing (user=%s)",
            getattr(interaction.user, "id", None),
        )
        return False
    except discord.HTTPException as exc:
        logger.warning("safe_edit: HTTP error %s", exc)
        return False
