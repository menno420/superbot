"""Grid Mine navigator view — the (x, y, z) world (hub-redesign PR 3).

Replaces the interim linear Descend/Ascend ``MineView`` (declutter PR 2) with the
owner-designed grid navigator (Q-0173): the player roams a seed-deterministic
procedural world with six movement buttons + Mine here, discovering cells as they
go (light fog-of-war).  Down/Up change the depth band (``z``, light-gated);
N/S/E/W roam laterally within a band.

All writes go through ``services/mining_workflow`` (RS02); this view only reads,
renders, and routes button clicks to the workflow, re-rendering itself in place so
the navigator persists instead of swapping to a results screen.
"""

from __future__ import annotations

import logging
import time

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db
from utils.mining import energy, grid, world
from utils.mining.character import character_stats
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import BaseView

logger = logging.getLogger("bot.views.mining.grid_mine_view")


async def build_grid_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str | None = None,
    color: int = MINING_COLOR,
) -> discord.Embed:
    """Render the navigator embed: position · current cell · fog-of-war map."""
    suid = str(user_id)
    depth = await db.get_depth(suid, guild_id)
    x, y = await db.get_position(suid, guild_id)
    seed = await db.get_world_seed(guild_id)
    # A brighter equipped light widens the fog-of-war window (BUG-0026 wiring):
    # the same radius feeds the discovered-cell query and the render so they
    # stay in lock-step. light_radius 0-1 keeps the prior default of 2.
    equipped = await db.get_equipment(suid, guild_id)
    # get_skills is keyed on a BIGINT user_id (player_skills, shared with game_xp),
    # unlike the TEXT-keyed mining tables above — so it takes the int user_id, not
    # suid. Passing the string raised asyncpg DataError on every !mine (the grid
    # navigator crash the mocked unit tests could not see; pinned below).
    alloc = await db.get_skills(user_id, guild_id)
    radius = grid.reveal_radius(character_stats(equipped, alloc).light_radius)
    discovered = await db.get_discovered_window(
        suid,
        guild_id,
        depth,
        x - radius,
        x + radius,
        y - radius,
        y + radius,
    )
    cell = grid.cell_at(seed, x, y, depth)
    body = grid.render_local_map(seed, x, y, depth, discovered, radius=radius)

    description = grid.describe_cell(cell)
    if note:
        description = f"{note}\n\n{description}"

    embed = discord.Embed(title="⛏️ Mine", description=description, color=color)
    e_cur, e_ts = await db.get_energy(suid, guild_id)
    e_now = energy.settle(energy.EnergyState(e_cur, e_ts), int(time.time())).current
    embed.add_field(name="📍 Depth", value=world.describe_position(depth), inline=True)
    embed.add_field(name="🧭 Position", value=f"({x}, {y})", inline=True)
    embed.add_field(name="⚡ Energy", value=energy.bar(e_now), inline=True)
    embed.add_field(name="🌐 World seed", value=str(seed), inline=True)
    embed.add_field(
        name="🗺️ Map",
        value=f"```\n{body}\n```\n{grid.MAP_LEGEND}",
        inline=False,
    )
    embed.set_footer(
        text="Each ⛏️ dig moves you one cell and mines it · only you can use this.",
    )
    return embed


class MineGridView(BaseView):
    """The grid Mine navigator (PR 3): dig the (x, y, z) world, in place.

    Owner model (post-#1281): every dig is locomotion — a directional dig moves you
    into the adjacent cell and mines it (N/S/E/W tunnel laterally, Deeper descends a
    band, Up ascends).  Ownership / timeout / error handling come from BaseView; each
    button routes to ``mining_workflow.dig`` (the RS02 write seam) and re-renders this
    same view on the anchor message.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author, timeout=120)
        self.user_id = author.id
        self.guild_id = guild_id

    async def _rerender(
        self,
        interaction: discord.Interaction,
        *,
        note: str | None,
        color: int = MINING_COLOR,
    ) -> None:
        embed = await build_grid_embed(
            self.user_id,
            self.guild_id,
            note=note,
            color=color,
        )
        await safe_edit(interaction, embed=embed, view=self)

    async def _dig(
        self,
        interaction: discord.Interaction,
        direction: str,
    ) -> None:
        """Dig in *direction* — move into the adjacent cell and mine it, in place."""
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.dig(self.user_id, self.guild_id, direction)
        if not result.moved:
            note = result.hint or "You can't dig that way."
            color = ERROR_COLOR
        else:
            parts = [
                f"You dig **{grid.move_phrase(direction)}** and mine "
                f"**{result.amount}× {result.found}**!",
            ]
            if result.cell_note:
                parts.append(result.cell_note)
            if result.wear.notes:
                parts.extend(result.wear.notes)
            if result.xp_note:
                parts.append(result.xp_note)
            if result.pack_warning:
                parts.append(result.pack_warning)
            note = "\n".join(parts)
            color = SUCCESS_COLOR
        await self._rerender(interaction, note=note, color=color)

    # --- directional digging (D-pad: N top, W / E middle, S bottom) ---------
    # Every dig moves you one cell in that direction AND mines it (owner model).

    @discord.ui.button(label="⛏️ North", style=discord.ButtonStyle.primary, row=0)
    async def north_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._dig(interaction, grid.NORTH)

    @discord.ui.button(label="⛏️ West", style=discord.ButtonStyle.primary, row=1)
    async def west_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._dig(interaction, grid.WEST)

    @discord.ui.button(label="⛏️ East", style=discord.ButtonStyle.primary, row=1)
    async def east_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._dig(interaction, grid.EAST)

    @discord.ui.button(label="⛏️ South", style=discord.ButtonStyle.primary, row=2)
    async def south_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._dig(interaction, grid.SOUTH)

    # --- vertical digging (depth band = z; Deeper is light-gated) ------------

    @discord.ui.button(label="⛏️ Deeper", style=discord.ButtonStyle.success, row=3)
    async def down_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._dig(interaction, grid.DOWN)

    @discord.ui.button(label="⛏️ Up", style=discord.ButtonStyle.success, row=3)
    async def up_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._dig(interaction, grid.UP)

    # --- navigation ---------------------------------------------------------

    @discord.ui.button(
        label="↩ Mining Menu",
        style=discord.ButtonStyle.secondary,
        row=4,
    )
    async def menu_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        # Late import to keep the module-load graph acyclic (main_panel imports
        # this module to open the navigator).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self.user_id,
            self.guild_id,
            name=interaction.user.display_name,
        )
        await safe_edit(interaction, embed=embed, view=MiningHubView())
        self.stop()

    @discord.ui.button(
        label="📚 Help",
        style=discord.ButtonStyle.secondary,
        row=4,
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
                "Grid Mine → Help navigation failed: %s",
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
