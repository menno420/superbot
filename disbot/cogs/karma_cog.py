"""Karma subsystem — peer reputation (thanks/upvote) command surface.

Thin dispatcher over :mod:`services.karma_service` (the audited write seam)
and :mod:`services.karma_config` (the operator policy). Commands:

  - ``!thanks @user [reason]`` / ``!karma add @user [reason]`` — grant karma
  - ``!karma [member]``                                        — show a karma card
  - ``/karma [member]``                                        — ephemeral karma card

All grant rules (no self/bot, cooldown, daily cap, enabled) live in the
service; this cog only resolves Discord objects, rejects bot recipients,
and renders the service's typed errors as friendly messages.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer, safe_followup
from services import karma_config, karma_service
from services.karma_service import (
    KarmaCooldownError,
    KarmaDailyCapError,
    KarmaDisabledError,
    KarmaError,
    SelfKarmaError,
)
from utils import embeds as em
from utils.cooldowns import format_remaining

logger = logging.getLogger("bot")

_KARMA_COLOR = discord.Color.magenta()


def _karma_card(
    guild: discord.Guild,
    member: discord.abc.User,
    record,
) -> discord.Embed:
    """Render a member's karma standing as an embed."""
    rank_line = f"#{record.rank}" if record.rank is not None else "unranked"
    embed = discord.Embed(
        title=f"✨ Karma — {member.display_name}",
        color=_KARMA_COLOR,
    )
    embed.add_field(name="Karma", value=f"**{record.points}** ✨", inline=True)
    embed.add_field(name="Rank", value=rank_line, inline=True)
    embed.add_field(
        name="Activity",
        value=f"received **{record.received_count}** · given **{record.given_count}**",
        inline=False,
    )
    avatar = getattr(member, "display_avatar", None)
    if avatar is not None:
        embed.set_thumbnail(url=avatar.url)
    embed.set_footer(text="Thank helpful members with !thanks @user")
    return embed


class KarmaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.karma.schemas import register_schemas

        register_schemas()

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu / Community-hub navigation hook — the viewer's karma card."""
        from views.base import HubView

        if interaction.guild is None:
            return (
                discord.Embed(description="Karma is only available in a server."),
                discord.ui.View(),
            )
        record = await karma_service.get_record(
            interaction.guild.id,
            interaction.user.id,
        )
        embed = _karma_card(interaction.guild, interaction.user, record)
        return embed, HubView(interaction.user)

    # --------------------------------------------------------------- reaction

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        """React-to-thank: reacting with the guild's configured emoji grants
        karma to the reacted message's author.

        Opt-in per guild (``karma.reaction_emoji`` — empty by default, so a
        server that never configures it behaves exactly as before). The grant
        flows through the same audited :func:`karma_service.give` seam as
        ``!thanks``, so the self-give guard, per-recipient cooldown, and daily
        cap all apply. Blocked grants are swallowed silently — a reaction must
        never spam the channel with error messages.
        """
        if payload.guild_id is None:
            return
        member = payload.member  # set for guild reaction-adds (the reactor)
        if member is None or member.bot:
            return

        # Fast gate: one settings read (like the starboard listener). Bail
        # unless react-to-thank is enabled and this is the trigger emoji —
        # true for the vast majority of reactions, before any message fetch.
        policy = await karma_config.load_policy(payload.guild_id)
        if not policy.enabled or not policy.reaction_emoji:
            return
        if str(payload.emoji) != policy.reaction_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        author = message.author
        # Can't thank a bot; a self-reaction is a no-op (the service guards it
        # too, but skip the write path entirely).
        if author.bot or author.id == payload.user_id:
            return

        try:
            await karma_service.give(
                payload.guild_id,
                from_user=payload.user_id,
                to_user=author.id,
                source="reaction",
                reason=None,
                policy=policy,  # reuse the policy already loaded above
            )
        except KarmaError:
            # Disabled / self / cooldown / daily-cap — stay silent.
            return

    # ------------------------------------------------------------------ grant

    async def _do_thanks(
        self,
        ctx: commands.Context,
        recipient: discord.Member,
        reason: str | None,
    ) -> None:
        """Shared grant path for ``!thanks`` and ``!karma add``."""
        if recipient.bot:
            await ctx.send(
                embed=em.error("You can't give karma to a bot."),
                delete_after=8,
            )
            return
        try:
            grant = await karma_service.give(
                ctx.guild.id,
                from_user=ctx.author.id,
                to_user=recipient.id,
                source="command",
                reason=reason or None,
            )
        except SelfKarmaError:
            await ctx.send(
                embed=em.error("You can't give karma to yourself."),
                delete_after=8,
            )
        except KarmaDisabledError:
            await ctx.send(
                embed=em.error("Karma is disabled on this server."),
                delete_after=8,
            )
        except KarmaCooldownError as exc:
            await ctx.send(
                embed=em.error(
                    f"You've already thanked {recipient.display_name} recently — "
                    f"try again in {format_remaining(exc.retry_after)}.",
                ),
                delete_after=8,
            )
        except KarmaDailyCapError as exc:
            await ctx.send(
                embed=em.error(
                    f"You've reached your daily limit of {exc.cap} karma grants. "
                    "Come back tomorrow!",
                ),
                delete_after=8,
            )
        else:
            await ctx.send(
                f"✨ {ctx.author.mention} gave karma to {recipient.mention} — "
                f"they now have **{grant.new_total}** karma.",
            )

    @commands.guild_only()
    @commands.cooldown(rate=5, per=10, type=commands.BucketType.user)
    @commands.command(name="thanks", aliases=["rep", "thank"])
    async def thanks(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> None:
        """Give a karma point to a helpful member: ``!thanks @user [reason]``."""
        await self._do_thanks(ctx, member, reason)

    # ------------------------------------------------------------------ card

    @commands.guild_only()
    @commands.cooldown(rate=5, per=10, type=commands.BucketType.user)
    @commands.group(name="karma", invoke_without_command=True)
    async def karma(
        self,
        ctx: commands.Context,
        member: discord.Member | None = None,
    ) -> None:
        """Show a member's karma standing: ``!karma [@user]``."""
        target = member or ctx.author
        record = await karma_service.get_record(ctx.guild.id, target.id)
        await ctx.send(embed=_karma_card(ctx.guild, target, record))

    @karma.command(name="add")  # type: ignore[arg-type]
    async def karma_add(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> None:
        """Give a karma point: ``!karma add @user [reason]``."""
        await self._do_thanks(ctx, member, reason)

    # ------------------------------------------------------------------ slash

    @app_commands.command(
        name="karma",
        description="Show your karma (peer reputation) — or another member's.",
    )
    @app_commands.describe(member="Whose karma to show (defaults to you).")
    @app_commands.guild_only()
    async def karma_slash(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """Slash front door for the karma card — ephemeral."""
        if not await safe_defer(interaction, ephemeral=True):
            return
        target = member or interaction.user
        record = await karma_service.get_record(interaction.guild_id, target.id)
        embed = _karma_card(interaction.guild, target, record)
        await safe_followup(interaction, embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(KarmaCog(bot))
