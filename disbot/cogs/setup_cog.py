"""Setup-wizard launcher cog.

Discord-facing surface only. The persistent launcher view, embed
builder, and channel-selection helpers live in
:mod:`views.setup.launcher`; this file holds:

* the cog class with lifecycle listeners and slash/prefix entry
  commands (``!setup`` / ``/setup``);
* a shared ``_resolve_hub_entry`` helper that branches between the
  guided hub (owner / delegated admin) and the deterministic
  readiness embed (plain administrator).

Re-exports the launcher view + post helpers so callers that imported
``cogs.setup_cog.SetupLauncherView`` / ``post_launcher`` /
``pick_launcher_channel`` keep working.

Wires:
* :mod:`services.setup_session` for the lifecycle row.
* :mod:`services.setup_access` for owner / admin / non-admin gating.
* :func:`services.setup_readiness.collect` for readiness scans.
* :class:`views.setup.hub.SetupHubView` for the guided setup hub.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from services import setup_access, setup_session
from views.setup.launcher import (
    SetupLauncherView,
)
from views.setup.launcher import _build_launcher_embed as _build_launcher_embed
from views.setup.launcher import (
    pick_launcher_channel,
    post_launcher,
)

logger = logging.getLogger("bot.cogs.setup")


# ---------------------------------------------------------------------------
# Shared hub-entry helper for direct commands (!setup / /setup).
# ---------------------------------------------------------------------------


async def _resolve_hub_entry(
    member: discord.Member,
    guild: discord.Guild,
) -> (
    tuple[discord.Embed, discord.ui.View, str]
    | tuple[discord.Embed, None, str]
    | tuple[None, None, str]
):
    """Resolve the hub-entry response for ``member`` in ``guild``.

    Returns one of three shapes:

    * ``(hub_embed, hub_view, "hub")`` — member can apply setup; full
      hub is rendered. Caller marks the session in progress.
    * ``(readiness_embed, None, "readiness")`` — member is a setup
      admin without apply authority; render the deterministic
      readiness embed instead.
    * ``(None, None, "denied")`` — member is not a setup admin.

    The helper performs no Discord send; the calling command decides
    whether to reply ephemerally (slash) or to ``ctx.send`` (prefix).
    """
    session = await setup_session.resume_session(guild.id)

    if setup_access.can_apply_setup(member, session):
        if session is None:
            try:
                session = await setup_session.start_session(
                    guild_id=guild.id,
                    guild_name=guild.name,
                    owner_id=guild.owner_id or 0,
                )
            except Exception:
                logger.exception(
                    "setup_cog._resolve_hub_entry: start_session failed",
                )
                session = None

        from services import setup_draft
        from views.setup.hub import SetupHubView, build_hub_embed

        try:
            draft_ops = await setup_draft.list_ops(guild.id)
        except Exception:
            logger.exception(
                "setup_cog._resolve_hub_entry: setup_draft.list_ops failed",
            )
            draft_ops = []
        hub = SetupHubView(member, session=session)
        embed = build_hub_embed(
            session,
            pending_ops=len(draft_ops),
            draft_ops=draft_ops,
        )
        return embed, hub, "hub"

    if setup_access.is_setup_admin(member, session):
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        return embed, None, "readiness"

    return None, None, "denied"


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class SetupCog(commands.Cog):
    """Setup-wizard launcher.

    Listens for ``on_guild_join`` and ``on_ready`` and keeps the
    launcher message in sync with the ``setup_session`` row.
    Exposes ``!setup`` and ``/setup`` as direct entry / recovery
    commands; both route through ``_resolve_hub_entry``.

    The base ``SetupLauncherView`` is registered at ``cog_load`` so
    discord.py can dispatch interactions even before the resume
    sweep finishes (the rebound message has the same custom_ids).
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(SetupLauncherView())

    @commands.command(name="setup")
    @commands.guild_only()
    async def setup_cmd(self, ctx: commands.Context) -> None:
        """Open or resume the setup wizard from any channel.

        Owners and delegated setup admins get the hub; administrators
        without delegation get a read-only readiness embed; everyone
        else is denied.
        """
        guild = ctx.guild
        member = ctx.author
        if guild is None or not isinstance(member, discord.Member):
            await ctx.send("Run `!setup` from inside the server.")
            return

        embed, view, mode = await _resolve_hub_entry(member, guild)
        if mode == "denied":
            await ctx.send(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can open the setup wizard.",
            )
            return
        if mode == "readiness":
            if embed is None:
                await ctx.send("Could not build the readiness scan.")
                return
            await ctx.send(embed=embed)
            return

        if embed is None or view is None:
            await ctx.send("Could not build the setup hub. See logs.")
            return
        await ctx.send(embed=embed, view=view)
        try:
            await setup_session.mark_in_progress(guild.id, step="hub")
        except Exception:
            logger.exception("setup_cog.setup_cmd: mark_in_progress failed")

    @app_commands.command(
        name="setup",
        description="Open the setup wizard (owner, delegated admin, or admin).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_slash(self, interaction: discord.Interaction) -> None:
        """Ephemeral slash front door for the setup wizard.

        Mirrors the access ladder of the prefix command.
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup` from inside the server.",
                ephemeral=True,
            )
            return

        embed, view, mode = await _resolve_hub_entry(member, guild)
        if mode == "denied":
            await interaction.response.send_message(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can open the setup wizard.",
                ephemeral=True,
            )
            return
        if mode == "readiness":
            if embed is None:
                await interaction.response.send_message(
                    "Could not build the readiness scan.",
                    ephemeral=True,
                )
                return
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if embed is None or view is None:
            await interaction.response.send_message(
                "Could not build the setup hub. See logs.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )
        try:
            await setup_session.mark_in_progress(guild.id, step="hub")
        except Exception:
            logger.exception("setup_cog.setup_slash: mark_in_progress failed")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self._handle_join(guild)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._resume_launchers()

    async def _handle_join(self, guild: discord.Guild) -> None:
        """Internal entry point — split out for direct testing."""
        try:
            channel, message = await post_launcher(guild)
            channel_id = channel.id if channel is not None else None
            message_id = message.id if message is not None else None
            await setup_session.start_session(
                guild_id=guild.id,
                guild_name=guild.name,
                owner_id=guild.owner_id or 0,
                setup_channel_id=channel_id,
                setup_message_id=message_id,
            )
        except Exception:
            logger.exception(
                "setup_cog.on_guild_join: handler failed for guild=%d",
                guild.id,
            )

    async def _resume_launchers(self) -> None:
        """Refresh every guild's launcher message in place; isolate failures."""
        for guild in list(self.bot.guilds):
            try:
                await self._resume_one_launcher(guild)
            except Exception:
                logger.exception(
                    "setup_cog.on_ready: resume failed for guild=%d",
                    guild.id,
                )

    async def _resume_one_launcher(self, guild: discord.Guild) -> bool:
        """Refresh one guild's launcher message.

        Returns ``True`` when the message was edited, ``False`` when
        no row exists, the row has no channel/message ids, or the
        original message could not be fetched.
        """
        session = await setup_session.resume_session(guild.id)
        if session is None:
            return False
        if session.setup_channel_id is None or session.setup_message_id is None:
            return False

        channel = guild.get_channel(session.setup_channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            logger.debug(
                "setup_cog.on_ready: channel %s not in guild %d cache.",
                session.setup_channel_id,
                guild.id,
            )
            return False

        try:
            message = await channel.fetch_message(session.setup_message_id)
        except discord.NotFound:
            logger.info(
                "setup_cog.on_ready: launcher message %s in guild %d is gone.",
                session.setup_message_id,
                guild.id,
            )
            return False
        except discord.Forbidden:
            logger.warning(
                "setup_cog.on_ready: cannot fetch launcher in #%s (guild=%d).",
                channel.name,
                guild.id,
            )
            return False
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog.on_ready: HTTP error fetching launcher in guild=%d: %s",
                guild.id,
                exc,
            )
            return False

        view = SetupLauncherView(status=session.setup_status)
        embed = _build_launcher_embed(session)
        try:
            await message.edit(embed=embed, view=view)
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog.on_ready: edit_message failed for launcher in guild=%d: %s",
                guild.id,
                exc,
            )
            return False
        return True


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))


__all__ = [
    "SetupCog",
    "SetupLauncherView",
    "pick_launcher_channel",
    "post_launcher",
    "setup",
]
