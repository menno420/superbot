"""Community hub view (S9).

The Community subsystem is a router-only hub with no business logic
of its own. Per the mother-hub map, it groups progression and
community-activity subsystems whose primary owners are spread across
the codebase:

* **XP** and **Roles** are the primary children (no existing domain
  cog owned them as a group, hence the new ``community_cog``).
* **Counting**, **Chain**, and **Leaderboard** appear as **cross-links**
  — their primary homes stay under Games (counting/chain) and Economy
  (leaderboard) per the cross-link policy. The buttons here route to
  the same ``build_help_menu_view`` hook those cogs already expose;
  no metadata change.

Five children fit comfortably under the hub-ui-standard button
threshold (≤8 buttons preferred over a dropdown). Back-nav is
attached by ``HelpCategoryView`` when the hub is surfaced from
``!help``; the direct ``!community`` entry shows the hub without a
back button, matching the ``!games`` pattern.
"""

from __future__ import annotations

import logging

import discord

from utils.ui_constants import GENERAL_COLOR
from views.base import HubView

logger = logging.getLogger("bot.views.community")


# Each tuple is (subsystem_key, button_label, button_style, row).
# Rows match the layout: progression on row 0, community games on row 1.
_HUB_CHILDREN: tuple[tuple[str, str, discord.ButtonStyle, int], ...] = (
    ("xp", "🏆 XP & Levels", discord.ButtonStyle.primary, 0),
    ("role", "🎭 Roles", discord.ButtonStyle.primary, 0),
    ("counting", "🔢 Counting", discord.ButtonStyle.secondary, 1),
    ("chain", "⛓️ Chain", discord.ButtonStyle.secondary, 1),
    ("leaderboard", "📊 Leaderboard", discord.ButtonStyle.secondary, 1),
)


def build_community_hub_embed() -> discord.Embed:
    """Build the embed shown by :class:`CommunityHubView`."""
    embed = discord.Embed(
        title="🌱 Community Hub",
        description=(
            "Pick a community feature below.\n\n"
            "**Progression**\n"
            "• 🏆 **XP & Levels** — earn XP by chatting; view your rank.\n"
            "• 🎭 **Roles** — manage self-assignable / XP / time-based roles.\n\n"
            "**Community games & standings**\n"
            "• 🔢 **Counting** — collaborative counting channel.\n"
            "• ⛓️ **Chain** — collaborative chain channel.\n"
            "• 📊 **Leaderboard** — cross-feature standings."
        ),
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

    Surfaces XP + Roles (primary children) and cross-links to
    Counting, Chain, and Leaderboard. The hub view itself contains
    zero business logic — every button forwards to the target cog's
    existing ``build_help_menu_view`` hook.
    """

    SUBSYSTEM = "community"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        for subsystem, label, style, row in _HUB_CHILDREN:
            self.add_item(
                _CommunityChildButton(
                    subsystem=subsystem,
                    label=label,
                    style=style,
                    row=row,
                ),
            )
