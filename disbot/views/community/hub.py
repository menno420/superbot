"""Community hub view (S9).

The Community subsystem is a router-only hub with no business logic
of its own. Per the mother-hub map, it groups progression and
community-activity subsystems whose primary owners are spread across
the codebase:

* **XP** and **Roles** are the primary children. Discovered from
  ``SUBSYSTEMS`` where ``parent_hub == "community"``.
* **Counting**, **Chain**, and **Leaderboard** appear as **cross-links**
  — their primary homes stay under Games (counting/chain) and Economy
  (leaderboard). Discovered from
  ``utils.hub_registry.get_hub("community").cross_link_children``.

Mirrors the Games hub pattern (``views.games.hub:discover_game_children``)
so the source of truth is the registry, not a hardcoded view-local
tuple. PR #4 migrated the view here from the previous ``_HUB_CHILDREN``
literal.

Five children fit comfortably under the hub-ui-standard button
threshold (≤8 buttons preferred over a dropdown). Layout: primary
children on row 0 with primary style, cross-links on row 1 with
secondary style. Back-nav is attached by ``HelpCategoryView`` when
the hub is surfaced from ``!help``; the direct ``!community`` entry
shows the hub without a back button, matching the ``!games`` pattern.
"""

from __future__ import annotations

import logging

import discord

from utils.hub_registry import get_hub
from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import GENERAL_COLOR
from views.base import HubView

logger = logging.getLogger("bot.views.community")


def discover_community_children() -> (
    tuple[list[tuple[str, dict]], list[tuple[str, dict]]]
):
    """Return ``(primary, cross_link)`` lists of (subsystem, meta) pairs.

    Primary children come from ``SUBSYSTEMS`` filtered by
    ``parent_hub == "community"``, sorted by ``ui_priority`` then key
    for determinism (matches the Games hub ordering rule).

    Cross-link children come from
    ``hub_registry.get_hub("community").cross_link_children`` in
    declared order. Unknown / missing subsystem keys are dropped with
    a WARNING — the hub stays functional even if a cross-link points
    at a subsystem that was unloaded.
    """
    primary = [
        (name, dict(meta))
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "community"
    ]
    primary.sort(key=lambda item: (item[1].get("ui_priority", 99), item[0]))

    cross_link: list[tuple[str, dict]] = []
    hub = get_hub("community")
    if hub is not None:
        for key in hub.cross_link_children:
            meta = SUBSYSTEMS.get(key)
            if meta is None:
                logger.warning(
                    "community hub cross_link_children %r is not in SUBSYSTEMS",
                    key,
                )
                continue
            cross_link.append((key, dict(meta)))

    return primary, cross_link


def _format_child_label(subsystem: str, meta: dict) -> str:
    """Build a button label from registry metadata.

    Mirrors the Games hub which uses
    ``meta.get("display_name") or name`` plus the subsystem emoji.
    """
    emoji = meta.get("emoji") or "•"
    display = meta.get("display_name") or subsystem
    return f"{emoji} {display}"


def build_community_hub_embed() -> discord.Embed:
    """Build the embed shown by :class:`CommunityHubView`.

    Description is generated from the discovered children so it stays
    in sync with the registry. The "Progression" / "Community games &
    standings" group headings are hardcoded — they are presentational
    framing, not metadata.
    """
    primary, cross_link = discover_community_children()
    parts = ["Pick a community feature below."]

    if primary:
        parts.append("\n**Progression**")
        for name, meta in primary:
            emoji = meta.get("emoji") or "•"
            display = meta.get("display_name") or name
            desc = meta.get("description") or ""
            parts.append(f"• {emoji} **{display}** — {desc}".rstrip(" —"))

    if cross_link:
        parts.append("\n**Community games & standings**")
        for name, meta in cross_link:
            emoji = meta.get("emoji") or "•"
            display = meta.get("display_name") or name
            desc = meta.get("description") or ""
            parts.append(f"• {emoji} **{display}** — {desc}".rstrip(" —"))

    embed = discord.Embed(
        title="🌱 Community Hub",
        description="\n".join(parts),
        color=GENERAL_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


class _CommunityChildButton(discord.ui.Button):
    """A button on the Community hub that opens a child cog's
    ``build_help_menu_view`` in place.
    """

    def __init__(
        self,
        *,
        subsystem: str,
        label: str,
        style: discord.ButtonStyle,
        row: int,
    ) -> None:
        super().__init__(
            label=label,
            style=style,
            custom_id=f"community:open:{subsystem}",
            row=row,
        )
        self._subsystem = subsystem

    async def callback(self, interaction: discord.Interaction) -> None:
        # Local import keeps the help cog out of module-import time.
        from cogs.help_cog import _cog_for_subsystem

        cog = _cog_for_subsystem(interaction.client, self._subsystem)  # type: ignore[arg-type]
        if cog is None:
            await interaction.response.send_message(
                f"The {self._subsystem!r} subsystem is not loaded right now.",
                ephemeral=True,
            )
            return

        build_panel = getattr(cog, "build_help_menu_view", None)
        if not callable(build_panel):
            await interaction.response.send_message(
                f"The {self._subsystem!r} subsystem has no panel yet.",
                ephemeral=True,
            )
            return

        try:
            embed, sub_view = await build_panel(interaction)
        except Exception as exc:  # noqa: BLE001 — nav must not crash
            logger.warning(
                "CommunityHubView: build_help_menu_view failed for %r: %s",
                self._subsystem,
                exc,
                exc_info=True,
            )
            await interaction.response.send_message(
                f"Could not open the {self._subsystem!r} panel — see bot logs.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(embed=embed, view=sub_view)


class CommunityHubView(HubView):
    """Router-only hub for the Community subsystem.

    Discovers primary children from ``SUBSYSTEMS`` (``parent_hub ==
    "community"``) and cross-links from ``hub_registry.get_hub
    ("community").cross_link_children``. Every button forwards to the
    target cog's existing ``build_help_menu_view`` hook — no business
    logic lives in this view.
    """

    SUBSYSTEM = "community"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        primary, cross_link = discover_community_children()
        for subsystem, meta in primary:
            self.add_item(
                _CommunityChildButton(
                    subsystem=subsystem,
                    label=_format_child_label(subsystem, meta),
                    style=discord.ButtonStyle.primary,
                    row=0,
                ),
            )
        for subsystem, meta in cross_link:
            self.add_item(
                _CommunityChildButton(
                    subsystem=subsystem,
                    label=_format_child_label(subsystem, meta),
                    style=discord.ButtonStyle.secondary,
                    row=1,
                ),
            )


__all__ = [
    "CommunityHubView",
    "build_community_hub_embed",
    "discover_community_children",
]
