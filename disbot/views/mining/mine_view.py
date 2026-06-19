"""!mine button view — extracted from ``cogs/mining_cog.py`` (S4.1).

A 30-second ephemeral view with three Mine Left/Right/Down buttons.
On click, rolls loot via ``utils.mining.rewards.roll_mine_loot`` and
updates the user's mining inventory via the shared DB helper.

Decoupled from the cog: the previous nested ``MiningCog.MineView``
called ``self.cog.update_inventory(...)`` which routed to
``db.update_mining_item``.  The extracted view skips the cog round-
trip and calls the DB primitive directly so it has no cog dependency
and can be unit-tested without a Discord mock.

After a direction is picked, the message swaps to a
:class:`_MineResultsView` (Mine Again / Back to Mining Menu / Back
to Help) so the user never lands on a dead-end message — fixes the
pre-PR-4 behavior where the view was set to ``None`` after a single
mine action.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils.mining import world
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import BaseView

logger = logging.getLogger("bot.views.mining.mine_view")


def _build_mine_prompt_embed() -> discord.Embed:
    """The same embed shown when ``MiningHubView``'s Mine button opens."""
    return discord.Embed(
        title="Mining",
        description=(
            "Choose a direction to mine.\n"
            "If you own a pickaxe, you'll get extra loot!\n\n"
            "**⬇️ Descend / ⬆️ Ascend** move between depth bands "
            "(deeper = richer, gated by your light).\n"
            "**🗺️ Explore** triggers a random depth event."
        ),
        color=MINING_COLOR,
    )


