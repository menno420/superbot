from __future__ import annotations

import logging
import math

import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.help.route import HUB_PANEL_BUILDERS as _HUB_PANEL_BUILDERS
from cogs.help.route import (
    HelpOpener,
    HelpRoute,
)
from cogs.help.route import discovery_label as _discovery_label
from cogs.help.route import open_route as _open_route
from cogs.help.route import resolve_route as _resolve_route
from core.runtime.persistent_views import PersistentView, register
from services import governance_service
from services.governance_service import GovernanceContext
from utils.hub_registry import ALL_COMMANDS_KEY, hubs_for_tier
from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted
from utils.ui_constants import ADMIN_COLOR, GENERAL_COLOR, MOD_COLOR, UTILITY_COLOR

logger = logging.getLogger("bot")

# Re-exports kept for test compatibility — the canonical definitions
# live in ``cogs.help.route``. The Help route model is shared by the
# typed ``!help <name>`` command and the Help dropdown so the same
# name produces the same destination regardless of entry point.
__all__ = [
    "HelpOpener",
    "HelpRoute",
    "_HUB_PANEL_BUILDERS",
    "_open_route",
    "_resolve_route",
]

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


def _classification_hidden(cmd: commands.Command) -> bool:
    """Return ``True`` if classification metadata hides ``cmd`` from help.

    Thin wrapper around the canonical
    :func:`core.runtime.command_surface_ledger.is_command_hidden_from_help`
    so help-rendering code consumes the **same policy** the ledger
    surface uses — there is no second hidden-set declaration to drift
    against.  An unknown / missing classification keeps the command
    visible (the policy default is "show").
    """
    # Function-local import keeps the help cog's import graph
    # consistent with the cycle-sensitive discipline used in
    # ``cogs.help.route``.
    from core.runtime.command_surface_ledger import is_command_hidden_from_help

    return is_command_hidden_from_help(cmd)


def _get_visible_commands(cog: commands.Cog) -> list[commands.Command]:
    return [
        cmd
        for cmd in cog.get_commands()
        if not cmd.hidden and cmd.enabled and not _classification_hidden(cmd)
    ]


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
        vis_result = await governance_service.resolve_visibility(gctx)
        new_view = HelpCategoryView(vis_result.member_tier)
        embed = build_categories_overview_embed(vis_result.member_tier)
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


def build_categories_overview_embed(member_tier: str) -> discord.Embed:
    """Build the top-level Help embed showing mother-hub categories.

    Iterates :data:`utils.hub_registry.HUBS`, filters to hubs visible at
    ``member_tier`` via :func:`hubs_for_tier`, and always appends the
    permanent "Advanced / All Commands" fallback row. Each hub row is a
    uniform two-line shape — purpose + typed entry command — with no
    ``Includes:`` line. Child rosters live inside each hub panel.
    """
    embed = discord.Embed(
        title="📚 Help Menu",
        description="Pick a category from the dropdown below.",
        color=UTILITY_COLOR,
    )

    for hub in hubs_for_tier(member_tier):
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
    vis_result = await governance_service.resolve_visibility(gctx)
    view = HelpCategoryView(vis_result.member_tier)
    embed = build_categories_overview_embed(vis_result.member_tier)
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
                _attach_back_to_help_button(sub_view)
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
        # RC-14: the prefix is operator-configurable (config.PREFIX / BOT_PREFIX);
        # don't hardcode "!" on the slash-help path.
        prefix = config.PREFIX
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


@register
class HelpCategoryView(PersistentView):
    """Top-level Help — mother-hub category index (S3).

    Replaces the pre-S3 paginated subsystem-list view as the surface
    ``!help`` opens. The dropdown shows one option per visible mother
    hub plus a permanent "All Commands / Advanced" fallback that swaps
    the view in place to :class:`HelpPanelView` (the legacy paginated
    list, now reachable only via that option).

    SUBSYSTEM is ``"help"`` — overwrites :class:`HelpPanelView`'s
    registration in the persistent-view registry. That's intentional:
    help anchors are skipped at restart (see
    ``message_anchor_manager.restore_anchors``), so the registration
    is effectively unused for restore but is kept for symmetry with
    the rest of the codebase.

    Stateless aside from ``_member_tier`` cached at construction time
    so the dropdown options match the user's governance tier. The
    select callback re-resolves visibility before opening a hub so a
    user who lost a tier between Help renders gets the current state,
    not the stale snapshot.
    """

    SUBSYSTEM = "help"

    def __init__(self, member_tier: str | None = None) -> None:
        super().__init__()
        self._member_tier = member_tier or "user"
        self._rebuild_items()

    def _rebuild_items(self) -> None:
        self.clear_items()
        visible_hubs = hubs_for_tier(self._member_tier)
        options: list[discord.SelectOption] = []
        for hub in visible_hubs:
            options.append(
                discord.SelectOption(
                    label=hub.display_name[:100],
                    value=hub.key,
                    description=hub.purpose[:100],
                    emoji=hub.emoji or None,
                ),
            )
        # All Commands / Advanced is permanent — guarantees discoverability
        # for every visible subsystem even when no mother hub owns it.
        options.append(
            discord.SelectOption(
                label="All Commands / Advanced",
                value=ALL_COMMANDS_KEY,
                description="Browse every visible command directly.",
                emoji="📋",
            ),
        )
        select = discord.ui.Select(  # type: ignore[var-annotated]
            custom_id="help_categories:select",
            placeholder="Pick a category…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        select.callback = self._on_select  # type: ignore[method-assign]
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        value = interaction.data["values"][0]  # type: ignore[typeddict-item]

        # Re-resolve governance at click time so the user's current
        # visibility/tier drives the next view, not the snapshot from
        # when the category panel was first rendered.
        gctx = GovernanceContext.from_interaction(interaction)
        vis_result = await governance_service.resolve_visibility(gctx)

        # The sentinel "All Commands / Advanced" routes through the same
        # resolver as everything else — keyed by the canonical "advanced"
        # alias so typed Help and the dropdown share one branch.
        name = "advanced" if value == ALL_COMMANDS_KEY else value
        opener = HelpOpener.from_interaction(interaction)
        route = _resolve_route(name, bot=opener.client)

        if route.kind == "unknown":
            await interaction.response.send_message(
                "That category is no longer available.",
                ephemeral=True,
            )
            return

        embed, sub_view = await _open_route(
            route,
            opener,
            visible_subsystems=vis_result.visible_subsystems,
            member_tier=vis_result.member_tier,
        )

        if sub_view is None:
            # Embed-only fallback (e.g. hub builder failed) — surface as
            # an ephemeral so the category panel stays intact.
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
            return

        # Attach Back-to-Help on every interactive surface opened from
        # the category index. ``HelpPanelView`` (the Advanced branch)
        # already provides its own pagination; the back button still
        # gives the user a one-click return to the category index.
        _attach_back_to_help_button(sub_view)
        await interaction.response.edit_message(embed=embed, view=sub_view)


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
                visible_subsystems=visible_set,
                member_tier=member_tier,
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
        view = HelpCategoryView(member_tier)
        embed = build_categories_overview_embed(member_tier)

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
        vis_result = await governance_service.resolve_visibility(gctx)
        visible_set = vis_result.visible_subsystems
        member_tier = vis_result.member_tier

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
                visible_subsystems=visible_set,
                member_tier=member_tier,
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
