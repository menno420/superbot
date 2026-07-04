"""Starboard / Hall-of-Fame cog (idea B1; plan starboard-plan-2026-06-21).

N ⭐-reactions on any message → it's posted to a configured hall-of-fame channel
with a jump link + a live-updating star count; the post is edited as the count
changes and removed if it falls back below threshold.

The cog is a thin Discord layer over :mod:`services.starboard_service`: the
raw-reaction listeners recount the live star total and delegate the post/edit/
delete *decision* to the service (which owns the DB + audit); the cog performs
the actual Discord send/edit/delete. Mirrors the reaction-role listener shape
(bot-ignore, resolve, fast-path gate) — the same hardened raw-reaction seam.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.permission_checks import perms_or_owner
from services import starboard_service

logger = logging.getLogger("bot.cogs.starboard")

STAR_COLOR = discord.Color.gold()


class StarboardCog(commands.Cog):
    """Reaction-triggered hall-of-fame + its per-guild config command."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ listeners

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        await self._handle(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        await self._handle(payload)

    async def _handle(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None:
            return
        bot_user = self.bot.user
        if bot_user is not None and payload.user_id == bot_user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        # Fast-path gate: bail immediately unless this guild has a starboard and
        # the reacted emoji is its trigger emoji (the vast majority of reactions).
        # One settings read also gives us ``self_star`` so the cog knows whether
        # the author's own ⭐ should be discounted (only then do we pay the extra
        # reactor-list fetch to find out if the author reacted).
        settings = await starboard_service.get_settings(guild.id)
        if settings is None or not settings["enabled"]:
            return
        emoji = settings["emoji"]
        if str(payload.emoji) != emoji:
            return

        source = self.bot.get_channel(payload.channel_id)
        if not isinstance(source, discord.abc.Messageable):
            return
        try:
            message = await source.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        star_count = _count_emoji(message, emoji)
        author_starred = False
        if not settings["self_star"]:
            author_starred = await _author_starred(message, emoji)
        outcome = await starboard_service.handle_star_change(
            guild_id=guild.id,
            source_channel_id=payload.channel_id,
            source_message_id=payload.message_id,
            star_count=star_count,
            author_starred=author_starred,
        )
        await self._apply(guild, message, emoji, outcome)

    async def _apply(
        self,
        guild: discord.Guild,
        message: discord.Message,
        emoji: str,
        outcome: starboard_service.StarboardOutcome,
    ) -> None:
        if outcome.action == starboard_service.NONE or outcome.channel_id is None:
            return
        board = self.bot.get_channel(outcome.channel_id)
        if not isinstance(board, discord.abc.Messageable):
            return

        if outcome.action == starboard_service.POST:
            embed = _build_embed(message, emoji, outcome.star_count)
            try:
                posted = await board.send(
                    content=_header(emoji, outcome.star_count, message),
                    embed=embed,
                )
            except (discord.Forbidden, discord.HTTPException):
                logger.warning(
                    "starboard: could not post to channel=%s (guild=%s)",
                    outcome.channel_id,
                    guild.id,
                )
                return
            await starboard_service.record_post(
                guild.id,
                message.id,
                starboard_message_id=posted.id,
                star_count=outcome.star_count,
            )
            return

        if outcome.starboard_message_id is None:
            return
        try:
            existing = await board.fetch_message(outcome.starboard_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
        if outcome.action == starboard_service.EDIT:
            try:
                await existing.edit(
                    content=_header(emoji, outcome.star_count, message),
                    embed=_build_embed(message, emoji, outcome.star_count),
                )
            except (discord.Forbidden, discord.HTTPException):
                pass
        elif outcome.action == starboard_service.DELETE:
            try:
                await existing.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

    # ------------------------------------------------------------------ config

    @commands.group(name="starboard", invoke_without_command=True)
    @perms_or_owner(manage_guild=True)
    async def starboard_group(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        threshold: int = 3,
    ) -> None:
        """Show or set the hall-of-fame channel + star threshold.

        ``!starboard`` shows the current config; ``!starboard #channel [n]`` sets
        the channel + threshold (default 3); ``!starboard off`` disables it.
        """
        if channel is None:
            settings = await starboard_service.get_settings(ctx.guild.id)
            if settings and settings["enabled"]:
                board = resources.resolve_channel(
                    ctx.guild,
                    channel_id=int(settings["channel_id"]),
                )
                where = board.mention if board else f"`{settings['channel_id']}`"
                await ctx.send(
                    f"⭐ Starboard: {settings['emoji']} ≥ **{settings['threshold']}** "
                    f"→ {where}. Set with `!starboard #channel [threshold]`, "
                    f"turn off with `!starboard off`.",
                )
            else:
                await ctx.send(
                    "⭐ Starboard is off. Turn it on with "
                    "`!starboard #channel [threshold]` (e.g. `!starboard #hall-of-fame 5`).",
                )
            return

        stored = await starboard_service.configure(
            guild_id=ctx.guild.id,
            channel_id=channel.id,
            threshold=threshold,
            actor_id=ctx.author.id,
        )
        await ctx.send(
            f"✅ Starboard set: ⭐ **{stored}**+ stars → {channel.mention}.",
        )

    @starboard_group.command(name="off")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def starboard_off(self, ctx: commands.Context) -> None:
        """Disable the starboard (config is preserved)."""
        await starboard_service.disable(guild_id=ctx.guild.id, actor_id=ctx.author.id)
        await ctx.send("✅ Starboard disabled. Re-enable with `!starboard #channel`.")

    @starboard_group.command(name="selfstar")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def starboard_selfstar(self, ctx: commands.Context, value: str) -> None:
        """Count the author's own ⭐? ``!starboard selfstar on|off`` (default off)."""
        on = value.strip().lower() in {"on", "yes", "true", "1", "enable", "enabled"}
        await starboard_service.set_self_star(
            guild_id=ctx.guild.id,
            self_star=on,
            actor_id=ctx.author.id,
        )
        await ctx.send(
            (
                "✅ Self-stars **count** toward the threshold."
                if on
                else "✅ Self-stars are **ignored** (the author's own ⭐ doesn't count)."
            ),
        )

    @starboard_group.command(name="ignore")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def starboard_ignore(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
    ) -> None:
        """Exclude a channel — its messages never enter the board."""
        await starboard_service.add_ignore_channel(
            guild_id=ctx.guild.id,
            channel_id=channel.id,
            actor_id=ctx.author.id,
        )
        await ctx.send(
            f"✅ Ignoring {channel.mention} — its messages won't be starred.",
        )

    @starboard_group.command(name="unignore")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def starboard_unignore(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
    ) -> None:
        """Stop ignoring a channel (messages there can enter the board again)."""
        await starboard_service.remove_ignore_channel(
            guild_id=ctx.guild.id,
            channel_id=channel.id,
            actor_id=ctx.author.id,
        )
        await ctx.send(f"✅ No longer ignoring {channel.mention}.")

    @starboard_group.command(name="panel")  # type: ignore[arg-type]
    @perms_or_owner(manage_guild=True)
    async def starboard_panel(self, ctx: commands.Context) -> None:
        """Open the interactive starboard config panel."""
        from views.base import send_panel
        from views.starboard import StarboardConfigPanel

        panel = StarboardConfigPanel(ctx)
        await send_panel(ctx, embed=await panel.build_embed(), view=panel)


def _count_emoji(message: discord.Message, emoji: str) -> int:
    """Live count of ``emoji`` reactions on a message (recount, not delta)."""
    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            return int(reaction.count)
    return 0


async def _author_starred(message: discord.Message, emoji: str) -> bool:
    """Whether the message author is among the ``emoji`` reactors.

    Only called when ``self_star`` is off (the cog discounts the author's own
    ⭐). Fetches the reactor list for the trigger reaction; on any API failure it
    returns ``False`` (fail open — never wrongly suppress a genuine star).
    """
    author_id = getattr(message.author, "id", None)
    if author_id is None:
        return False
    for reaction in message.reactions:
        if str(reaction.emoji) != emoji:
            continue
        try:
            async for user in reaction.users():
                if getattr(user, "id", None) == author_id:
                    return True
        except (discord.HTTPException, discord.Forbidden):
            return False
        return False
    return False


def _header(emoji: str, star_count: int, message: discord.Message) -> str:
    channel = getattr(message.channel, "mention", "")
    return f"{emoji} **{star_count}** · {channel}".strip()


def _build_embed(
    message: discord.Message,
    emoji: str,
    star_count: int,
) -> discord.Embed:
    """Render a starred message into its hall-of-fame embed."""
    embed = discord.Embed(
        description=(message.content or None),
        color=STAR_COLOR,
        timestamp=message.created_at,
    )
    embed.set_author(
        name=message.author.display_name,
        icon_url=getattr(message.author.display_avatar, "url", None),
    )
    embed.add_field(
        name="Source",
        value=f"[Jump to message]({message.jump_url})",
        inline=False,
    )
    # First image attachment becomes the embed image preview.
    for attachment in message.attachments:
        ctype = attachment.content_type or ""
        if ctype.startswith("image/"):
            embed.set_image(url=attachment.url)
            break
    embed.set_footer(text=f"{emoji} {star_count}")
    return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StarboardCog(bot))
