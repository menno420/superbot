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
from utils.fishing import weather as weather_mod
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
            "**⛵ Set sail** — shore ↔ deepwater\n"
            "**🎒 Rod** — view & upgrade your rod\n"
            "**🪱 Bait** — load a lure for rarer catches\n"
            "**🏗 Structures** — build coral structures\n"
            "**📖 Fishdex** — your collection"
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Fishing from",
        value=f"{profile.emoji} **{profile.name}** — {profile.blurb}",
        inline=False,
    )
    forecast = weather_mod.current_weather()
    embed.add_field(
        name=f"Today's forecast: {forecast.emoji} {forecast.name}",
        value=f"*{forecast.blurb}* ({weather_mod.effect_text(forecast)})",
        inline=False,
    )
    if energy_current is not None:
        embed.add_field(
            name="Energy",
            value=fish_energy.bar(energy_current),
            inline=False,
        )
    return embed


def _venue_log_lines(
    log: dict[str, int],
    venue: str,
    cap: int,
    records: dict[str, float],
) -> list[str]:
    """The per-species log lines for one venue (caught / unlocked / locked).

    A caught species shows its tally and, when a trophy weight has been recorded
    (``records``), the player's heaviest catch — the personal-best long-tail goal.
    """
    lines = []
    for species in species_for_venue(venue):
        count = log.get(species.name, 0)
        unlocked = species.size_rank <= cap
        if count:
            best = records.get(species.name, 0.0)
            trophy = f" · 🏅 {best:g}kg" if best > 0 else ""
            lines.append(
                f"{species.emoji} **{species.name.title()}** "
                f"(#{species.size_rank}) ×{count}{trophy}",
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
    records: dict[str, float] | None = None,
) -> discord.Embed:
    """The collection embed — shared by ``!fishlog`` and the Fishdex button.

    Grouped by venue (Q-0175 §5): a Shore section and a Deepwater (boat-only)
    section, each with its own size cap. Counts only current-catalog species so
    legacy rows from a superseded catalog (Q-0175 reconciliation) never show
    impossible progress.
    """
    records = records or {}
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
        lines = _venue_log_lines(log, venue, cap, records)
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
    records = await db.get_fishing_records(user_id, guild_id)
    xp_map = await db.get_game_xp(user_id, guild_id)
    level = fishing_workflow.fishing_level_from_xp(
        xp_map.get(game_xp_service.GAME_FISHING, 0),
    )
    return build_fishlog_embed(display_name, log, level, records)


def _rules_embed() -> discord.Embed:
    """The "how to fish" quick-reference — the menu's 📖 rules affordance."""
    return discord.Embed(
        title="📖 How to fish",
        description=(
            "**The loop**\n"
            "1. **🎣 Cast** — drop a line, then *wait* for the bite.\n"
            "2. **Bite!** — when the float dips, hit **Reel** before the fish "
            "spits the hook (reel too early and it spooks).\n"
            "3. **Fight** the big ones — keep reeling to land a trophy.\n\n"
            "**Get better catches**\n"
            "• **🎒 Rod** — upgrade your rod for a wider reel window, faster "
            "bites, and less escape.\n"
            "• **🪱 Bait** — load a lure for rarer fish (a consumable knob on "
            "top of your rod).\n"
            "• **⛵ Set sail** — head to deepwater for the rare boat-only fish.\n"
            "• **📖 Fishdex** — track your collection and personal-best weights."
        ),
        color=GAME_COLOR,
    )


class FishingMenuView(HubView):
    """The author-restricted fishing hub panel (Cast · Rod · Fishdex).

    Declares ``SUBSYSTEM = "fishing"`` so
    :func:`views.navigation.attach_standard_nav` auto-attaches **📚 Help** +
    **↩ Games** — a panel reached by ``!fishing`` / the Help hook stays one click
    from Help and its mother hub (the 2026-06-23 never-stranded directive;
    mirrors ``_FishingDoneView``).
    """

    SUBSYSTEM = "fishing"

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

    @discord.ui.button(
        label="Structures",
        emoji="🏗",
        style=discord.ButtonStyle.secondary,
    )
    async def structures_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # One button opens the structures sub-hub (🪸 Tide Pool · ⚓ Dock · …),
        # keeping the menu lean as more coral structures land.
        from views.fishing.structures_hub import (
            StructuresView,
            build_structures_embed,
        )

        embed = await build_structures_embed(self._author.id, self.guild_id)
        view = StructuresView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
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

    @discord.ui.button(
        label="How to fish",
        emoji="📖",
        style=discord.ButtonStyle.secondary,
    )
    async def rules_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # An ephemeral how-to-play card (mirrors the blackjack panel's rules
        # affordance) — the menu embed describes the loop, this spells it out.
        await interaction.response.send_message(embed=_rules_embed(), ephemeral=True)


async def open_fishing_menu(
    interaction: discord.Interaction,
    author: discord.Member | discord.User,
    guild_id: int,
) -> None:
    """Rebuild the fishing menu in place — the Rod/Bait shops' ↩ back target.

    The menu ``self.stop()``s when it opens a shop, so the shops can't simply
    re-show the old menu instance; they call this to mint a fresh, fully-
    navigable :class:`FishingMenuView` (Cast · Sail · Rod · Bait · Fishdex +
    Help/↩ Games) and edit it back onto the panel message. Lazy-imported by the
    shops to respect the menu→shop import direction.
    """
    energy = await fishing_workflow.get_energy(author.id, guild_id)
    profile = await fishing_workflow.get_venue(author.id, guild_id)
    view = FishingMenuView(author, guild_id)
    await interaction.response.edit_message(
        embed=build_menu_embed(energy, profile),
        view=view,
    )
    view.message = interaction.message
