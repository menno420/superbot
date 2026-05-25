"""Workspace-anchor entry points for ``/setup`` and ``!setup``.

Phase 3 of the setup-wizard plan.  Routes both slash and prefix
invocations through the same flow:

1. Resolve / start the session row.
2. For owners + delegated admins → open the linear wizard via
   :func:`views.setup.wizard.open_setup_workspace` (posts / edits one
   anchor message in ``#superbot-setup``), then reply transiently in
   the invoking channel with a jump link.
3. For plain administrators → render the read-only readiness embed
   (mirror of the legacy ``_resolve_hub_entry`` "readiness" mode).
4. For everyone else → deny.

Extracted from :mod:`cogs.setup_cog` to keep the cog file under the
S4.6 800-LOC ceiling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from services import setup_access, setup_session
from views.setup.wizard import jump_link, open_setup_workspace

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.cogs.setup.wizard_entry")


async def open_wizard_from_slash(interaction: discord.Interaction) -> None:
    """Slash-command entry point.  Ephemeral throughout."""
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "Use `/setup` from inside the server.",
            ephemeral=True,
        )
        return

    session = await _resume_or_start(guild, owner_id=member.id)
    if setup_access.can_apply_setup(member, session):
        await _open_wizard_workspace_for_slash(interaction, guild, member, session)
        return

    if setup_access.is_setup_admin(member, session):
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        if embed is None:
            await interaction.response.send_message(
                "Could not build the readiness scan.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.send_message(
        "Only the server owner, an administrator, or a delegated "
        "setup admin can open the setup wizard.",
        ephemeral=True,
    )


async def open_wizard_from_prefix(ctx: commands.Context) -> None:
    """Prefix-command entry point.  Posts a transient confirmation in the
    invoking channel (prefix replies can't be ephemeral; we keep the
    channel-side noise minimal).
    """
    guild = ctx.guild
    member = ctx.author
    if guild is None or not isinstance(member, discord.Member):
        await ctx.send("Run `!setup` from inside the server.")
        return

    session = await _resume_or_start(guild, owner_id=member.id)
    if setup_access.can_apply_setup(member, session):
        await _open_wizard_workspace_for_prefix(ctx, guild, member, session)
        return

    if setup_access.is_setup_admin(member, session):
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        if embed is None:
            await ctx.send("Could not build the readiness scan.")
            return
        await ctx.send(embed=embed)
        return

    await ctx.send(
        "Only the server owner, an administrator, or a delegated "
        "setup admin can open the setup wizard.",
    )


async def _resume_or_start(
    guild: discord.Guild,
    *,
    owner_id: int,
) -> setup_session.SetupSession | None:
    """Return the existing session row, starting one if missing.

    Best-effort: a DB failure on start_session is logged and ``None``
    is returned so the caller continues with the "denied" path.
    """
    try:
        session = await setup_session.resume_session(guild.id)
    except Exception:
        logger.exception("_wizard_entry.resume failed")
        session = None
    if session is None:
        try:
            session = await setup_session.start_session(
                guild_id=guild.id,
                guild_name=guild.name,
                owner_id=guild.owner_id or owner_id,
            )
        except Exception:
            logger.exception("_wizard_entry.start_session failed")
            session = None
    return session


async def _open_wizard_workspace_for_slash(
    interaction: discord.Interaction,
    guild: discord.Guild,
    member: discord.Member,
    session: setup_session.SetupSession | None,
) -> None:
    channel, message, reason = await open_setup_workspace(
        guild,
        member=member,
        session=session,
    )
    if reason == "no_channel" or channel is None:
        await interaction.response.send_message(
            "I couldn't ensure the private `#superbot-setup` channel — "
            "I need the **Manage Channels** permission.  Grant it and "
            "re-run `/setup`.",
            ephemeral=True,
        )
        return
    if reason == "post_failed" or message is None:
        await interaction.response.send_message(
            f"The `#superbot-setup` channel exists ({channel.mention}) "
            "but I couldn't post the wizard there — check my permissions "
            "in that channel.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"Setup wizard is open in {channel.mention} — {jump_link(message)}.",
        ephemeral=True,
    )


async def _open_wizard_workspace_for_prefix(
    ctx: commands.Context,
    guild: discord.Guild,
    member: discord.Member,
    session: setup_session.SetupSession | None,
) -> None:
    channel, message, reason = await open_setup_workspace(
        guild,
        member=member,
        session=session,
    )
    if reason == "no_channel" or channel is None:
        await ctx.send(
            "I couldn't ensure the private `#superbot-setup` channel — "
            "I need the **Manage Channels** permission.  Grant it and "
            "re-run `!setup`.",
        )
        return
    if reason == "post_failed" or message is None:
        await ctx.send(
            f"The `#superbot-setup` channel exists ({channel.mention}) "
            "but I couldn't post the wizard there — check my permissions "
            "in that channel.",
        )
        return

    await ctx.send(
        f"Setup wizard is open in {channel.mention} — {jump_link(message)}.",
    )


__all__ = [
    "open_wizard_from_prefix",
    "open_wizard_from_slash",
]
