"""Help panel views + paginated overview embed (decomposed from help_cog).

The two persistent Help views — :class:`HelpCategoryView` (the S3 mother-hub
category index ``!help`` opens) and :class:`HelpPanelView` (the legacy
paginated Advanced browser) — plus the page-embed builder they share.
Extracted from ``cogs/help_cog.py`` when HLP-3 pushed it past the 800-LOC
cog ceiling; ``help_cog`` re-exports these names, so its import surface is
unchanged (the F-3 convention: ``cogs/<sub>_cog.py`` is the Discord-facing
surface, ``cogs/<sub>/`` holds the helpers).

Cycle discipline: imports of ``cogs.help_cog`` helpers
(``_resolve_projection`` / ``_cog_for_subsystem`` / ``build_cog_embed`` /
``_attach_back_to_help_button``) are **function-local and late-bound** —
the same pattern ``cogs.help.route`` uses — so the import graph stays
acyclic and test monkeypatches on the ``help_cog`` module keep biting.
"""

from __future__ import annotations

import logging
import math

import discord

from cogs.help.route import HelpOpener
from cogs.help.route import open_route as _open_route
from cogs.help.route import resolve_route as _resolve_route
from core.runtime.persistent_views import PersistentView, register
from services.governance_service import GovernanceContext
from services.help_projection import HelpProjection
from utils.hub_registry import ALL_COMMANDS_KEY
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


def _build_page_embed(
    bot: object,
    visible_list: list[str],
    page: int,
    member_tier: str,
    *,
    projection: HelpProjection | None = None,
) -> discord.Embed:
    """Build the overview embed for a specific page of subsystems.

    HLP-3: display fields come from the projection's presentations when
    given (guild overlay renames apply); tier grouping and parent-hub
    structure stay registry identity, never overlay-affected.
    """
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
            presentation = (
                projection.subsystem_presentation(name)
                if projection is not None
                else None
            )
            if presentation is not None:
                emoji = presentation.emoji
                display = presentation.display_name
                desc = presentation.description
            else:
                emoji = meta.get("emoji", "•")
                display = meta.get("display_name", name)
                desc = meta.get("description", "")
            entries.append(f"{emoji} **{display}** — {desc}")
        if entries:
            embed.add_field(name=group["label"], value="\n".join(entries), inline=False)

    if not embed.fields:
        embed.description = "No commands are available in this channel."
    return embed


