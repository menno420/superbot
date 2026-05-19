"""Games hub view — routes to per-game help/hub panels.

The Games subsystem is a router-only hub. It discovers its children
dynamically from :data:`utils.subsystem_registry.SUBSYSTEMS` by filtering
for entries whose ``parent_hub`` equals ``"games"``, then groups them by
``hub_group`` (currently ``"competitive"`` and ``"activities"``).

Game logic stays in each individual cog (Blackjack, RPS, Deathmatch,
Mining, Counting, Chain). This view is a navigation surface only:

* The select dropdown forwards to the child cog's
  :meth:`build_help_menu_view` hook, identical to how ``!help`` routes
  into a subsystem.
* A "↩ Back to Games" button is attached to the child view via
  :func:`views.navigation.attach_back_button` (S2). The closure captures
  the original author so the rebuilt hub remains invoker-restricted.

Direct ``!games`` invocation: the hub opens with the select only.
``!help`` is the way back to the help menu in that flow, mirroring
``!countingmenu`` / ``!minemenu`` / ``!adminmenu`` conventions.

When the hub is surfaced via ``!help`` → "Games", :func:`HelpPanelView`
appends the "↩ Back to Help" button itself — so this view never adds
that button, avoiding duplicates.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from services import governance_service
from services.governance_service import GovernanceContext
from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import GAME_COLOR
from views.base import HubView
from views.navigation import attach_back_button

logger = logging.getLogger("bot.views.games")

# Hub group rendering order. Groups not listed sort last (alphabetically).
_GROUP_ORDER: dict[str, int] = {"competitive": 0, "activities": 1}

_GROUP_HEADINGS: dict[str, str] = {
    "competitive": "🏆 Competitive",
    "activities": "🎲 Activities",
}


def discover_game_children() -> list[tuple[str, dict]]:
    """Return SUBSYSTEMS entries that route to the Games hub.

    Sorted by ``hub_group`` (competitive before activities), then by
    ``ui_priority``, then by subsystem key — fully deterministic so the
    UI ordering is stable.
    """
    children = [
        (name, dict(meta))
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "games"
    ]
    children.sort(
        key=lambda item: (
            _GROUP_ORDER.get(item[1].get("hub_group") or "", 99),
            item[1].get("ui_priority", 99),
            item[0],
        ),
    )
    return children


def build_games_hub_embed(
    children: list[tuple[str, dict]] | None = None,
) -> discord.Embed:
    """Build the embed shown by :class:`GamesHubView`.

    When ``children`` is supplied (typically pre-filtered by
    :func:`build_games_hub_panel`), the embed only describes those
    subsystems. When ``None``, falls back to the unfiltered list — used
    by callers that construct the view directly (tests, persistent
    re-registration).
    """
    embed = discord.Embed(
        title="🎮 Games Hub",
        description=(
            "Pick a game from the dropdown to see its commands and modes. "
            "Typed shortcuts (e.g. `!blackjack`, `!mine`) still work."
        ),
        color=GAME_COLOR,
    )

    if children is None:
        children = discover_game_children()

    by_group: dict[str, list[tuple[str, dict]]] = {}
    for name, meta in children:
        group = meta.get("hub_group") or "other"
        by_group.setdefault(group, []).append((name, meta))

    if not by_group:
        embed.add_field(
            name="No games configured",
            value="No subsystems route to the Games hub yet.",
            inline=False,
        )
        return embed

    seen_groups = sorted(
        by_group,
        key=lambda g: (_GROUP_ORDER.get(g, 99), g),
    )
    for group in seen_groups:
        members = by_group[group]
        heading = _GROUP_HEADINGS.get(group, group.title())
        lines = [
            f"{meta.get('emoji', '')} **{meta['display_name']}** — "
            f"{meta['description']}".strip()
            for _, meta in members
        ]
        embed.add_field(name=heading, value="\n".join(lines), inline=False)

    embed.set_footer(text="Only you can interact with this panel.")
    return embed


async def build_games_hub_panel(
    author: discord.Member | discord.User,
    *,
    interaction: discord.Interaction | None = None,
    ctx: commands.Context | None = None,
    visible: set[str] | None = None,
) -> tuple[discord.Embed, GamesHubView]:
    """Resolve governance, filter children, and build the hub panel.

    Single source of truth for opening the Games hub. Callers are:

    * ``!games`` prefix command → pass ``ctx``.
    * ``GamesCog.build_help_menu_view`` (help hook) → pass ``interaction``.
    * Back-to-Games closure rebuilds → pass ``interaction``.

    When ``visible`` is supplied the caller has already resolved
    visibility (e.g. inside an outer closure) and we skip the
    re-resolution. Otherwise the factory builds a
    :class:`GovernanceContext` from whichever of ``interaction`` /
    ``ctx`` was provided and calls
    ``governance_service.resolve_visibility``.

    Filtered children are passed to both the embed builder and the
    view constructor so the surface stays in sync.
    """
    if visible is None:
        if interaction is not None:
            gctx = GovernanceContext.from_interaction(interaction)
        elif ctx is not None:
            gctx = GovernanceContext.from_ctx(ctx)
        else:
            raise ValueError(
                "build_games_hub_panel requires interaction or ctx "
                "when visible is not pre-resolved",
            )
        result = await governance_service.resolve_visibility(gctx)
        visible = result.visible_subsystems

    children = [
        (name, meta) for name, meta in discover_game_children() if name in visible
    ]
    embed = build_games_hub_embed(children)
    view = GamesHubView(author, children=children)
    return embed, view


def attach_back_to_games_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
) -> bool:
    """Append a "↩ Back to Games" control to a child view opened from the hub.

    Thin wrapper around :func:`views.navigation.attach_back_button` (S2).
    The parent-builder closure captures ``author`` so the rebuilt
    :class:`GamesHubView` remains invoker-restricted; the child list is
    re-discovered (and re-filtered through governance) at click time so
    the hub reflects the live state — not the snapshot from when the
    panel was opened. PR D: rebuild now routes through
    :func:`build_games_hub_panel` to apply governance filtering on the
    rebuilt hub.

    Returns ``False`` (no-op) if the view is already at Discord's
    25-component cap — ``attach_back_button`` logs a WARNING in that
    case so operators can see why a panel lost its back nav.
    """

    async def _build_games_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        return await build_games_hub_panel(author, interaction=interaction)

    return attach_back_button(
        view,
        label="↩ Back to Games",
        custom_id="games:back",
        parent_builder=_build_games_parent,
        row=4,
        style=discord.ButtonStyle.secondary,
        error_message="Could not reload the Games hub. Please try again.",
    )


def _build_no_panel_embed(name: str, meta: dict) -> discord.Embed:
    """Fallback embed for a child whose cog lacks ``build_help_menu_view``."""
    embed = discord.Embed(
        title=f"{meta.get('emoji', '')} {meta['display_name']}".strip(),
        description=meta.get("description", ""),
        color=meta.get("color", GAME_COLOR.value),
    )
    entries = meta.get("entry_points", ())
    if entries:
        embed.add_field(
            name="Commands",
            value="\n".join(f"`!{ep}`" for ep in entries),
            inline=False,
        )
    else:
        embed.add_field(
            name="Commands",
            value="_No commands declared for this subsystem._",
            inline=False,
        )
    embed.set_footer(text="Panel view not implemented yet.")
    return embed


class _GamesHubSelect(discord.ui.Select):
    """Dropdown listing every ``parent_hub == "games"`` child."""

    def __init__(self, children: list[tuple[str, dict]]) -> None:
        options: list[discord.SelectOption] = []
        for name, meta in children[:25]:  # Discord cap
            label = (meta.get("display_name") or name)[:100]
            description = (meta.get("description") or "")[:100] or None
            emoji = meta.get("emoji") or None
            options.append(
                discord.SelectOption(
                    label=label,
                    value=name,
                    description=description,
                    emoji=emoji,
                ),
            )
        if not options:
            # Discord rejects a Select with zero options; provide a sentinel.
            options.append(
                discord.SelectOption(
                    label="No games available",
                    value="__none__",
                    description="No subsystems route to the Games hub yet.",
                ),
            )
        super().__init__(
            placeholder="Choose a game…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="games:select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # ``self.view`` is the GamesHubView this select was added to.
        view = self.view
        if not isinstance(view, GamesHubView):
            await interaction.response.send_message(
                "This dropdown is no longer attached to the Games hub.",
                ephemeral=True,
            )
            return
        await view.handle_select(interaction, self.values[0])


class GamesHubView(HubView):
    """Router-only hub for the Games subsystem.

    Discovers ``parent_hub == "games"`` children from
    :data:`utils.subsystem_registry.SUBSYSTEMS` and surfaces them in a
    single select. Selecting a child calls that child cog's
    ``build_help_menu_view`` hook; if the hook is missing the hub falls
    back to a typed-command embed so the operator can still discover
    commands.

    The view itself contains zero game logic — pure routing.
    """

    SUBSYSTEM = "games"

    def __init__(
        self,
        author: discord.Member | discord.User,
        children: list[tuple[str, dict]] | None = None,
    ) -> None:
        super().__init__(author)
        # NOTE: discord.py's ``discord.ui.View`` uses ``self._children``
        # for its internal items list (see ``discord/ui/view.py``
        # `_init_children`). Naming our cached child-metadata list
        # ``self._children`` overwrites the items list and lets tuples
        # leak into the view's components — which fails serialization
        # when the view is sent to Discord. Use a distinct name.
        #
        # PR D: ``children`` is normally pre-filtered by
        # :func:`build_games_hub_panel` so only governance-visible
        # subsystems render. ``None`` falls back to the unfiltered
        # discovery — used by tests and any caller that constructs
        # the view directly. Click-time recheck in :meth:`handle_select`
        # still gates correctly even on the unfiltered path.
        if children is None:
            children = discover_game_children()
        self._game_children = children
        self.add_item(_GamesHubSelect(self._game_children))

    async def handle_select(
        self,
        interaction: discord.Interaction,
        sub_name: str,
    ) -> None:
        """Open the selected child's help panel in place."""
        if sub_name == "__none__":
            await interaction.response.send_message(
                "No games are routed to the Games hub yet.",
                ephemeral=True,
            )
            return

        meta = SUBSYSTEMS.get(sub_name)
        if meta is None or meta.get("parent_hub") != "games":
            await interaction.response.send_message(
                "That game is no longer routed to the Games hub.",
                ephemeral=True,
            )
            return

        # PR D: click-time governance recheck. If the subsystem has
        # become invisible between render and click (visibility change,
        # role removal, channel scope override), fail closed with an
        # ephemeral. ``resolve_visibility`` is cached by
        # ``(guild_id, channel_id, tier, role_ids)`` so the re-check is
        # essentially free in steady state.
        gctx = GovernanceContext.from_interaction(interaction)
        vis_result = await governance_service.resolve_visibility(gctx)
        if sub_name not in vis_result.visible_subsystems:
            await interaction.response.send_message(
                "That feature is no longer available in this channel.",
                ephemeral=True,
            )
            return

        # Local import keeps the helper out of module-import time and
        # avoids dragging the help cog into every consumer of this view.
        from cogs.help_cog import _cog_for_subsystem

        cog = _cog_for_subsystem(interaction.client, sub_name)  # type: ignore[arg-type]
        if cog is None:
            embed = _build_no_panel_embed(sub_name, dict(meta))
            attach_back_to_games_button(self, self._author)
            await interaction.response.edit_message(embed=embed, view=self)
            return

        build_panel = getattr(cog, "build_help_menu_view", None)
        if not callable(build_panel):
            embed = _build_no_panel_embed(sub_name, dict(meta))
            attach_back_to_games_button(self, self._author)
            await interaction.response.edit_message(embed=embed, view=self)
            return

        try:
            embed, sub_view = await build_panel(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash
            logger.warning(
                "Games hub: build_help_menu_view failed for subsystem=%r: %s",
                sub_name,
                exc,
                exc_info=True,
            )
            fallback = _build_no_panel_embed(sub_name, dict(meta))
            attach_back_to_games_button(self, self._author)
            await interaction.response.edit_message(embed=fallback, view=self)
            return

        attach_back_to_games_button(sub_view, self._author)
        await interaction.response.edit_message(embed=embed, view=sub_view)
