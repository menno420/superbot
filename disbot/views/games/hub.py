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
* A "↩ Back to Games" button is attached to the child view so users can
  return to the hub. The Phase 2 roadmap step (a shared back-nav helper)
  is deferred to Phase 3.5; until then, the inline factory below mirrors
  the existing patterns in ``help_cog.py``, ``admin_cog.py``, and
  ``views/settings/subsystem_view.py``.

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

from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import GAME_COLOR
from views.base import HubView

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


def build_games_hub_embed() -> discord.Embed:
    """Build the embed shown by :class:`GamesHubView`."""
    embed = discord.Embed(
        title="🎮 Games Hub",
        description=(
            "Pick a game from the dropdown to see its commands and modes. "
            "Typed shortcuts (e.g. `!blackjack`, `!mine`) still work."
        ),
        color=GAME_COLOR,
    )

    by_group: dict[str, list[tuple[str, dict]]] = {}
    for name, meta in discover_game_children():
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


def attach_back_to_games_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
) -> bool:
    """Append a "↩ Back to Games" control to a child view opened from the hub.

    No-op (returns ``False``) if the view already has Discord's 25-child
    limit. The callback rebuilds a fresh :class:`GamesHubView` so the
    child list reflects the current registry on click.

    Inline factory mirroring ``cogs.help_cog._attach_back_to_help_button``
    and friends. Will be migrated into a shared helper in Phase 3.5.
    """
    if len(view.children) >= 25:
        logger.warning(
            "Back-to-games button skipped — %s already has 25 children.",
            type(view).__name__,
        )
        return False

    back_btn = discord.ui.Button(  # type: ignore[var-annotated]
        label="↩ Back to Games",
        custom_id="games:back",
        style=discord.ButtonStyle.secondary,
        row=4,
    )

    async def _back_callback(interaction: discord.Interaction) -> None:
        new_view = GamesHubView(author)
        await interaction.response.edit_message(
            embed=build_games_hub_embed(),
            view=new_view,
        )

    back_btn.callback = _back_callback  # type: ignore[method-assign]
    view.add_item(back_btn)
    return True


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

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        # NOTE: discord.py's ``discord.ui.View`` uses ``self._children``
        # for its internal items list (see ``discord/ui/view.py``
        # `_init_children`). Naming our cached child-metadata list
        # ``self._children`` overwrites the items list and lets tuples
        # leak into the view's components — which fails serialization
        # when the view is sent to Discord. Use a distinct name.
        self._game_children = discover_game_children()
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
