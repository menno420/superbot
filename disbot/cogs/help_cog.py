from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.help.panels import _PAGE_SIZE  # noqa: F401 — re-export (tests)
from cogs.help.panels import (
    HelpCategoryView,
    HelpPanelView,
    _build_page_embed,
)
from cogs.help.route import HUB_PANEL_BUILDERS as _HUB_PANEL_BUILDERS
from cogs.help.route import (
    HelpOpener,
    HelpRoute,
)
from cogs.help.route import discovery_label as _discovery_label
from cogs.help.route import open_route as _open_route
from cogs.help.route import resolve_route as _resolve_route
from services import governance_service, help_overlay
from services.governance_service import GovernanceContext
from services.help_projection import HelpProjection, is_command_displayable
from utils.hub_registry import ALL_COMMANDS_KEY  # noqa: F401 — re-export (tests)
from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import UTILITY_COLOR

logger = logging.getLogger("bot")

# Re-exports kept for test compatibility — the canonical definitions live
# in ``cogs.help.route`` (route model) and ``cogs.help.panels`` (the two
# persistent views + page embed, decomposed when HLP-3 pushed this file
# past the 800-LOC cog ceiling). The Help route model is shared by the
# typed ``!help <name>`` command and the Help dropdown so the same name
# produces the same destination regardless of entry point.
__all__ = [
    "HelpCategoryView",
    "HelpOpener",
    "HelpPanelView",
    "HelpRoute",
    "_HUB_PANEL_BUILDERS",
    "_build_page_embed",
    "_open_route",
    "_resolve_route",
]


def _cog_for_subsystem(bot: commands.Bot, subsystem_name: str) -> commands.Cog | None:
    """Find the cog that corresponds to a subsystem by checking entry_points.

    Matches against both ``cmd.name`` and ``cmd.aliases`` so registry entries
    that reference an alias (e.g. ``"deathmatch"`` for ``dm_challenge``) still
    resolve to the owning cog.
    """
    meta = SUBSYSTEMS.get(subsystem_name)
    if not meta:
        return None
    entry_points = set(meta.get("entry_points", []))
    for cog in bot.cogs.values():
        cog_names: set[str] = set()
        for cmd in cog.get_commands():
            cog_names.add(cmd.name)
            cog_names.update(cmd.aliases)
        if cog_names & entry_points:
            return cog
    return None


def _get_visible_commands(cog: commands.Cog) -> list[commands.Command]:
    """Commands the help surfaces may render for ``cog``.

    Delegates to :func:`services.help_projection.is_command_displayable` —
    the one display filter (Discord-hidden / disabled / ledger
    classification) shared by the command-list embed and the typed
    single-command route (HLP-2).
    """
    return [cmd for cmd in cog.get_commands() if is_command_displayable(cmd)]


async def _resolve_projection(gctx: GovernanceContext) -> HelpProjection:
    """Governance + guild Help overlay → the audience projection (HLP-2/3).

    The cog's one projection-construction seam: every entry point and
    click-time re-check builds its :class:`HelpProjection` here, so the
    governance resolve (mockable via ``governance_service``) and the
    HLP-3 overlay fetch (cached; empty for DMs/faults) can never diverge
    across render paths.
    """
    vis_result = await governance_service.resolve_visibility(gctx)
    overlay = await help_overlay.get_guild_help_overlay(gctx.guild_id or None)
    return HelpProjection.from_visibility(vis_result, overlay=overlay)


def build_cog_embed(
    cog: commands.Cog,
    prefix: str,
    subsystem_name: str | None = None,
    *,
    projection: HelpProjection | None = None,
) -> discord.Embed:
    """Build a detail embed for one cog/subsystem.

    HLP-3: when a ``projection`` is given, the title takes the guild's
    effective display name (overlay rename) instead of the registry
    default — Help-only per Q-0056.
    """
    meta = SUBSYSTEMS.get(subsystem_name) if subsystem_name else None
    color = discord.Color(meta["color"]) if meta else UTILITY_COLOR
    display = (
        meta.get("display_name", cog.qualified_name.replace("Cog", ""))
        if meta
        else cog.qualified_name.replace("Cog", "")
    )
    emoji = meta.get("emoji", "📖") if meta else "📖"
    if projection is not None and subsystem_name:
        presentation = projection.subsystem_presentation(subsystem_name)
        if presentation is not None:
            display = presentation.display_name
            emoji = presentation.emoji

    _FIELD_CAP = 24  # Discord limit is 25; reserve 1 for overflow note
    embed = discord.Embed(title=f"{emoji} {display}", color=color)
    cmds = _get_visible_commands(cog)
    for cmd in cmds[:_FIELD_CAP]:
        aliases = f"  *(aliases: {', '.join(cmd.aliases)})*" if cmd.aliases else ""
        sig = f" {cmd.signature}".rstrip() if cmd.signature else ""
        label = _discovery_label(cmd)
        label_suffix = f"  ·  {label}" if label else ""
        embed.add_field(
            name=f"`{prefix}{cmd.name}`{label_suffix}{aliases}",
            value=f"{cmd.help or 'No description.'}\nUsage: `{prefix}{cmd.name}{sig}`",
            inline=False,
        )
    if len(cmds) > _FIELD_CAP:
        overflow = len(cmds) - _FIELD_CAP
        embed.add_field(
            name=f"… {overflow} more command(s)",
            value=f"Use `{prefix}help {display.lower()}` for the full list.",
            inline=False,
        )
    if not embed.fields:
        embed.description = "No commands available in this category."
    return embed


