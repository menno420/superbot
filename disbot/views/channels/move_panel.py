"""Channel move / reorder sub-panel (server-management PR7).

Bulk-move the selected channels into a category, or send them to the top /
bottom of their category — all routed through the audited
:class:`services.channel_lifecycle_service.ChannelLifecycleService` (the ``move``
and ``reorder`` operations), with per-channel partial-failure reporting.  This is
the panel sibling of the prefix ``!move`` command; both share the one service.

Discord reorder is not atomic; a partial batch records its actual final state via
the service's per-channel steps, surfaced here as an Applied / Failed result.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services.channel_lifecycle_service import (
    ChannelLifecycleRequest,
    ChannelLifecycleService,
)
from services.lifecycle import SUCCESS
from utils.ui_constants import CHANNEL_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.selectors import MultiSelect

logger = logging.getLogger("bot")


def _category_options(guild: discord.Guild) -> list[discord.SelectOption]:
    """A single-select destination list: top level + each category (25-cap)."""
    opts = [discord.SelectOption(label="— Top level (no category) —", value="0")]
    for cat in sorted(getattr(guild, "categories", []), key=lambda c: c.position):
        opts.append(discord.SelectOption(label=cat.name[:100], value=str(cat.id)))
    return opts[:25]


_OnCategoryPick = Callable[[discord.Interaction, int | None, str], Awaitable[None]]


class _CategorySelect(discord.ui.Select):
    """Destination-category picker for the Move operation."""

    def __init__(self, on_pick: _OnCategoryPick, options, *, row: int) -> None:
        super().__init__(
            placeholder="Destination category (for Move)…",
            options=options,
            row=row,
        )
        self._on_pick = on_pick

    async def callback(self, interaction: discord.Interaction) -> None:
        cid = int(self.values[0])
        name = next(
            (o.label for o in self.options if o.value == self.values[0]),
            "?",
        )
        await self._on_pick(interaction, None if cid == 0 else cid, name)


class _MoveSubView(BaseView):
    """Multi-select channels, then move to a category or send to top/bottom."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        options: list[discord.SelectOption],
        manager_message: discord.Message | None,
    ) -> None:
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.selected_channel_ids: list[int] = []
        self.selected_category_id: int | None = None
        self.selected_category_name: str | None = None
        self.category_chosen = False
        self._option_names: dict[int, str] = {}
        for opt in options:
            try:
                self._option_names[int(opt.value)] = opt.label
            except ValueError:
                continue

        self.channel_select = MultiSelect(
            options,
            self._on_channels_selected,
            placeholder="Select channels to move / reorder…",
            min_values=1,
            row=0,
        )
        self.add_item(self.channel_select)
        self.add_item(
            _CategorySelect(
                self._on_category_picked,
                _category_options(ctx.guild),
                row=1,
            ),
        )

        async def _build_parent(
            _interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            from views.channels.main_panel import _ChannelManagerView

            manager = _ChannelManagerView(self.ctx)
            manager.message = self.manager_message
            return manager.build_embed(), manager

        attach_back_button(
            self,
            label="↩️ Back",
            custom_id="channels:move:back",
            parent_builder=_build_parent,
            row=3,
        )

    async def _on_channels_selected(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        ids: list[int] = []
        for v in values:
            try:
                ids.append(int(v))
            except (TypeError, ValueError):
                continue
        self.selected_channel_ids = ids
        try:
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except discord.HTTPException:
            await safe_defer(interaction)

    async def _on_category_picked(
        self,
        interaction: discord.Interaction,
        category_id: int | None,
        category_name: str,
    ) -> None:
        self.selected_category_id = category_id
        self.selected_category_name = category_name
        self.category_chosen = True
        try:
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except discord.HTTPException:
            await safe_defer(interaction)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("MoveSubView error on %s: %s", item, error, exc_info=True)
        await safe_followup(
            interaction,
            f"❌ {type(error).__name__}: {error}",
            ephemeral=True,
        )

    def _selected_names(self) -> list[str]:
        return [
            self._option_names.get(cid, str(cid)) for cid in self.selected_channel_ids
        ]

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="↔️ Move / Reorder Channels",
            description=(
                "Select channels, then **Move to Category** (pick a destination "
                "above) or **Send to Top / Bottom**."
            ),
            color=CHANNEL_COLOR,
        )
        names = self._selected_names()
        embed.add_field(
            name=f"Selected channel{'s' if len(names) != 1 else ''}",
            value=(", ".join(f"`{n}`" for n in names) if names else "*(none)*"),
            inline=False,
        )
        if self.category_chosen:
            embed.add_field(
                name="Move destination",
                value=f"`{self.selected_category_name}`",
                inline=False,
            )
        return embed

    async def _apply(
        self,
        interaction: discord.Interaction,
        request: ChannelLifecycleRequest,
        verb: str,
    ) -> None:
        if not self.selected_channel_ids:
            await interaction.response.send_message(
                "Please select at least one channel first.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction):
            return
        result = await ChannelLifecycleService().apply(
            interaction.guild,
            request,
            interaction.user,
            actor_type="admin",
        )
        await safe_edit(interaction, embed=self._result_embed(result, verb), view=self)

    @discord.ui.button(
        label="Move to Category",
        style=discord.ButtonStyle.blurple,
        emoji="📁",
        row=2,
    )
    async def move_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.category_chosen:
            await interaction.response.send_message(
                "Pick a destination category above first.",
                ephemeral=True,
            )
            return
        await self._apply(
            interaction,
            ChannelLifecycleRequest(
                operation="move",
                channel_ids=tuple(self.selected_channel_ids),
                category_id=self.selected_category_id,
            ),
            "Moved",
        )

    @discord.ui.button(
        label="Send to Top",
        style=discord.ButtonStyle.grey,
        emoji="⬆️",
        row=2,
    )
    async def top_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply(
            interaction,
            ChannelLifecycleRequest(
                operation="reorder",
                channel_ids=tuple(self.selected_channel_ids),
                position="top",
            ),
            "Sent to top",
        )

    @discord.ui.button(
        label="Send to Bottom",
        style=discord.ButtonStyle.grey,
        emoji="⬇️",
        row=2,
    )
    async def bottom_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply(
            interaction,
            ChannelLifecycleRequest(
                operation="reorder",
                channel_ids=tuple(self.selected_channel_ids),
                position="bottom",
            ),
            "Sent to bottom",
        )

    def _result_embed(self, result, verb: str) -> discord.Embed:
        applied = [s.target_name or str(s.target_id) for s in result.applied]
        failed = [
            (s.target_name or str(s.target_id), s.error or "?") for s in result.failed
        ]
        if result.outcome == SUCCESS:
            title, color = f"✅ {verb}", SUCCESS_COLOR
        elif applied:
            title, color = f"{verb} — partial", WARNING_COLOR
        else:
            title, color = f"❌ {verb} failed", ERROR_COLOR
        embed = discord.Embed(title=title, color=color)
        if applied:
            embed.add_field(
                name="✅ Applied",
                value=", ".join(f"`{n}`" for n in applied),
                inline=False,
            )
        if failed:
            embed.add_field(
                name="⚠️ Failed",
                value="\n".join(f"`{n}` — {e}" for n, e in failed),
                inline=False,
            )
        embed.set_footer(
            text="Discord reorder is not atomic — see per-channel results.",
        )
        return embed
