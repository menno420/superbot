from __future__ import annotations

import io
import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import help_ctx_shim
from core.runtime.permission_checks import admin_or_owner
from services import xp_migration, xp_service
from services.rank_providers import get_provider
from services.xp_helpers import (
    _STAT_TYPES,
    RANK_CARD_FILENAME,
    build_rank_response,
    fetch_avatar_png,
)
from utils import embeds as em
from utils import xp_migration as xpm
from utils.rank_render import render_rank_card
from utils.ui_constants import ECONOMY_COLOR, UTILITY_COLOR
from views.base import send_panel
from views.xp.config_panel import XpConfigView
from views.xp.import_panel import XpImportView
from views.xp.main_panel import _XpHubView
from views.xp.rank_view import _RankView

logger = logging.getLogger("bot")


async def _build_rank_provider_response(
    provider,
    member: discord.Member,
    guild: discord.Guild,
) -> tuple[discord.Embed, discord.File | None]:
    """Render a single-user rank card for any non-XP provider.

    XP and coins keep their richer level / progress-bar card via
    :func:`services.xp_helpers.build_rank_response`. Everything else uses
    this thinner card: title from the provider, the member's rank +
    provider-formatted value, or an empty-state line when the member has no
    entry. The image rides the provider's own ``card_theme`` (so ``!rank
    mining`` shows the abyss skin, ``!rank crafting`` the ember skin, etc.) —
    the same per-category skinning the leaderboard card uses; an unranked
    member or a Pillow-less host falls back to the plain embed.
    """
    rank_pos, rendered = await provider.member_rank(guild, member.id)
    embed = discord.Embed(
        title=f"{provider.display_title} — {member.display_name}",
        color=ECONOMY_COLOR,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    if rank_pos is None:
        embed.description = provider.empty_hint
        return embed, None

    embed.add_field(name="Rank", value=f"#{rank_pos}", inline=True)
    embed.add_field(name="Value", value=rendered, inline=True)
    png = render_rank_card(
        display_name=member.display_name,
        subtitle=provider.display_title,
        stats=[("Rank", f"#{rank_pos}"), (provider.select_label, rendered)],
        theme=provider.card_theme,
        avatar_png=await fetch_avatar_png(member),
    )
    if png is None:
        return embed, None
    embed.set_image(url=f"attachment://{RANK_CARD_FILENAME}")
    return embed, discord.File(io.BytesIO(png), filename=RANK_CARD_FILENAME)


class XpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.xp.schemas import register_schemas
        from cogs.xp.stage import XpStage
        from core.runtime import message_pipeline

        message_pipeline.register(XpStage())
        register_schemas()

    async def cog_unload(self) -> None:
        from cogs.xp.stage import XP_STAGE_NAME
        from core.runtime import message_pipeline

        message_pipeline.unregister(XP_STAGE_NAME)

    @commands.command(name="xpmenu")
    async def xp_menu(self, ctx: commands.Context):
        """Open the XP panel showing your rank and quick admin actions."""
        view = _XpHubView(ctx)
        embed, card = await view.build_response()
        await send_panel(ctx, embed=embed, view=view, file=card)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the XP hub panel).

        Renders the same rank **image card** the direct ``!xpmenu`` surface shows
        (visual card engine H3): the card is stashed on the view as
        ``help_nav_card`` and every help-nav render site forwards it
        (``views.navigation.help_nav_card``), so the XP hub looks identical
        whether opened by command or reached through Help / hub navigation. On a
        Pillow-less host the card is ``None`` and the embed stays the source of
        truth — byte-identical to the prior embed-only behaviour.
        """
        view = _XpHubView(help_ctx_shim(interaction))
        embed, card = await view.build_response()
        view.help_nav_card = card
        return embed, view

    # ------------------------------------------------------------------ commands

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, *args):
        """Show rank in a category.

        PR G — provider-aware. Supported forms:

        * ``!rank``                — XP + coins overview (legacy default).
        * ``!rank xp|coins|both``  — XP/coin rank card (legacy).
        * ``!rank @user``          — XP + coins for another member.
        * ``!rank @user xp|coins`` — that user's XP or coin card.
        * ``!rank <category>``     — your rank in mining / deathmatch /
          rps / counting (any provider name or alias from
          :mod:`services.rank_providers`).
        """
        member: discord.Member = ctx.author  # type: ignore[assignment]
        stat: str | None = None
        category: str | None = None
        for arg in args:
            lowered = arg.lower()
            if lowered in _STAT_TYPES:
                stat = lowered
                continue
            # Try a non-XP provider category (mining, deathmatch, rps,
            # counting, plus all the aliases). Skip "xp"/"coins" — those
            # already match _STAT_TYPES above so the legacy rank card
            # path handles them.
            if lowered not in {"xp", "coins"}:
                provider = get_provider(lowered)
                if provider is not None:
                    category = provider.name
                    continue
            try:
                member = await commands.MemberConverter().convert(ctx, arg)
            except commands.BadArgument:
                pass

        if category is not None:
            provider = get_provider(category)
            assert provider is not None  # noqa: S101 — guarded above
            embed, card = await _build_rank_provider_response(
                provider,
                member,
                ctx.guild,
            )
            if card is not None:
                await ctx.send(embed=embed, file=card)
            else:
                await ctx.send(embed=embed)
            return

        stat = stat or "both"
        embed, card = await build_rank_response(member, ctx.guild, stat)
        view = _RankView(member, ctx.guild, stat)
        if card is not None:
            view.message = await ctx.send(embed=embed, view=view, file=card)
        else:
            view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="givexp")
    @admin_or_owner()
    async def givexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Give XP to a user (admin only)."""
        if amount <= 0:
            await ctx.send(embed=em.error("Amount must be positive."), delete_after=5)
            return
        result = await xp_service.award(
            guild_id=ctx.guild.id,
            user_id=member.id,
            amount=amount,
            source="admin:givexp",
        )
        await ctx.send(
            f"✅ Gave **{amount}** XP to {member.mention}. "
            f"They now have **{result.new_xp}** XP (Level **{result.new_level}**).",
        )

    @commands.command(name="resetxp")
    @admin_or_owner()
    async def resetxp(self, ctx: commands.Context, member: discord.Member):
        """Reset a user's XP to zero (admin only)."""
        await xp_service.reset(
            guild_id=ctx.guild.id,
            user_id=member.id,
            source="admin:resetxp",
            actor_id=ctx.author.id,
            actor_type="admin",
        )
        await ctx.send(f"✅ Reset XP for {member.mention}.")

    @commands.command(name="xpconfig")
    @admin_or_owner()
    async def xpconfig(self, ctx: commands.Context):
        """Open the XP configuration panel (admin only)."""
        view = XpConfigView(ctx)
        msg = await ctx.send(embed=await view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="xpimport")
    @admin_or_owner()
    async def xpimport(self, ctx: commands.Context, *args: str):
        """Import XP/levels from another bot by reading its level-up channel.

        Works by scanning the **dedicated level-up channel** another leveling
        bot posts in (the "so-and-so reached level N" announcements) and copying
        the highest level it announced for each member. Also reachable as the
        **📥 Import from another bot** button on ``!xpconfig``.

        Usage: ``!xpimport [source] [#channel] [limit]`` (admin only).

        * ``source``  — which bot posted the announcements: ``arcane`` (default),
          ``mee6``, ``superbot``, or ``generic``.
        * ``#channel`` — that bot's level-up channel (defaults to here).
        * ``limit``    — max messages to scan (defaults to the whole channel).

        Keeps the **highest** level announced per member and opens a preview to
        confirm before writing. The import is **raise-only** — it never lowers a
        member — so it is safe to re-run. Run ``!xpimport help`` for the list of
        supported bots.
        """
        source_key: str | None = None
        channel: discord.TextChannel | None = None
        limit: int | None = None
        for arg in args:
            lowered = arg.lower()
            if lowered in {"help", "formats", "list"}:
                await ctx.send(embed=self._formats_embed())
                return
            if xpm.get_format(lowered) is not None:
                source_key = lowered
                continue
            if arg.isdigit():
                limit = int(arg)
                continue
            try:
                channel = await commands.TextChannelConverter().convert(ctx, arg)
                continue
            except commands.BadArgument:
                pass  # unknown token — ignore; preview shows what was scanned

        fmt = xpm.get_format(source_key or xpm.DEFAULT_FORMAT)
        assert fmt is not None  # noqa: S101 — DEFAULT_FORMAT is always a valid key
        target: discord.TextChannel = channel or ctx.channel  # type: ignore[assignment]

        status = await ctx.send(
            embed=discord.Embed(
                title="📥 Scanning…",
                description=f"Reading {target.mention} for **{fmt.label}** level-ups…",
                color=UTILITY_COLOR,
            ),
        )

        plan = await xp_migration.scan_channel(ctx.guild, target, fmt, limit)
        if plan is None:
            await status.edit(
                embed=em.error(
                    f"I can't read message history in {target.mention}. "
                    "Grant me **Read Message History** there and try again.",
                ),
            )
            return
        if not plan.records:
            await status.edit(
                embed=discord.Embed(
                    title="Nothing to import",
                    description=(
                        f"Scanned **{plan.scanned_messages}** message(s) in "
                        f"{target.mention} but found no **{fmt.label}** level-up "
                        "announcements. Try a different `source` or `#channel` — "
                        "`!xpimport help` lists the formats."
                    ),
                    color=UTILITY_COLOR,
                ),
            )
            return

        view = XpImportView(ctx, plan)
        view.message = await status.edit(embed=view.build_embed(), view=view)

    @staticmethod
    def _formats_embed() -> discord.Embed:
        embed = discord.Embed(
            title="📥 Import XP from another bot",
            description=(
                "SuperBot can copy the levels members earned under a **different "
                "leveling bot** by reading that bot's **dedicated level-up "
                "channel** — the channel where it posts *“so-and-so reached level "
                "N”* — and keeping the highest level per member (raise-only, "
                "preview first).\n\n"
                "Use the **📥 Import from another bot** button on `!xpconfig`, or "
                "`!xpimport [source] [#channel] [limit]`. Supported bots:"
            ),
            color=UTILITY_COLOR,
        )
        for key in xpm.format_keys():
            fmt = xpm.get_format(key)
            assert fmt is not None  # noqa: S101 — iterating the registry's own keys
            default = " *(default)*" if key == xpm.DEFAULT_FORMAT else ""
            embed.add_field(name=f"`{key}`{default}", value=fmt.label, inline=True)
        embed.set_footer(
            text="Needs the other bot's level-up channel — the one with its "
            "“reached level N” messages.",
        )
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(XpCog(bot))
    logger.info("XpCog loaded.")
