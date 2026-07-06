"""Subsystem-visibility sub-panel + per-channel toggle grid.

Two-stage flow: ``_VisibilitySubView`` multi-selects one or more channels
via ``views.selectors.attach_multi_select``; pressing "Configure Selected" opens a
shared ``_SubsystemToggleView`` whose tri-state buttons apply to *every*
chosen channel at once (audit P1-10 — the visibility sibling of the
restrict/delete multi-select panels).

Each toggle reflects the **aggregate** state across the selected channels
(green = all on, red = all off, grey = all inherit, blue = mixed).
Clicking force-sets every selected channel to the next state in the cycle
on → off → inherit (a mixed group jumps to on first) so the channels
converge to a consistent value.

The toggle callback writes through ``governance_service.set_subsystem_visibility``,
which routes via ``GovernanceMutationPipeline`` (audit log + cache
invalidation + event emission per INV-E) once per channel.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services import governance_service
from services.governance_service import GovernanceContext
from utils.subsystem_registry import all_subsystems_sorted
from utils.ui_constants import CHANNEL_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.selectors import attach_multi_select

logger = logging.getLogger("bot")


class _VisibilitySubView(BaseView):
    """Channel picker for subsystem visibility — multi-select.

    Pick one or more channels, then "Configure Selected" opens the shared
    subsystem toggle grid that applies to every chosen channel.
    """

    def __init__(
        self,
        ctx: commands.Context,
        *,
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.manager_message = manager_message
        self.selected_channel_ids: list[int] = []
        self._option_names: dict[int, str] = {}

        # Full channel list — the windowed select paginates past 25 (◀/▶ nav)
        # instead of front-truncating (the #1040 silent-drop class).
        options: list[discord.SelectOption] = []
        for ch in ctx.guild.text_channels:
            channel_name = f"#{ch.name}"
            self._option_names[ch.id] = channel_name
            options.append(
                discord.SelectOption(
                    label=channel_name[:100],
                    value=str(ch.id),
                    description=f"ID: {ch.id}",
                ),
            )

        attach_multi_select(
            self,
            options,
            self._on_channels_selected,
            placeholder="Select one or more channels to configure…",
            min_values=1,
            select_row=0,
            nav_row=2,
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
            label="↩ Back",
            custom_id="channels:visibility:back",
            parent_builder=_build_parent,
            row=1,
        )

    async def _on_channels_selected(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        # The windowed multi-select hands back option *value* strings; our options carry
        # int channel ids, so coerce (``_option_names`` is int-keyed).
        ids: list[int] = []
        for v in values:
            try:
                ids.append(int(v))
            except (TypeError, ValueError):
                continue
        self.selected_channel_ids = ids
        try:
            await interaction.response.edit_message(
                embed=self.build_embed(),
                view=self,
            )
        except discord.HTTPException:
            await safe_defer(interaction)

    def _selected_names(self) -> list[str]:
        return [
            self._option_names.get(cid, str(cid)) for cid in self.selected_channel_ids
        ]

    def build_embed(self) -> discord.Embed:
        names = self._selected_names()
        embed = discord.Embed(
            title="🔍 Subsystem Visibility",
            description=(
                "Select one or more channels, then press **Configure Selected** "
                "to set which subsystems are visible there.\n\n"
                "**Green** = enabled  •  **Red** = disabled  •  **Grey** = inherit  "
                "•  **Blue** = mixed across the selection\n\n"
                "_Use ◀/▶ to page through channels. Category and guild-scope "
                "controls coming soon._"
            ),
            color=CHANNEL_COLOR,
        )
        embed.add_field(
            name=f"Selected channel{'s' if len(names) != 1 else ''}",
            value=(", ".join(f"`{n}`" for n in names) if names else "*(none)*"),
            inline=False,
        )
        return embed

    @discord.ui.button(
        label="Configure Selected",
        style=discord.ButtonStyle.blurple,
        emoji="⚙️",
        row=1,
    )
    async def configure_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not self.selected_channel_ids:
            await interaction.response.send_message(
                "Please select at least one channel first.",
                ephemeral=True,
            )
            return
        # Defer before the DB round-trip in ``load`` — it can exceed the
        # 3 s interaction-token window across several channels.
        if not await safe_defer(interaction):
            return
        channels = [
            (cid, self._option_names.get(cid, str(cid)))
            for cid in self.selected_channel_ids
        ]
        sub = _SubsystemToggleView(
            self.ctx,
            channels=channels,
            manager_message=self.manager_message,
        )
        await sub.load(interaction.guild_id)
        await safe_edit(interaction, embed=sub.build_embed(), view=sub)


class _SubsystemToggleView(BaseView):
    """Subsystem toggle grid applied to one or more channels at once."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        channels: list[tuple[int, str]],
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.channels = channels  # list of (channel_id, display_name)
        self.manager_message = manager_message
        # per-channel explicit-visibility rows, aligned with ``self.channels``
        self._channel_rows: list[dict[str, bool | None]] = []

    async def load(self, guild_id: int) -> None:
        from utils import db

        self._channel_rows = [
            await db.get_subsystem_visibility(guild_id, "channel", cid)
            for cid, _name in self.channels
        ]
        self._rebuild_buttons()

    def _aggregate(self, subsystem_name: str) -> bool | None | str:
        """Combined state across all channels; ``"mixed"`` when they differ."""
        states = {rows.get(subsystem_name) for rows in self._channel_rows}
        if len(states) == 1:
            return next(iter(states))
        return "mixed"

    def _rebuild_buttons(self) -> None:
        # Rebuild from scratch each refresh: clear all items, re-add the
        # toggle grid (rows 1-4), then re-attach the Back button (row 0).
        for item in list(self.children):
            self.remove_item(item)

        visible_subsystems = [
            (name, meta)
            for name, meta in all_subsystems_sorted()
            if meta.get("visibility_mode", "normal") not in ("internal",)
        ][:20]  # max 20 toggles to stay within Discord's 25-item limit

        for i, (name, meta) in enumerate(visible_subsystems):
            agg = self._aggregate(name)
            display = meta.get("display_name", name)
            if agg is True:
                style = discord.ButtonStyle.green
                label = f"✓ {display}"
            elif agg is False:
                style = discord.ButtonStyle.red
                label = f"✗ {display}"
            elif agg == "mixed":
                style = discord.ButtonStyle.blurple
                label = f"± {display}"
            else:  # None — inherit from parent scope
                style = discord.ButtonStyle.grey
                label = f"~ {display}"

            btn = discord.ui.Button(  # type: ignore[var-annotated]
                label=label[:80],
                style=style,
                row=min(1 + i // 5, 4),
                custom_id=f"toggle_{name}",
            )
            btn.callback = self._make_toggle_callback(name)  # type: ignore[method-assign]
            self.add_item(btn)

        self._attach_back_button()

    def _attach_back_button(self) -> None:
        """Re-add Back nav to the channel picker (audit §9.3 dead-end fix)."""

        async def _build_parent(
            _interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            parent = _VisibilitySubView(
                self.ctx,
                manager_message=self.manager_message,
            )
            return parent.build_embed(), parent

        attach_back_button(
            self,
            label="↩ Back",
            custom_id="channels:visibility:toggle:back",
            parent_builder=_build_parent,
            row=0,
        )

    def _make_toggle_callback(self, subsystem_name: str):
        async def callback(interaction: discord.Interaction):
            agg = self._aggregate(subsystem_name)
            # Force-uniform cycle: on → off → inherit → on.  A mixed group
            # jumps straight to on so the channels converge.
            if agg is True:
                new_val: bool | None = False
            elif agg is False:
                new_val = None
            else:  # None (inherit) or "mixed"
                new_val = True

            if not await safe_defer(interaction):
                return

            gctx = GovernanceContext.from_interaction(interaction)
            failed: list[str] = []
            for i, (ch_id, ch_name) in enumerate(self.channels):
                try:
                    await governance_service.set_subsystem_visibility(
                        gctx,
                        "channel",
                        ch_id,
                        subsystem_name,
                        new_val,
                    )
                except Exception as exc:
                    logger.warning(
                        "Subsystem visibility toggle failed | channel=%r "
                        "subsystem=%r exc=%s",
                        ch_name,
                        subsystem_name,
                        exc,
                        exc_info=True,
                    )
                    failed.append(ch_name)
                    continue
                # Reflect the write locally so the aggregate recomputes
                # correctly (a partial failure naturally shows as mixed).
                self._channel_rows[i][subsystem_name] = new_val

            if failed:
                await safe_followup(
                    interaction,
                    f"⚠️ Couldn't update **{subsystem_name}** for: "
                    + ", ".join(f"`{n}`" for n in failed),
                    ephemeral=True,
                )

            self._rebuild_buttons()
            await safe_edit(interaction, embed=self.build_embed(), view=self)

        return callback

    def build_embed(self) -> discord.Embed:
        names = ", ".join(f"`{n}`" for _, n in self.channels)
        count = len(self.channels)
        return discord.Embed(
            title=f"🔍 Subsystem Visibility — {count} channel{'s' if count != 1 else ''}",
            description=(
                f"Toggling applies to: {names}\n\n"
                "**✓ Green** = force enabled  •  **✗ Red** = force disabled  •  "
                "**~ Grey** = inherit  •  **± Blue** = mixed across channels\n"
                "_Clicking forces every selected channel to the next state._"
            ),
            color=CHANNEL_COLOR,
        )
