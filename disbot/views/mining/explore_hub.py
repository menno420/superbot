"""Explore sub-hub — the open-world explorer group of the mining hub (STUB).

Part of the Option A hub declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): the main mining hub shrinks
to 6 buttons, and the new ``🗺️ Explore`` button opens this **open-world** sub-hub.

Name-clash note (deviation flagged for owner review, 2026-06-19): this open-world
Explore is a *different concept* from the existing depth-tied mining random-event
"explore" — the latter is a mining mechanic that folded into the Mine action
(``MineView``) in this same PR. This sub-hub is the open-world explorer the owner
asked for ("a separate open-world explorer, not tied to mine depth"); its exact
commands are undefined, so it ships as a **pure stub / "early" hub**.

The Fishing / Roam / Quests buttons show an in-place "coming soon" message and are
deliberately **not** wired into any fishing module or any file outside this lane —
fishing v1 lives in separate modules a future design pass / other lane owns.

Authority is re-checked at callback time via ``HubView``'s invoker lock + the
per-callback guild guard (mirrors the main hub).
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from utils.ui_constants import MINING_COLOR
from views.base import HubView

_GUIDE = (
    "_Open-world exploration — **early / coming soon**. Unlike the mine (which is "
    "tied to depth), this is a free-roam overworld. The activities below are being "
    "designed; the buttons preview what's planned._\n\n"
    "**🎣 Fishing** — cast a line in lakes and rivers _(coming soon)_\n"
    "**🧭 Roam** — wander the overworld and stumble on places _(coming soon)_\n"
    "**📜 Quests** — pick up and track objectives _(coming soon)_"
)


def build_explore_hub_embed() -> discord.Embed:
    """The Explore sub-hub overview (static stub — no live state yet)."""
    embed = discord.Embed(
        title="🗺️ Explore — open world (early)",
        description=_GUIDE,
        color=MINING_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


def _coming_soon_embed(feature: str, blurb: str) -> discord.Embed:
    """An in-place 'coming soon' card for a stubbed Explore activity."""
    embed = discord.Embed(
        title=f"{feature} — coming soon",
        description=(
            f"{blurb}\n\n"
            "This is part of the open-world Explore hub, which is **early** and still "
            "being designed. It isn't playable yet — pick another option above, or "
            "head back to the mining hub."
        ),
        color=MINING_COLOR,
    )
    embed.set_footer(text="Pick another action above to continue.")
    return embed


class MiningExploreHubView(HubView):
    """Sub-hub for the open-world explorer (Fishing / Roam / Quests).

    A stub child of the mining hub — no game logic, every activity is a
    placeholder.
    """

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="🎣 Fishing", style=discord.ButtonStyle.primary, row=0)
    async def fishing_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = _coming_soon_embed(
            "🎣 Fishing",
            "Cast a line in lakes and rivers for fish, junk, and the occasional "
            "treasure.",
        )
        await safe_edit(interaction, embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🧭 Roam", style=discord.ButtonStyle.primary, row=0)
    async def roam_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = _coming_soon_embed(
            "🧭 Roam",
            "Wander the overworld and stumble on biomes, landmarks, and encounters.",
        )
        await safe_edit(interaction, embed=embed, view=self, attachments=[])

    @discord.ui.button(label="📜 Quests", style=discord.ButtonStyle.primary, row=0)
    async def quests_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        embed = _coming_soon_embed(
            "📜 Quests",
            "Pick up objectives, track progress, and earn rewards for completing them.",
        )
        await safe_edit(interaction, embed=embed, view=self, attachments=[])

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        await interaction.response.edit_message(
            embed=embed,
            view=MiningHubView(),
            attachments=[],
        )
        self.stop()


__all__ = ["MiningExploreHubView", "build_explore_hub_embed"]