def _build_help_page_view(visible_list: list[str], page: int) -> HelpPanelView:
    """Construct a HelpPanelView for the given page of visible subsystems."""
    return HelpPanelView(visible_list, page)


def _attach_back_to_help_button(view: discord.ui.View) -> None:
    """Add a "↩ Back to Help" control to a panel surfaced from Help.

    Does not mutate the cog's panel class — adds the button to the live view
    instance only. No-op if the view already has 25 components (Discord cap;
    the shared helper logs a WARNING in that case).

    Re-resolves governance at click time so the Help menu the user returns
    to reflects current visibility (not the stale snapshot from when the
    panel was opened).

    S3: rebuilds :class:`HelpCategoryView` — the new top-level of Help
    after the category-index refactor. The pre-S3 implementation rebuilt
    a paginated :class:`HelpPanelView`; that view is still reachable as
    the "All Commands / Advanced" category but is no longer the top.

    AB2: also stashes a :class:`BackTarget` on ``view._back_target`` so
    that openers further down the chain can use :func:`chain_back` to
    preserve back-to-Help when they rebuild this panel.
    """
    # Local import — navigation is at the views layer; help_cog is at
    # the cogs layer. Function-local import keeps the import graph
    # acyclic in case the navigation module ever grows imports of its
    # own.
    from views.navigation import BackTarget, attach_back_button

    async def _build_help_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        gctx = GovernanceContext.from_interaction(interaction)
        projection = await _resolve_projection(gctx)
        new_view = HelpCategoryView(projection=projection)
        embed = build_categories_overview_embed(projection=projection)
        return embed, new_view

    attach_back_button(
        view,
        label="↩ Back to Help",
        custom_id="help:back",
        parent_builder=_build_help_parent,
        row=4,
        style=discord.ButtonStyle.secondary,
        error_message="Could not load help menu. Please try again.",
    )
    # AB2: child openers further down can compose back-to-Help via
    # ``chain_back(_build_me, grandparent=self._back_target)``. The
    # attribute is set unconditionally; persistent-view re-registration
    # constructs without ever calling this helper, so ``_back_target``
    # remains unset on restored views (the fail-safe contract).
    view._back_target = BackTarget(  # type: ignore[attr-defined]
        builder=_build_help_parent,
        label="↩ Back to Help",
        custom_id="help:back",
    )


def build_categories_overview_embed(
    member_tier: str | None = None,
    *,
    projection: HelpProjection | None = None,
) -> discord.Embed:
    """Build the top-level Help embed showing mother-hub categories.

    HLP-2: hub rows come from ``projection.visible_hubs()`` — the one
    effective-access seam (hub tier floor **and** host-subsystem governance
    visibility), so Home can no longer show a hub whose subsystem is
    governance-hidden in this scope. Live callers pass the projection they
    built from the resolved :class:`VisibilityResult`; ``member_tier`` alone
    falls back to :meth:`HelpProjection.registry_defaults` (static registry
    tiers — tests / restore symmetry only, byte-equivalent to the pre-seam
    tier-only rule).

    Always appends the permanent "Advanced / All Commands" fallback row.
    Each hub row is a uniform two-line shape — purpose + typed entry
    command — with no ``Includes:`` line. Child rosters live inside each
    hub panel.
    """
    if projection is None:
        projection = HelpProjection.registry_defaults(member_tier or "user")
    embed = discord.Embed(
        title="📚 Help Menu",
        description="Pick a category from the dropdown below.",
        color=UTILITY_COLOR,
    )

    for hub in projection.visible_hubs():
        embed.add_field(
            name=f"{hub.emoji} {hub.display_name}",
            value=f"{hub.purpose}\n→ `{hub.entry_command}`",
            inline=False,
        )

    # Advanced / All Commands is permanent — guarantees discoverability
    # for every visible subsystem even when no mother hub owns it.
    embed.add_field(
        name="📋 Advanced / All Commands",
        value="Browse every available command directly.",
        inline=False,
    )

    if not embed.fields:
        embed.description = "No commands are available in this channel."
    return embed


