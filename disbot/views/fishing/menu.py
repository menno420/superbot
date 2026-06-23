"""The fishing menu — the interactive hub panel (owner design Q-0175 §6).

``FishingMenuView`` is the "make the menu a place" panel the design called for:
one author-restricted :class:`HubView` whose buttons each route into the existing
fishing flows —

* **🎣 Cast** — launches the cast minigame *in place* (shares ``prepare_cast``
  with the ``!fish`` command);
* **🎒 Rod** — swaps the panel to the rod shop (``RodShopView``);
* **📖 Fishdex** — shows your collection, keeping the menu so you can keep going.

Reached from the Help hub (``FishingCog.build_help_menu_view``) and the
``!fishing`` command. Mirrors ``views/games/blackjack_panel.py`` — a panel whose
button spawns a real game.
"""

from __future__ import annotations

import discord

from services import fishing_workflow, game_xp_service
from utils import db
from utils.fishing import energy as fish_energy
from utils.fishing import rods as rods_mod
from utils.fishing import venue as venue_mod
from utils.fishing.fish import (
    MAX_LEVEL,
    max_size_rank_for_level,
    species_for_venue,
)
from utils.ui_constants import GAME_COLOR
from views.base import HubView
from views.fishing.bait_shop import BaitShopView, build_bait_embed
from views.fishing.cast_view import prepare_cast
from views.fishing.rod_shop import RodShopView, build_rod_embed

_FISHING_COLOR = discord.Color.blue()


