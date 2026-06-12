"""UX Lab home — the gallery's front door.

Four wing buttons + the probe bench, a coverage line driven by the pattern
registry, and in-place transitions throughout (the lab demonstrates the
V-02 navigation doctrine it exhibits).
"""

from __future__ import annotations

import discord

from utils.ux_patterns import PatternCategory, category_counts
from views.base import HubView
from views.ux_lab.buttons import ButtonsWingView
from views.ux_lab.compare import CompareView
from views.ux_lab.embeds import EmbedsWingView
from views.ux_lab.image_cards import ImageWingView
from views.ux_lab.layout_v2 import LayoutWingView
from views.ux_lab.mockups import MockupsWingView
from views.ux_lab.modals import ModalsWingView
from views.ux_lab.probes import ProbesBenchView
from views.ux_lab.selects import SelectsWingView
from views.ux_lab.wing import ExhibitWingView

_WING_LABELS: dict[PatternCategory, str] = {
    PatternCategory.BUTTONS: "Buttons",
    PatternCategory.SELECTS: "Selects",
    PatternCategory.MODALS: "Modals",
    PatternCategory.EMBEDS: "Embeds",
    PatternCategory.LAYOUT_V2: "Components V2",
    PatternCategory.IMAGE: "PIL cards",
    PatternCategory.MOCKUP: "Mock studio",
    PatternCategory.PROBE: "Probe bench",
}


def build_home_embed() -> discord.Embed:
    """The Home card: what the lab is + live registry coverage."""
    counts = category_counts()
    coverage = " · ".join(
        f"{label} **{counts[cat]}**"
        for cat, label in _WING_LABELS.items()
        if counts[cat]
    )
    embed = discord.Embed(
        title="🧪 UX Lab — interface gallery",
        description=(
            "Browse every interaction pattern SuperBot could use. Every "
            "exhibit **reacts** when you press it and carries a spec card "
            "(use-for / avoid-for / platform limits).\n\n"
            "**Nothing here is real**: the lab never writes to the database "
            "or changes the server (CI-enforced)."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Exhibits", value=coverage or "—", inline=False)
    embed.add_field(
        name="How to browse",
        value=(
            "Open a wing → flip exhibits with ◀ ▶ → press things. "
            "🏠 always returns here, in place."
        ),
        inline=False,
    )
    embed.set_footer(
        text="Design: docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md",
    )
    return embed


async def home_builder(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, discord.ui.View]:
    """ParentBuilder for every wing's 🏠 button — rebuilds Home in place."""
    return build_home_embed(), UxLabHomeView(interaction.user)


class UxLabHomeView(HubView):
    """The gallery's category hub (admin workbench — author-locked)."""

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        wings: tuple[tuple[str, str, type[ExhibitWingView], int], ...] = (
            ("🔘", "Buttons", ButtonsWingView, 0),
            ("📋", "Selects", SelectsWingView, 0),
            ("⌨️", "Modals", ModalsWingView, 0),
            ("🪧", "Embeds", EmbedsWingView, 0),
            ("🧱", "Components V2", LayoutWingView, 1),
            ("🎨", "PIL cards", ImageWingView, 1),
            ("🎭", "Mock studio", MockupsWingView, 1),
        )
        for emoji, label, wing_cls, row in wings:
            btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=discord.ButtonStyle.primary,
                row=row,
            )

            async def _open(
                interaction: discord.Interaction,
                cls: type[ExhibitWingView] = wing_cls,
            ) -> None:
                wing = cls(interaction.user, home_builder=home_builder)
                embeds, view = wing.build()
                await interaction.response.edit_message(embeds=embeds, view=view)

            btn.callback = _open  # type: ignore[method-assign]
            self.add_item(btn)

        bench_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="Probe bench",
            emoji="🔬",
            style=discord.ButtonStyle.secondary,
            row=1,
        )

        async def _open_bench(interaction: discord.Interaction) -> None:
            bench = ProbesBenchView(interaction.user, home_builder=home_builder)
            embeds, view = bench.build()
            await interaction.response.edit_message(embeds=embeds, view=view)

        bench_btn.callback = _open_bench  # type: ignore[method-assign]
        self.add_item(bench_btn)

        compare_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="Compare",
            emoji="⚖️",
            style=discord.ButtonStyle.secondary,
            row=2,
        )

        async def _open_compare(interaction: discord.Interaction) -> None:
            panel = CompareView(interaction.user, home_builder=home_builder)
            embeds, view = panel.build()
            await interaction.response.edit_message(embeds=embeds, view=view)

        compare_btn.callback = _open_compare  # type: ignore[method-assign]
        self.add_item(compare_btn)