class MineView(BaseView):
    """Mine Left/Right/Down + movement (Descend/Ascend) + Explore (30s timeout).

    Option A declutter (owner-directed, 2026-06-15;
    ``docs/planning/mining-hub-redesign-2026-06-15.md``): Descend / Ascend and
    the old depth-tied mining random-event "explore" folded off the main hub
    into the Mine action here, as an interim until PR3's grid Mine. (The main
    hub's new ``🗺️ Explore`` button is the *open-world* explorer — a different
    concept; this Explore is the mining depth-event mechanic.)

    Ownership/timeout/error handling come from BaseView (RS10) — another
    user's click now gets the standard ephemeral denial instead of the
    old silent False.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author, timeout=30)
        self.user_id = author.id
        self.guild_id = guild_id

    @discord.ui.button(label="Mine Left", style=discord.ButtonStyle.primary, row=0)
    async def mine_left(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._handle_mine(interaction, "left")

    @discord.ui.button(label="Mine Right", style=discord.ButtonStyle.primary, row=0)
    async def mine_right(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._handle_mine(interaction, "right")

    @discord.ui.button(label="Mine Down", style=discord.ButtonStyle.primary, row=0)
    async def mine_down(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._handle_mine(interaction, "down")

    @discord.ui.button(label="⬇️ Descend", style=discord.ButtonStyle.success, row=1)
    async def descend_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.descend(self.user_id, self.guild_id)
        if not result.moved:
            description = (
                f"{interaction.user.mention} can't descend any deeper.\n"
                f"_{result.hint}_"
            )
            color = ERROR_COLOR
        else:
            description = (
                f"{interaction.user.mention} descended to "
                f"**{world.describe_position(result.depth)}**."
            )
            if result.xp_note:
                description += "\n" + result.xp_note
            color = SUCCESS_COLOR
        await self._swap_to_results(interaction, "⛏️ Descend", description, color)

    @discord.ui.button(label="⬆️ Ascend", style=discord.ButtonStyle.secondary, row=1)
    async def ascend_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.ascend(self.user_id, self.guild_id)
        if not result.moved:
            description = f"{interaction.user.mention} is already at the **Surface**."
            color = MINING_COLOR
        else:
            description = (
                f"{interaction.user.mention} climbed up to "
                f"**{world.describe_position(result.depth)}**."
            )
            color = SUCCESS_COLOR
        await self._swap_to_results(interaction, "⛏️ Ascend", description, color)

    @discord.ui.button(label="🗺️ Explore", style=discord.ButtonStyle.primary, row=1)
    async def explore_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.explore(self.user_id, self.guild_id)
        description = (
            f"{interaction.user.mention} {result.text}\n"
            f"_{world.describe_position(result.depth)}_"
        )
        if result.wear.notes:
            description += "\n" + "\n".join(result.wear.notes)
        if result.xp_note:
            description += "\n" + result.xp_note
        if result.pack_warning:
            description += "\n" + result.pack_warning
        color = SUCCESS_COLOR if result.amount >= 0 else ERROR_COLOR
        await self._swap_to_results(interaction, "🗺️ Explored!", description, color)

    async def _swap_to_results(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: int,
    ) -> None:
        """Shared post-action swap to ``_MineResultsView`` (Mine Again / Menu / Help).

        Used by Descend / Ascend / Explore so a movement action lands the user on
        the same navigable results screen as a mine, never a dead end.
        """
        result_embed = discord.Embed(title=title, description=description, color=color)
        result_embed.set_footer(
            text=(
                "Click ⛏️ Mine Again to keep mining, "
                "or use the buttons below to navigate."
            ),
        )
        results_view = _MineResultsView(interaction.user, self.guild_id)
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=None,
            embed=result_embed,
            view=results_view,
        )
        results_view.message = interaction.message
        self.stop()

    async def _handle_mine(
        self,
        interaction: discord.Interaction,
        direction: str,
    ) -> None:
        if not await safe_defer(interaction):
            return

        result = await mining_workflow.mine(self.user_id, self.guild_id)

        description = (
            f"{interaction.user.mention} mined **{result.amount}x {result.found}** "
            f"by going {direction} in {world.describe_position(result.depth)}!"
        )
        if result.wear.notes:
            description += "\n" + "\n".join(result.wear.notes)
        if result.xp_note:
            description += "\n" + result.xp_note
        if result.pack_warning:
            description += "\n" + result.pack_warning
        result_embed = discord.Embed(
            title="⛏️ Mined!",
            description=description,
            color=MINING_COLOR,
        )
        result_embed.set_footer(
            text=(
                "Click ⛏️ Mine Again to try another direction, "
                "or use the buttons below to navigate."
            ),
        )
        results_view = _MineResultsView(interaction.user, self.guild_id)
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=None,
            embed=result_embed,
            view=results_view,
        )
        results_view.message = interaction.message
        self.stop()


class _MineResultsView(BaseView):
    """Post-mine results view: Mine Again / Back to Mining Menu / Back to Help.

    Fixes the pre-PR-4 dead-end where the MineView was replaced with
    ``view=None`` after a single direction click, leaving the user
    with no on-message way to continue. Ownership/timeout/error handling
    come from BaseView (RS10).
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author, timeout=60)
        self.user_id = author.id
        self.guild_id = guild_id

    @discord.ui.button(
        label="⛏️ Mine Again",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def mine_again_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        view = MineView(interaction.user, self.guild_id)
        await interaction.response.edit_message(
            embed=_build_mine_prompt_embed(),
            view=view,
        )
        view.message = interaction.message
        self.stop()

    @discord.ui.button(
        label="↩ Mining Menu",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def mining_menu_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Late import to keep the module-load graph acyclic
        # (main_panel imports this module).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self.user_id,
            self.guild_id,
            name=interaction.user.display_name,
        )
        view = MiningHubView()
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()

    @discord.ui.button(
        label="📚 Back to Help",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def help_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        try:
            from cogs.help_cog import resolve_help_panel_state

            embed, new_view = await resolve_help_panel_state(interaction)
            await safe_edit(interaction, embed=embed, view=new_view)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash panel
            logger.warning(
                "Mining results → Help navigation failed: %s",
                exc,
                exc_info=True,
            )
            embed = discord.Embed(
                title="Help unavailable",
                description=f"Could not open Help: `{type(exc).__name__}`.",
                color=discord.Color.orange(),
            )
            await safe_edit(interaction, embed=embed, view=self)
        else:
            self.stop()