def build_menu_embed(
    energy_current: int | None = None,
    venue_profile: venue_mod.VenueProfile | None = None,
) -> discord.Embed:
    """The fishing-menu landing embed — what the panel shows before you act.

    Pass *energy_current* (settled) to show the ⚡ cast-energy gauge and
    *venue_profile* to show where the player is currently fishing.
    """
    profile = venue_profile or venue_mod.SHORE_PROFILE
    shore_n = len(species_for_venue(venue_mod.SHORE))
    deep_n = len(species_for_venue(venue_mod.DEEPWATER))
    embed = discord.Embed(
        title="🎣 Fishing",
        description=(
            f"Cast a line to catch from **{shore_n}** shoreline fish — or set sail "
            f"for the **{deep_n}** rare boat-only fish of the deep. Wait for the "
            "bite, reel it in, and fight the big ones; then level up and buy "
            "better rods.\n\n"
            "**🎣 Cast** — wait → bite → reel\n"
            "**⛵ Set sail / 🏖️ Dock** — shore ↔ deepwater\n"
            "**🎒 Rod** — view & upgrade your rod\n"
            "**🪱 Bait** — load a lure for rarer catches\n"
            "**📖 Fishdex** — your collection"
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Fishing from",
        value=f"{profile.emoji} **{profile.name}** — {profile.blurb}",
        inline=False,
    )
    if energy_current is not None:
        embed.add_field(
            name="Energy",
            value=fish_energy.bar(energy_current),
            inline=False,
        )
    return embed


def _venue_log_lines(log: dict[str, int], venue: str, cap: int) -> list[str]:
    """The per-species log lines for one venue (caught / unlocked / locked)."""
    lines = []
    for species in species_for_venue(venue):
        count = log.get(species.name, 0)
        unlocked = species.size_rank <= cap
        if count:
            lines.append(
                f"{species.emoji} **{species.name.title()}** "
                f"(#{species.size_rank}) ×{count}",
            )
        elif unlocked:
            lines.append(
                f"{species.emoji} {species.name.title()} (#{species.size_rank}) "
                "— *not yet caught*",
            )
        else:
            lines.append(f"🔒 ??? (#{species.size_rank}) — *locked*")
    return lines


def build_fishlog_embed(
    display_name: str,
    log: dict[str, int],
    level: int,
) -> discord.Embed:
    """The collection embed — shared by ``!fishlog`` and the Fishdex button.

    Grouped by venue (Q-0175 §5): a Shore section and a Deepwater (boat-only)
    section, each with its own size cap. Counts only current-catalog species so
    legacy rows from a superseded catalog (Q-0175 reconciliation) never show
    impossible progress.
    """
    all_species = species_for_venue(venue_mod.SHORE) + species_for_venue(
        venue_mod.DEEPWATER,
    )
    known = {s.name for s in all_species}
    caught = sum(1 for name in log if name in known)
    total = sum(c for name, c in log.items() if name in known)
    embed = discord.Embed(
        title=f"🎣 {display_name}'s Fishing Log",
        color=_FISHING_COLOR,
    )
    embed.description = (
        f"**{caught}/{len(known)}** species discovered · "
        f"**{total}** total catches · Fishing level **{level}/{MAX_LEVEL}**"
    )
    for venue, label in (
        (venue_mod.SHORE, "🏖️ Shore"),
        (venue_mod.DEEPWATER, "⛵ Deepwater (boat-only)"),
    ):
        cap = max_size_rank_for_level(level, venue)
        lines = _venue_log_lines(log, venue, cap)
        if lines:
            embed.add_field(
                name=f"{label} — up to size #{cap}",
                value="\n".join(lines),
                inline=False,
            )
    embed.set_footer(
        text="🎣 Cast to fish · ⛵ Set sail for the deep · 🎒 Rod to upgrade",
    )
    return embed


async def _fishdex_embed(
    user_id: int,
    guild_id: int,
    display_name: str,
) -> discord.Embed:
    log = await db.get_fishing_log(user_id, guild_id)
    xp_map = await db.get_game_xp(user_id, guild_id)
    level = fishing_workflow.fishing_level_from_xp(
        xp_map.get(game_xp_service.GAME_FISHING, 0),
    )
    return build_fishlog_embed(display_name, log, level)


class FishingMenuView(HubView):
    """The author-restricted fishing hub panel (Cast · Rod · Fishdex)."""

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="Cast", emoji="🎣", style=discord.ButtonStyle.success)
    async def cast_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        prepared = await prepare_cast(self._author.id, self.guild_id)
        if isinstance(prepared, str):
            await interaction.response.send_message(prepared, ephemeral=True)
            return
        embed, view = prepared
        # The cast minigame takes over this panel message; hand off and stop the
        # menu so its timeout can't fight the cast view for the same message.
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
        view.start()
        self.stop()

    @discord.ui.button(
        label="Set sail / Dock",
        emoji="⛵",
        style=discord.ButtonStyle.primary,
    )
    async def sail_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        change = await fishing_workflow.toggle_venue(self._author.id, self.guild_id)
        energy = await fishing_workflow.get_energy(self._author.id, self.guild_id)
        embed = build_menu_embed(energy, venue_mod.profile_for(change.venue))
        # Keep the menu so the player can Cast straight away at the new venue.
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(change.message, ephemeral=True)

    @discord.ui.button(label="Rod", emoji="🎒", style=discord.ButtonStyle.secondary)
    async def rod_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        tier = await db.get_rod_tier(self._author.id, self.guild_id)
        current = rods_mod.rod_for_tier(tier)
        nxt = rods_mod.next_rod(tier)
        balance = await db.get_coins(self._author.id, self.guild_id)
        embed = build_rod_embed(current, nxt, balance)
        shop = RodShopView(self._author, self.guild_id, at_max=nxt is None)
        await interaction.response.edit_message(embed=embed, view=shop)
        shop.message = interaction.message
        self.stop()

    @discord.ui.button(label="Bait", emoji="🪱", style=discord.ButtonStyle.secondary)
    async def bait_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        active, charges = await fishing_workflow.get_active_bait(
            self._author.id,
            self.guild_id,
        )
        balance = await db.get_coins(self._author.id, self.guild_id)
        embed = build_bait_embed(active, charges, balance)
        shop = BaitShopView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=shop)
        shop.message = interaction.message
        self.stop()

    @discord.ui.button(label="Fishdex", emoji="📖", style=discord.ButtonStyle.secondary)
    async def fishdex_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = await _fishdex_embed(
            self._author.id,
            self.guild_id,
            self._author.display_name,
        )
        # Keep the menu so the player can Cast / open the Rod shop after browsing.
        await interaction.response.edit_message(embed=embed, view=self)