async def resolve_help_panel_state(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, HelpCategoryView]:
    """Resolve governance + build the Help top-level ``(embed, view)`` pair.

    Used by navigation buttons in other cogs / views (e.g.
    ``cogs.admin_cog._AdminPanelView.help_btn`` and
    ``views.mining.mine_view._MineResultsView.help_btn``) so they
    don't re-implement governance resolution + embed construction.

    S3: the returned view is :class:`HelpCategoryView` — the new
    mother-hub category index. The legacy :class:`HelpPanelView` is
    reached by selecting "All Commands / Advanced" inside the
    category view.

    Raises whatever ``governance_service.resolve_visibility`` raises;
    callers are responsible for catching to fall back to an in-place
    error embed.
    """
    gctx = GovernanceContext.from_interaction(interaction)
    projection = await _resolve_projection(gctx)
    view = HelpCategoryView(projection=projection)
    embed = build_categories_overview_embed(projection=projection)
    return embed, view


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(name="help", aliases=["hilfe"])
    async def help_command(self, ctx: commands.Context, *, category: str = None):
        """Shows available commands. Pass a category name for details."""
        gctx = GovernanceContext.from_ctx(ctx)
        projection = await _resolve_projection(gctx)
        prefix = ctx.prefix or "!"

        if category:
            opener = HelpOpener.from_ctx(ctx)
            route = _resolve_route(category, bot=self.bot)

            if route.kind == "unknown":
                await ctx.send(
                    f"No command or category named `{category}` found.",
                    delete_after=10,
                )
                return

            embed, sub_view = await _open_route(
                route,
                opener,
                projection=projection,
                prefix=prefix,
            )

            if sub_view is None:
                await ctx.send(embed=embed, delete_after=60)
                return

            # For typed Help with a hub/subsystem/advanced surface, send
            # the panel as a fresh message and attach Back-to-Help so the
            # user can return to the category index.
            _attach_back_to_help_button(sub_view)
            await ctx.send(embed=embed, view=sub_view)
            return

        # S3: the top of Help is the mother-hub category index. The
        # legacy paginated subsystem list is reached only via the
        # "Advanced / All Commands" entry inside HelpCategoryView.
        view = HelpCategoryView(projection=projection)
        embed = build_categories_overview_embed(projection=projection)

        # The help panel is invoke-and-see, not a stable hub: each !help should
        # appear at the bottom of the channel where the user just typed.
        # Delete any prior anchored help message so the new one is the only
        # active panel and the channel doesn't accumulate dead help embeds.
        from core.runtime import message_anchor_manager

        old_anchor = await message_anchor_manager.get(
            ctx.author.id,
            ctx.channel.id,
            "help",
        )
        if old_anchor and not old_anchor["is_stale"]:
            try:
                old_msg = await ctx.channel.fetch_message(old_anchor["message_id"])
                await old_msg.delete()
            except discord.NotFound:
                pass
            except (discord.Forbidden, discord.HTTPException) as exc:
                logger.debug(
                    "Could not delete prior help message | user=%d | msg=%d: %s",
                    ctx.author.id,
                    old_anchor["message_id"],
                    exc,
                )
            await message_anchor_manager.mark_stale(str(old_anchor["anchor_id"]))

        msg = await ctx.send(embed=embed, view=view)
        await message_anchor_manager.upsert(
            ctx.author.id,
            ctx.guild.id,
            ctx.channel.id,
            "help",
            msg.id,
        )

    @app_commands.command(
        name="help",
        description="Show available commands (optionally narrow to one category).",
    )
    @app_commands.describe(name="Optional category, hub, or command name")
    async def help_slash(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
    ) -> None:
        """Slash front door for Help — resolves identically to ``!help``.

        Same governance resolution + ``HelpRoute`` resolver + opener
        as the prefix command; differences are purely entry-point:

        * Responses are ephemeral (slash help is personal — each user
          gets their own panel without polluting the channel).
        * No message-anchor bookkeeping (Discord owns the ephemeral
          lifecycle; there is no anchor to clean up).
        * For hub/subsystem/advanced routes, the Back-to-Help button is
          attached so the user can return to the category index without
          rerunning ``/help``.

        PR #9 — first slash command in the bot. Proves the
        ``HelpRoute`` reuse pattern; follow-ups can land
        ``/games``, ``/economy``, etc.
        """
        gctx = GovernanceContext.from_interaction(interaction)
        projection = await _resolve_projection(gctx)

        if name:
            opener = HelpOpener.from_interaction(interaction)
            route = _resolve_route(name, bot=self.bot)

            if route.kind == "unknown":
                await interaction.response.send_message(
                    f"No command or category named `{name}` found.",
                    ephemeral=True,
                )
                return

            embed, sub_view = await _open_route(
                route,
                opener,
                projection=projection,
                prefix=config.PREFIX,  # RC-14: operator-configurable, not "!"
            )

            if sub_view is None:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Mirror the prefix path: any hub/subsystem/advanced surface
            # gets a Back-to-Help button so the user can return to the
            # category index in place.
            _attach_back_to_help_button(sub_view)
            await interaction.response.send_message(
                embed=embed,
                view=sub_view,
                ephemeral=True,
            )
            return

        # Default: top-level category index. Reuse
        # ``resolve_help_panel_state`` so the slash path and every
        # navigation Back-to-Help button land on the same builder.
        embed, view = await resolve_help_panel_state(interaction)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
    logger.info("HelpCog loaded.")
