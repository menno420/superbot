"""The farm menu — the interactive idle-farm hub panels.

Two author-restricted :class:`HubView` panels (mirrors the mining hub →
workshop-sub-hub split, ``views/mining/main_panel.py``):

* **FarmMenuView** — the main loop: **🥚 Collect** settled eggs for coins + game
  XP · **🛒 Shop** opens the shop sub-view · **🔄 Refresh** re-settles & redraws.
* **FarmShopView** — the coin sinks: **🐔 Buy hen** (faster lay rate) · **🏠
  Upgrade coop** (bigger egg cap) · **◀ Back** to the main panel.

Reached from ``!farm``, the Help hub (``FarmCog.build_help_menu_view``), and the
Explore world hub. Each action re-reads the live state and redraws in place.
"""

from __future__ import annotations

import time

import discord

from services import farm_workflow
from utils import db, idle_summary
from utils import farm as farm_mod
from utils.ui_constants import GAME_COLOR
from views.base import HubView
from views.navigation import carry_back

#: The capped nudge for the farm's "while you were away" blurb.
_COOP_FULL_NOTE = "The coop is full — collect to keep your hens laying!"


def build_farm_embed(
    state: farm_mod.FarmState,
    balance: int,
    *,
    seconds_to_full: int = 0,
    away_summary: str | None = None,
) -> discord.Embed:
    """The main farm-panel embed — flock, coop fill, lay rate, and balance.

    *away_summary* (the optional "while you were away" blurb) renders as the first
    field when something accrued since the player's last action.
    """
    capacity = farm_mod.coop_capacity(state.coop_level)
    rate = farm_mod.lay_rate_per_hour(state.chickens)
    pending_value = farm_mod.collect_value(state.eggs)
    embed = discord.Embed(
        title="🐔 Chicken Farm",
        description=(
            "Your hens lay eggs around the clock — even while you're away. "
            "Press **Collect** to cash them in, then visit the **Shop** to grow."
        ),
        color=GAME_COLOR,
    )
    if away_summary:
        embed.add_field(name="🌙 Welcome back", value=away_summary, inline=False)
    fill = (
        "**full!**"
        if state.eggs >= capacity
        else f"fills in {idle_summary.format_duration(seconds_to_full)}"
    )
    embed.add_field(
        name="Coop",
        value=(
            f"{farm_mod.egg_bar(state.eggs, capacity)}\n"
            f"Worth **{pending_value}** 🪙 · {fill}"
        ),
        inline=False,
    )
    embed.add_field(
        name="Flock",
        value=f"🐔 **{state.chickens}** hen(s) · **{rate}** eggs/hr",
        inline=True,
    )
    embed.add_field(
        name="Coop level",
        value=f"🏠 **{state.coop_level}** · holds **{capacity}** eggs",
        inline=True,
    )
    embed.set_footer(text=f"Balance: {balance} 🪙  ·  🥚 Collect · 🛒 Shop")
    return embed


def build_shop_embed(
    state: farm_mod.FarmState | None = None,
    balance: int | None = None,
) -> discord.Embed:
    """The shop sub-panel embed.

    Called with no *state* by the Shop button (so opening the shop never needs a
    DB read — it stays an instant, always-available navigation), and with the
    live *state* after a purchase so the concrete next prices show.
    """
    embed = discord.Embed(
        title="🛒 Farm Shop",
        description=(
            "Spend your egg coins to grow the farm:\n\n"
            "**🐔 Buy hen** — one more hen lays eggs faster.\n"
            "**🏠 Upgrade coop** — hold more eggs so idle progress banks longer.\n\n"
            "Prices rise as your farm grows."
        ),
        color=GAME_COLOR,
    )
    if state is not None:
        if farm_mod.can_buy_chicken(state.chickens):
            hen = f"**{farm_mod.chicken_price(state.chickens)}** 🪙 (own {state.chickens})"
        else:
            hen = "maxed"
        if farm_mod.can_upgrade_coop(state.coop_level):
            coop = (
                f"**{farm_mod.coop_upgrade_price(state.coop_level)}** 🪙 "
                f"→ holds {farm_mod.coop_capacity(state.coop_level + 1)}"
            )
        else:
            coop = "maxed"
        embed.add_field(name="🐔 Next hen", value=hen, inline=True)
        embed.add_field(name="🏠 Coop upgrade", value=coop, inline=True)
    if balance is not None:
        embed.set_footer(text=f"Balance: {balance} 🪙")
    return embed