@register
class HelpPanelView(PersistentView):
    """Persistent, paginated help panel — resolves the 25-item dropdown cap.

    HLP-3: ``projection`` carries the guild's effective presentations
    (overlay renames) for the dropdown options; ``None`` renders registry
    defaults (restore symmetry / tests). Click-time callbacks re-resolve a
    fresh projection regardless.
    """

    SUBSYSTEM = "help"

    def __init__(
        self,
        visible_list: list[str] | None = None,
        page: int = 0,
        *,
        projection: HelpProjection | None = None,
    ) -> None:
        super().__init__()
        self._visible = visible_list or []
        self._page = page
        self._num_pages = max(1, math.ceil(len(self._visible) / _PAGE_SIZE))
        self._projection = projection
        self._rebuild_items()

    def _option_fields(self, name: str) -> tuple[str, str, str | None]:
        """(label, description, emoji) for one subsystem option."""
        presentation = (
            self._projection.subsystem_presentation(name)
            if self._projection is not None
            else None
        )
        if presentation is not None:
            return (
                presentation.display_name,
                presentation.description,
                presentation.emoji or None,
            )
        meta = SUBSYSTEMS.get(name, {})
        return (
            meta.get("display_name", name),
            meta.get("description", ""),
            meta.get("emoji"),
        )

    def _rebuild_items(self) -> None:
        self.clear_items()
        page_items = self._visible[
            self._page * _PAGE_SIZE : (self._page + 1) * _PAGE_SIZE
        ]

        if page_items:
            options = []
            for name in page_items:
                label, description, emoji = self._option_fields(name)
                options.append(
                    discord.SelectOption(
                        label=label[:100],
                        value=name,
                        description=description[:100],
                        emoji=emoji,
                    ),
                )
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
    ) -> tuple[list[str], HelpProjection]:
        """Return (sorted visible subsystem names, fresh projection) via
        the projection seam (HLP-2/3).
        """
        # Late-bound so test monkeypatches on help_cog keep working.
        from cogs.help_cog import _resolve_projection

        gctx = GovernanceContext.from_interaction(interaction)
        projection = await _resolve_projection(gctx)
        return projection.advanced_subsystems(), projection

    async def _on_select(self, interaction: discord.Interaction) -> None:
        """Open the chosen subsystem in place — direct navigation, no extra clicks.

        HLP-2: re-resolves governance and checks the selected target against
        the projection **at click time** (pre-seam, a stale dropdown opened
        any subsystem regardless of current visibility — audit §3).

        Resolution order:
          1. If the cog exposes ``build_help_menu_view(interaction)``, call it
             and replace the help message with the subsystem's actual panel
             (with a "↩ Back to Help" button appended so the user can return).
          2. Otherwise, fall back to the inline command-list embed.  This
             preserves backwards compatibility for cogs that have not yet
             adopted the direct-navigation hook.
        """
        # Late-bound to cogs.help_cog (the canonical patch seam for tests).
        from cogs.help_cog import (
            _attach_back_to_help_button,
            _cog_for_subsystem,
            _resolve_projection,
            build_cog_embed,
        )

        subsystem_name = interaction.data["values"][0]  # type: ignore[typeddict-item]

        gctx = GovernanceContext.from_interaction(interaction)
        projection = await _resolve_projection(gctx)
        if not projection.is_subsystem_advertised(subsystem_name):
            await interaction.response.send_message(
                "That category is no longer available.",
                ephemeral=True,
            )
            return

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
        import config

        embed = build_cog_embed(
            cog,
            config.PREFIX,
            subsystem_name,
            projection=projection,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        visible_list, projection = await self._resolve_visible(interaction)
        new_page = max(0, self._page - 1)
        new_view = HelpPanelView(visible_list, new_page, projection=projection)
        embed = _build_page_embed(
            interaction.client,
            visible_list,
            new_page,
            projection.member_tier,
            projection=projection,
        )
        await interaction.response.edit_message(embed=embed, view=new_view)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        visible_list, projection = await self._resolve_visible(interaction)
        num_pages = max(1, math.ceil(len(visible_list) / _PAGE_SIZE))
        new_page = min(self._page + 1, num_pages - 1)
        new_view = HelpPanelView(visible_list, new_page, projection=projection)
        embed = _build_page_embed(
            interaction.client,
            visible_list,
            new_page,
            projection.member_tier,
            projection=projection,
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

    Stateless aside from ``_projection`` cached at construction time
    so the dropdown options match the user's effective access (HLP-2:
    hub tier floor **and** host-subsystem governance visibility — the
    same seam every other Help path consumes). The select callback
    re-resolves visibility before opening a hub so a user who lost a
    tier between Help renders gets the current state, not the stale
    snapshot.

    ``member_tier`` (without a projection) falls back to the static
    registry-defaults projection — persistent-view restore symmetry and
    tests only; live callers pass ``projection``.
    """

    SUBSYSTEM = "help"

    def __init__(
        self,
        member_tier: str | None = None,
        *,
        projection: HelpProjection | None = None,
    ) -> None:
        super().__init__()
        self._projection = projection or HelpProjection.registry_defaults(
            member_tier or "user",
        )
        self._rebuild_items()

    def _rebuild_items(self) -> None:
        self.clear_items()
        options: list[discord.SelectOption] = []
        for hub in self._projection.visible_hubs():
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
        # Late-bound to cogs.help_cog (the canonical patch seam for tests).
        from cogs.help_cog import _attach_back_to_help_button, _resolve_projection

        value = interaction.data["values"][0]  # type: ignore[typeddict-item]

        # Re-resolve governance at click time so the user's current
        # visibility/tier drives the next view, not the snapshot from
        # when the category panel was first rendered.
        gctx = GovernanceContext.from_interaction(interaction)
        projection = await _resolve_projection(gctx)

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
            projection=projection,
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


__all__ = [
    "_PAGE_SIZE",
    "HelpCategoryView",
    "HelpPanelView",
    "_build_page_embed",
]
