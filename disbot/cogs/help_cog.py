from __future__ import annotations

import logging
import math

import discord
from discord.ext import commands

from core.runtime.persistent_views import PersistentView, register
from services import governance_service
from services.governance_service import GovernanceContext
from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted
from utils.ui_constants import ADMIN_COLOR, GENERAL_COLOR, MOD_COLOR, UTILITY_COLOR

logger = logging.getLogger("bot")

_PAGE_SIZE = 12  # subsystems per help page — well under Discord's 25-option limit

# Tier group display configuration
_TIER_GROUPS = [
    {
        "label": "🟢 User Commands",
        "tiers": {"user", "trusted"},
        "color": GENERAL_COLOR,
    },
    {
        "label": "🟠 Moderation",
        "tiers": {"staff", "moderator"},
        "color": MOD_COLOR,
    },
    {
        "label": "🔴 Administration",
        "tiers": {"administrator", "owner"},
        "color": ADMIN_COLOR,
    },
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
    return [cmd for cmd in cog.get_commands() if not cmd.hidden and cmd.enabled]


async def build_overview_embed(
    bot: commands.Bot,
    ctx: commands.Context,
    visible: set[str],
    member_tier: str,
) -> discord.Embed:
    """Build a governance-aware overview embed grouped by visibility tier.

    Subsystems with ``parent_hub`` set (e.g. Blackjack under the Games
    hub) are hidden from the top-level overview — they remain reachable
    through their hub and via typed commands.
    """
    embed = discord.Embed(
        title="📚 Help Menu",
        description="Select a category from the dropdown below.",
        color=UTILITY_COLOR,
    )

    subsystems_by_name = dict(all_subsystems_sorted())

    for group in _TIER_GROUPS:
        group_tiers: set[str] = group["tiers"]
        entries: list[str] = []

        for name, meta in subsystems_by_name.items():
            if name not in visible:
                continue
            if meta.get("parent_hub"):
                continue
            if meta.get("visibility_tier") not in group_tiers:
                continue
            emoji = meta.get("emoji", "•")
            display = meta.get("display_name", name)
            desc = meta.get("description", "")
            entries.append(f"{emoji} **{display}** — {desc}")

        if entries:
            embed.add_field(
                name=group["label"],
                value="\n".join(entries),
                inline=False,
            )

    if not embed.fields:
        embed.description = "No commands are available in this channel."
    return embed


def build_cog_embed(
    cog: commands.Cog,
    prefix: str,
    subsystem_name: str | None = None,
) -> discord.Embed:
    """Build a detail embed for one cog/subsystem."""
    meta = SUBSYSTEMS.get(subsystem_name) if subsystem_name else None
    color = discord.Color(meta["color"]) if meta else UTILITY_COLOR
    display = (
        meta.get("display_name", cog.qualified_name.replace("Cog", ""))
        if meta
        else cog.qualified_name.replace("Cog", "")
    )
    emoji = meta.get("emoji", "📖") if meta else "📖"

    embed = discord.Embed(title=f"{emoji} {display}", color=color)
    cmds = _get_visible_commands(cog)
    for cmd in cmds:
        aliases = f"  *(aliases: {', '.join(cmd.aliases)})*" if cmd.aliases else ""
        sig = f" {cmd.signature}".rstrip() if cmd.signature else ""
        embed.add_field(
            name=f"`{prefix}{cmd.name}`{aliases}",
            value=f"{cmd.help or 'No description.'}\nUsage: `{prefix}{cmd.name}{sig}`",
            inline=False,
        )
    if not embed.fields:
        embed.description = "No commands available in this category."
    return embed


def _build_help_page_view(visible_list: list[str], page: int) -> HelpPanelView:
    """Construct a HelpPanelView for the given page of visible subsystems."""
    return HelpPanelView(visible_list, page)


def _attach_back_to_help_button(
    view: discord.ui.View,
    visible_list: list[str],
    page: int,
) -> None:
    """Add a "↩ Back to Help" control to a subsystem panel surfaced from help.

    Does not mutate the cog's panel class — adds the button to the live view
    instance only. No-op if the view already has 25 components (Discord cap;
    the shared helper logs a WARNING in that case).

    Re-resolves governance at click time so the Help menu the user returns
    to reflects current visibility (not the stale snapshot from when the
    panel was opened).

    Phase 3.5: implementation moved to ``views.navigation.attach_back_button``;
    the help-specific parent-builder (governance resolve + pagination clamp +
    fresh HelpPanelView) is kept here as a closure.
    """
    # Local import — navigation is at the views layer; help_cog is at
    # the cogs layer. Function-local import keeps the import graph
    # acyclic in case the navigation module ever grows imports of its
    # own.
    from views.navigation import attach_back_button

    async def _build_help_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        gctx = GovernanceContext.from_interaction(interaction)
        vis_result = await governance_service.resolve_visibility(gctx)
        fresh_visible = [
            name
            for name, meta in all_subsystems_sorted()
            if name in vis_result.visible_subsystems and not meta.get("parent_hub")
        ]
        new_page = min(page, max(0, math.ceil(len(fresh_visible) / _PAGE_SIZE) - 1))
        new_view = HelpPanelView(fresh_visible, new_page)
        embed = _build_page_embed(
            interaction.client,  # type: ignore[arg-type]
            fresh_visible,
            new_page,
            vis_result.member_tier,
        )
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


def _build_page_embed(
    bot: commands.Bot,
    visible_list: list[str],
    page: int,
    member_tier: str,
) -> discord.Embed:
    """Build the overview embed for a specific page of subsystems."""
    num_pages = max(1, math.ceil(len(visible_list) / _PAGE_SIZE))
    page_items = visible_list[page * _PAGE_SIZE : (page + 1) * _PAGE_SIZE]
    visible_set = set(page_items)

    embed = discord.Embed(
        title="📚 Help Menu",
        description=(
            f"Page {page + 1} of {num_pages} — select a category from the dropdown."
            if num_pages > 1
            else "Select a category from the dropdown below."
        ),
        color=UTILITY_COLOR,
    )

    subsystems_by_name = dict(all_subsystems_sorted())
    for group in _TIER_GROUPS:
        group_tiers: set[str] = group["tiers"]
        entries: list[str] = []
        for name, meta in subsystems_by_name.items():
            if name not in visible_set:
                continue
            if meta.get("parent_hub"):
                continue
            if meta.get("visibility_tier") not in group_tiers:
                continue
            emoji = meta.get("emoji", "•")
            display = meta.get("display_name", name)
            desc = meta.get("description", "")
            entries.append(f"{emoji} **{display}** — {desc}")
        if entries:
            embed.add_field(name=group["label"], value="\n".join(entries), inline=False)

    if not embed.fields:
        embed.description = "No commands are available in this channel."
    return embed


async def resolve_help_panel_state(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, HelpPanelView]:
    """Resolve governance + build the Help-panel ``(embed, view)`` pair.

    Used by navigation buttons in other cogs / views (e.g.
    ``cogs.admin_cog._AdminPanelView.help_btn`` and
    ``views.mining.mine_view._MineResultsView.help_btn``) so they
    don't re-implement governance resolution + page-embed
    construction.

    Raises whatever ``governance_service.resolve_visibility`` raises;
    callers are responsible for catching to fall back to an in-place
    error embed.
    """
    gctx = GovernanceContext.from_interaction(interaction)
    vis_result = await governance_service.resolve_visibility(gctx)
    visible_list = [
        name
        for name, meta in all_subsystems_sorted()
        if name in vis_result.visible_subsystems and not meta.get("parent_hub")
    ]
    view = HelpPanelView(visible_list, page=0)
    embed = _build_page_embed(
        interaction.client,  # type: ignore[arg-type]
        visible_list,
        0,
        vis_result.member_tier,
    )
    return embed, view


@register
class HelpPanelView(PersistentView):
    """Persistent, paginated help panel — resolves the 25-item dropdown cap."""

    SUBSYSTEM = "help"

    def __init__(self, visible_list: list[str] | None = None, page: int = 0) -> None:
        super().__init__()
        self._visible = visible_list or []
        self._page = page
        self._num_pages = max(1, math.ceil(len(self._visible) / _PAGE_SIZE))
        self._rebuild_items()

    def _rebuild_items(self) -> None:
        self.clear_items()
        page_items = self._visible[
            self._page * _PAGE_SIZE : (self._page + 1) * _PAGE_SIZE
        ]

        if page_items:
            options = [
                discord.SelectOption(
                    label=SUBSYSTEMS.get(name, {}).get("display_name", name),
                    value=name,
                    description=SUBSYSTEMS.get(name, {}).get("description", "")[:100],
                    emoji=SUBSYSTEMS.get(name, {}).get("emoji"),
                )
                for name in page_items
            ]
            select = discord.ui.Select(  # type: ignore[var-annotated]
                custom_id="help:select",
                placeholder="Choose a category…",
                min_values=1,
                max_values=1,
                options=options,
                row=0,
            )
            select.callback = self._on_select  # type: ignore[method-assign]
            self.add_item(select)

        prev_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="◀ Prev",
            custom_id="help:prev",
            style=discord.ButtonStyle.grey,
            disabled=(self._page == 0),
            row=1,
        )
        prev_btn.callback = self._on_prev  # type: ignore[method-assign]
        self.add_item(prev_btn)

        if self._num_pages > 1:
            page_lbl = discord.ui.Button(  # type: ignore[var-annotated]
                label=f"Page {self._page + 1}/{self._num_pages}",
                custom_id="help:page_lbl",
                style=discord.ButtonStyle.grey,
                disabled=True,
                row=1,
            )
            self.add_item(page_lbl)

        next_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="Next ▶",
            custom_id="help:next",
            style=discord.ButtonStyle.grey,
            disabled=(self._page >= self._num_pages - 1),
            row=1,
        )
        next_btn.callback = self._on_next  # type: ignore[method-assign]
        self.add_item(next_btn)

    async def _resolve_visible(
        self,
        interaction: discord.Interaction,
    ) -> tuple[list[str], str]:
        """Return (sorted visible subsystem names, member_tier) via governance."""
        gctx = GovernanceContext.from_interaction(interaction)
        vis_result = await governance_service.resolve_visibility(gctx)
        visible_set = vis_result.visible_subsystems
        visible_list = [
            name
            for name, meta in all_subsystems_sorted()
            if name in visible_set and not meta.get("parent_hub")
        ]
        return visible_list, vis_result.member_tier

    async def _on_select(self, interaction: discord.Interaction) -> None:
        """Open the chosen subsystem in place — direct navigation, no extra clicks.

        Resolution order:
          1. If the cog exposes ``build_help_menu_view(interaction)``, call it
             and replace the help message with the subsystem's actual panel
             (with a "↩ Back to Help" button appended so the user can return).
          2. Otherwise, fall back to the inline command-list embed.  This
             preserves backwards compatibility for cogs that have not yet
             adopted the direct-navigation hook.
        """
        subsystem_name = interaction.data["values"][0]  # type: ignore[typeddict-item]
        cog = _cog_for_subsystem(interaction.client, subsystem_name)  # type: ignore[arg-type]
        if not cog:
            await interaction.response.send_message(
                "That category is no longer loaded.",
                ephemeral=True,
            )
            return

        # Direct-navigation hook (Phase 5 — help UX completion).
        build_panel = getattr(cog, "build_help_menu_view", None)
        if callable(build_panel):
            try:
                embed, sub_view = await build_panel(interaction)
                _attach_back_to_help_button(sub_view, self._visible, self._page)
                await interaction.response.edit_message(embed=embed, view=sub_view)
                return
            except Exception as exc:
                logger.warning(
                    "build_help_menu_view failed for subsystem=%r — falling back "
                    "to inline command list: %s",
                    subsystem_name,
                    exc,
                    exc_info=True,
                )

        # Fallback: inline cog command list, keep help view's nav controls.
        prefix = getattr(interaction.client, "command_prefix", "!")
        if callable(prefix):
            prefix = "!"
        embed = build_cog_embed(cog, prefix, subsystem_name)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        visible_list, member_tier = await self._resolve_visible(interaction)
        new_page = max(0, self._page - 1)
        new_view = HelpPanelView(visible_list, new_page)
        embed = _build_page_embed(
            interaction.client,  # type: ignore[arg-type]
            visible_list,
            new_page,
            member_tier,
        )
        await interaction.response.edit_message(embed=embed, view=new_view)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        visible_list, member_tier = await self._resolve_visible(interaction)
        num_pages = max(1, math.ceil(len(visible_list) / _PAGE_SIZE))
        new_page = min(self._page + 1, num_pages - 1)
        new_view = HelpPanelView(visible_list, new_page)
        embed = _build_page_embed(
            interaction.client,  # type: ignore[arg-type]
            visible_list,
            new_page,
            member_tier,
        )
        await interaction.response.edit_message(embed=embed, view=new_view)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(name="help", aliases=["hilfe"])
    async def help_command(self, ctx: commands.Context, *, category: str = None):
        """Shows available commands. Pass a category name for details."""
        gctx = GovernanceContext.from_ctx(ctx)
        vis_result = await governance_service.resolve_visibility(gctx)
        visible_set = vis_result.visible_subsystems
        member_tier = vis_result.member_tier
        # parent_hub children are reachable via their hub and via typed
        # commands; they're hidden from the overview/select. The typed
        # category-lookup branch below iterates SUBSYSTEMS directly and
        # is therefore unaffected by this filter.
        visible_list = [
            name
            for name, meta in all_subsystems_sorted()
            if name in visible_set and not meta.get("parent_hub")
        ]

        if category:
            for name, meta in SUBSYSTEMS.items():
                if name not in visible_set:
                    continue
                if category.lower() in (
                    name.lower(),
                    meta.get("display_name", "").lower(),
                ):
                    cog = _cog_for_subsystem(self.bot, name)
                    if cog:
                        await ctx.send(
                            embed=build_cog_embed(cog, ctx.prefix or "!", name),
                            delete_after=60,
                        )
                        return

            cog = self.bot.get_cog(category) or self.bot.get_cog(category + "Cog")
            cmd = self.bot.get_command(category)
            if cog:
                await ctx.send(
                    embed=build_cog_embed(cog, ctx.prefix or "!"),
                    delete_after=60,
                )
                return
            if cmd:
                prefix = ctx.prefix or "!"
                embed = discord.Embed(
                    title=f"`{prefix}{cmd.name}`",
                    description=cmd.help or "No description.",
                    color=UTILITY_COLOR,
                )
                if cmd.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(f"`{a}`" for a in cmd.aliases),
                    )
                embed.add_field(
                    name="Usage",
                    value=f"`{prefix}{cmd.name}{(' ' + cmd.signature) if cmd.signature else ''}`",
                    inline=False,
                )
                await ctx.send(embed=embed, delete_after=60)
                return
            await ctx.send(
                f"No command or category named `{category}` found.",
                delete_after=10,
            )
            return

        view = HelpPanelView(visible_list, page=0)
        embed = _build_page_embed(self.bot, visible_list, 0, member_tier)

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


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
    logger.info("HelpCog loaded.")