async def _panel_data(
    user_id: int,
    guild_id: int,
) -> tuple[farm_mod.FarmState, int, int, str | None]:
    """Read the settled state, balance, seconds-to-full, and the away blurb."""
    status = await farm_workflow.get_status(user_id, guild_id)
    balance = await db.get_coins(user_id, guild_id)
    to_full = farm_mod.seconds_until_full(status.state, int(time.time()))
    away = idle_summary.summarize_idle_gain(
        status.eggs_gained,
        status.elapsed_seconds,
        noun_singular="egg",
        noun_plural="eggs",
        capped=status.at_capacity,
        capped_note=_COOP_FULL_NOTE,
    )
    return status.state, balance, to_full, away


async def open_farm_panel(
    user: discord.Member | discord.User,
    guild_id: int,
) -> tuple[discord.Embed, FarmMenuView]:
    """Build the main farm panel ``(embed, view)`` for *user* in *guild_id*.

    The one entry point shared by ``!farm``, the Help hook, and the Explore-world
    opener, so none of them duplicate the read-then-build sequence.
    """
    state, balance, to_full, away = await _panel_data(user.id, guild_id)
    return (
        build_farm_embed(
            state,
            balance,
            seconds_to_full=to_full,
            away_summary=away,
        ),
        FarmMenuView(user, guild_id),
    )


class FarmMenuView(HubView):
    """The main idle-farm panel (Collect · Shop · Refresh)."""

    SUBSYSTEM = "farm"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    async def _redraw(
        self,
        interaction: discord.Interaction,
        flash: str | None,
    ) -> None:
        state, balance, to_full, away = await _panel_data(
            self._author.id,
            self.guild_id,
        )
        # Redraw onto a fresh view instance so the panel's timeout clock resets
        # on every interaction (and the classifier sees a real in-place update).
        view = FarmMenuView(self._author, self.guild_id)
        carry_back(self, view)
        embed = build_farm_embed(
            state,
            balance,
            seconds_to_full=to_full,
            away_summary=away,
        )
        if flash:
            embed.description = f"{flash}\n\n{embed.description}"
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(label="Collect", emoji="🥚", style=discord.ButtonStyle.success)
    async def collect_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        result = await farm_workflow.collect(self._author.id, self.guild_id)
        flash = result.message
        if result.success and result.xp_note:
            flash = f"{flash}\n{result.xp_note}"
        await self._redraw(interaction, flash)

    @discord.ui.button(label="Shop", emoji="🛒", style=discord.ButtonStyle.primary)
    async def shop_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Static shop landing — no DB read, so the shop always opens instantly.
        view = FarmShopView(self._author, self.guild_id)
        carry_back(self, view)
        await interaction.response.edit_message(embed=build_shop_embed(), view=view)
        view.message = interaction.message

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._redraw(interaction, None)


class FarmShopView(HubView):
    """The farm shop sub-panel (Buy hen · Upgrade coop · Back)."""

    SUBSYSTEM = "farm"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    async def _redraw_shop(
        self,
        interaction: discord.Interaction,
        flash: str | None,
    ) -> None:
        state, balance, _, _ = await _panel_data(self._author.id, self.guild_id)
        view = FarmShopView(self._author, self.guild_id)
        carry_back(self, view)
        embed = build_shop_embed(state, balance)
        if flash:
            embed.description = f"{flash}\n\n{embed.description}"
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(label="Buy hen", emoji="🐔", style=discord.ButtonStyle.primary)
    async def buy_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        result = await farm_workflow.buy_chicken(self._author.id, self.guild_id)
        await self._redraw_shop(interaction, result.message)

    @discord.ui.button(
        label="Upgrade coop",
        emoji="🏠",
        style=discord.ButtonStyle.secondary,
    )
    async def upgrade_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        result = await farm_workflow.upgrade_coop(self._author.id, self.guild_id)
        await self._redraw_shop(interaction, result.message)

    @discord.ui.button(label="Back", emoji="◀", style=discord.ButtonStyle.secondary)
    async def back_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        state, balance, to_full, away = await _panel_data(
            self._author.id,
            self.guild_id,
        )
        view = FarmMenuView(self._author, self.guild_id)
        carry_back(self, view)
        await interaction.response.edit_message(
            embed=build_farm_embed(
                state,
                balance,
                seconds_to_full=to_full,
                away_summary=away,
            ),
            view=view,
        )
        view.message = interaction.message
