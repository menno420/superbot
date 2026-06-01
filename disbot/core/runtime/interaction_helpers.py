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
from types import SimpleNamespace
from typing import Any

import discord

logger = logging.getLogger("bot.runtime.interaction")


def help_ctx_shim(interaction: discord.Interaction) -> SimpleNamespace:
    """Build a ctx-like object from an interaction for help-menu view dispatch.

    Cog hub views (e.g. _AdminPanelView, _XpHubView, _ChannelManagerView)
    were written to take a commands.Context.  When the help dropdown opens
    them directly we only have a discord.Interaction.  The four attributes
    those views read from ctx are ``author``, ``guild``, ``channel``, and
    ``bot`` — this shim exposes them.

    Views that need ``ctx.invoke``, ``ctx.send``, ``ctx.prefix``, or
    ``ctx.message`` cannot use this shim and must take their dependencies
    directly instead.
    """
    return SimpleNamespace(
        author=interaction.user,
        guild=interaction.guild,
        channel=interaction.channel,
        bot=interaction.client,
    )


# Discord embed size limits.
# https://discord.com/developers/docs/resources/message#embed-object-embed-limits
_EMBED_TITLE_LIMIT = 256
_EMBED_DESCRIPTION_LIMIT = 4096
_EMBED_FIELD_NAME_LIMIT = 256
_EMBED_FIELD_VALUE_LIMIT = 1024
_EMBED_FOOTER_LIMIT = 2048
_EMBED_AUTHOR_LIMIT = 256
_EMBED_MAX_FIELDS = 25


def _clip(text: str, limit: int) -> str:
    """Truncate ``text`` to ``limit`` chars (ellipsis-terminated)."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def clamp_embed(embed: discord.Embed) -> discord.Embed:
    """Truncate ``embed`` in place to Discord's hard size limits.

    A single over-limit component — most commonly a field ``value``
    over 1024 chars, but also an over-long ``description`` / title /
    footer — makes Discord reject the *entire* message with
    ``400 Invalid Form Body``.  Inside a panel edit that means the edit
    never lands and the UI silently freezes (observed: the diagnostics
    "Database" panel, whose "Unexpected Tables" field overflowed once
    the schema grew past ~50 tables).  Clamping each component to its
    documented maximum degrades an oversized payload to a
    truncated-but-rendered panel instead of a hard failure.

    Only mutates when a value actually exceeds its limit, so well-formed
    embeds pass through unchanged.  Returns the same object for
    call-site convenience.
    """
    if not isinstance(embed, discord.Embed):
        # Defensive: callers should pass a discord.Embed, but never choke
        # on a non-embed (e.g. a test double) — just hand it back.
        return embed
    if embed.title and len(embed.title) > _EMBED_TITLE_LIMIT:
        embed.title = _clip(embed.title, _EMBED_TITLE_LIMIT)
    if embed.description and len(embed.description) > _EMBED_DESCRIPTION_LIMIT:
        embed.description = _clip(embed.description, _EMBED_DESCRIPTION_LIMIT)

    for idx, field in enumerate(embed.fields):
        name = field.name or ""
        value = field.value or ""
        if len(name) > _EMBED_FIELD_NAME_LIMIT or len(value) > _EMBED_FIELD_VALUE_LIMIT:
            embed.set_field_at(
                idx,
                name=_clip(name, _EMBED_FIELD_NAME_LIMIT),
                value=_clip(value, _EMBED_FIELD_VALUE_LIMIT),
                inline=field.inline,
            )

    # Guard the field-count cap too: drop the overflow rather than let
    # the API reject the whole embed.
    while len(embed.fields) > _EMBED_MAX_FIELDS:
        embed.remove_field(_EMBED_MAX_FIELDS)

    footer = embed.footer
    if footer.text and len(footer.text) > _EMBED_FOOTER_LIMIT:
        embed.set_footer(
            text=_clip(footer.text, _EMBED_FOOTER_LIMIT),
            icon_url=footer.icon_url,
        )

    author = embed.author
    if author.name and len(author.name) > _EMBED_AUTHOR_LIMIT:
        embed.set_author(
            name=_clip(author.name, _EMBED_AUTHOR_LIMIT),
            url=author.url,
            icon_url=author.icon_url,
        )
    return embed


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
    file: discord.File | None = None,
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
        kwargs["embed"] = clamp_embed(embed)
    if view is not None:
        kwargs["view"] = view
    if file is not None:
        kwargs["file"] = file
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
        kwargs["embed"] = clamp_embed(embed)
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
