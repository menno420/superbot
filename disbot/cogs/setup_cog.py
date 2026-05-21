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

    Returns one of four shapes:

    * ``(depth_embed, depth_view, "depth_picker")`` — first-time entry
      for an apply-capable member with no depth chosen yet.
    * ``(hub_embed, hub_view, "hub")`` — member can apply setup and
      has a persisted depth; full hub renders, filtered by depth.
      Caller marks the session in progress.
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

        if session is not None and session.depth is None:
            from views.setup.depth_panel import (
                DepthPanelView,
                build_depth_embed,
            )

            view = DepthPanelView(member, session=session)
            return build_depth_embed(), view, "depth_picker"

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


_STATUS_COLOR_BY_STATUS = {
    "pending": discord.Color.blurple(),
    "in_progress": discord.Color.gold(),
    "complete": discord.Color.green(),
    "dismissed": discord.Color.dark_grey(),
}


def _build_status_embed(
    session: setup_session.SetupSession | None,
    *,
    pending_ops: int,
) -> discord.Embed:
    """Render a read-only status snapshot for ``/setup-status``.

    Pure helper — takes a resolved session + the pending-op count and
    returns the embed. No DB / Discord I/O. Mirrors the data points
    the hub embed surfaces (status, depth, current step, readiness
    score, pending ops, skipped sections) but with no buttons.
    """
    status = session.setup_status if session is not None else "no session"
    color = _STATUS_COLOR_BY_STATUS.get(status, discord.Color.blurple())
    embed = discord.Embed(
        title="🛰 Setup status",
        description=f"**Status:** `{status}`",
        color=color,
    )
    if session is None:
        embed.add_field(
            name="No session row",
            value=(
                "The bot has not recorded any setup session for this guild. "
                "Run `!setup` or `/setup` to start."
            ),
            inline=False,
        )
        return embed

    if session.depth:
        embed.add_field(name="Depth", value=f"`{session.depth}`", inline=True)
    if session.current_step:
        embed.add_field(
            name="Current step",
            value=f"`{session.current_step}`",
            inline=True,
        )
    if session.last_readiness_score is not None:
        embed.add_field(
            name="Readiness",
            value=f"`{session.last_readiness_score}%`",
            inline=True,
        )
    embed.add_field(
        name="Pending operations",
        value=f"`{pending_ops}`",
        inline=True,
    )
    if session.skipped_sections:
        embed.add_field(
            name="Skipped sections",
            value=", ".join(f"`{s}`" for s in sorted(session.skipped_sections)),
            inline=False,
        )
    if session.delegated_admins:
        embed.add_field(
            name="Delegated admins",
            value=", ".join(f"<@{uid}>" for uid in session.delegated_admins),
            inline=False,
        )
    if session.setup_channel_id is not None:
        embed.add_field(
            name="Setup channel",
            value=f"<#{session.setup_channel_id}>",
            inline=True,
        )
    embed.set_footer(text="Read-only. Run `!setup` / `/setup` to make changes.")
    return embed


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
        if mode == "hub":
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
        if mode == "hub":
            try:
                await setup_session.mark_in_progress(guild.id, step="hub")
            except Exception:
                logger.exception("setup_cog.setup_slash: mark_in_progress failed")

    @app_commands.command(
        name="setup-status",
        description="Quick at-a-glance setup state (read-only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_status_slash(self, interaction: discord.Interaction) -> None:
        """Ephemeral read-only status view.

        Surfaces the session lifecycle, depth choice, pending op
        count, and skipped section list without opening the
        interactive hub. Useful for "where am I?" peeks that don't
        want to enter the wizard.
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup-status` from inside the server.",
                ephemeral=True,
            )
            return

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_status_slash: resume failed")
            session = None

        if not setup_access.is_setup_admin(member, session):
            await interaction.response.send_message(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can view setup status.",
                ephemeral=True,
            )
            return

        from services import setup_draft

        try:
            pending_ops = await setup_draft.count(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_status_slash: draft.count failed")
            pending_ops = 0

        embed = _build_status_embed(session, pending_ops=pending_ops)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self._handle_join(guild)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._resume_launchers()

    async def _handle_join(self, guild: discord.Guild) -> None:
        """Internal entry point — split out for direct testing.

        Tries to auto-create a private ``#superbot-setup`` channel and
        post the launcher there with an owner ping. If the bot lacks
        Manage Channels (or the create fails), falls back to
        :func:`post_launcher` which picks the safest existing channel
        or DMs the owner.
        """
        try:
            channel_id, message_id = await self._post_launcher_in_setup_channel(
                guild,
            )
            if channel_id is None:
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

    async def _post_launcher_in_setup_channel(
        self,
        guild: discord.Guild,
    ) -> tuple[int | None, int | None]:
        """Try the private-setup-channel path; return ``(channel_id,
        message_id)`` on success or ``(None, None)`` to signal the
        caller should fall back to :func:`post_launcher`.

        Resuming on bot restart hits the same path and is idempotent
        (``ensure_setup_channel`` returns the existing channel without
        recreating, and the cog keeps the prior message id when the
        existing launcher message is still posted).
        """
        from services.setup_channel import ensure_setup_channel

        existing_session = await setup_session.resume_session(guild.id)
        existing_channel_id = (
            existing_session.setup_channel_id if existing_session else None
        )
        try:
            channel, was_created = await ensure_setup_channel(
                guild,
                existing_channel_id=existing_channel_id,
            )
        except Exception:
            logger.exception(
                "setup_cog._post_launcher_in_setup_channel: ensure failed "
                "(guild=%d)",
                guild.id,
            )
            return None, None
        if channel is None:
            return None, None

        # On a restart where the channel already existed and we already
        # posted a launcher, do not double-post — the existing message
        # gets edited in place by ``_resume_launchers`` on ``on_ready``.
        if (
            not was_created
            and existing_session is not None
            and existing_session.setup_channel_id == channel.id
            and existing_session.setup_message_id is not None
        ):
            return channel.id, existing_session.setup_message_id

        embed = _build_launcher_embed(None)
        view = SetupLauncherView()
        owner_mention = guild.owner.mention if guild.owner is not None else ""
        content = (
            f"{owner_mention} SuperBot just joined! I'll use this private "
            f"channel as the setup workspace. Click **Start Setup** below "
            f"(or run `!setup` / `/setup`) to begin."
            if was_created
            else None
        )
        try:
            message = await channel.send(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(users=True, everyone=False),
            )
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog._post_launcher_in_setup_channel: send failed "
                "in guild=%d: %s",
                guild.id,
                exc,
            )
            return None, None
        return channel.id, message.id

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
