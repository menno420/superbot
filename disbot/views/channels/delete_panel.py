"""Channel-deletion sub-panel + confirmation step.

Two-stage flow: ``_DeleteSubView`` multi-selects one or more channels;
pressing "Delete Selected" transitions to ``_DeleteConfirmView`` which
lists every target by name and performs the deletes after an explicit
confirmation click.

Multi-channel delete (audit P1-10) is the sibling of the restrict
panel's multi-lock — both adopt ``views.selectors.attach_multi_select``.  Because
deletion is destructive and irreversible, the confirm step names every
channel that will be removed before anything happens.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.panel_recovery import restore_parent_or_send_fresh
from services.channel_lifecycle_service import (
    ChannelLifecycleRequest,
    ChannelLifecycleService,
)
from services.lifecycle import LifecycleResult, StepResult
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
from views.base import BaseView
from views.channels._helpers import _build_channel_options
from views.navigation import attach_back_button
from views.selectors import attach_multi_select

logger = logging.getLogger("bot")


class _DeleteSubView(BaseView):
    """Channel-deletion sub-panel: multi-select picker + confirmation flow."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        options: list[discord.SelectOption],
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.selected_channel_ids: list[int] = []
        # id -> display name, sourced from the option labels so the
        # confirm/result embeds can name channels without re-resolving.
        self._option_names: dict[int, str] = {}
        for opt in options:
            try:
                self._option_names[int(opt.value)] = opt.label
            except ValueError:
                continue

        attach_multi_select(
            self,
            options,
            self._on_channels_selected,
            placeholder="Select one or more channels to delete…",
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
            label="↩️ Back",
            custom_id="channels:delete:back",
            parent_builder=_build_parent,
            row=1,
        )

    async def _on_channels_selected(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        # The windowed multi-select hands back option *value* strings; our options
        # carry int channel ids, so coerce. ``_option_names`` is int-keyed
        # — without this the confirm/result embeds fall back to raw ids
        # instead of channel names.
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

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        # Channel-management views intentionally surface
        # ``type(error).__name__`` to admins for diagnosability — see
        # ``views.base.handle_view_error`` docstring. ``safe_followup``
        # collapses the legacy ``is_done()`` ladder to a single call
        # that routes through ``followup.send`` or ``response.send_message``
        # as appropriate, and swallows the recoverable errors itself.
        logger.error("DeleteSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        await safe_followup(interaction, msg, ephemeral=True)

    def _selected_names(self) -> list[str]:
        return [
            self._option_names.get(cid, str(cid)) for cid in self.selected_channel_ids
        ]

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🗑️ Delete Channel",
            description=(
                "Select one or more channels to delete, then press **Delete Selected**."
            ),
            color=ERROR_COLOR,
        )
        names = self._selected_names()
        embed.add_field(
            name=f"Selected channel{'s' if len(names) != 1 else ''}",
            value=(", ".join(f"`{n}`" for n in names) if names else "*(none)*"),
            inline=False,
        )
        return embed

    @discord.ui.button(
        label="Delete Selected",
        style=discord.ButtonStyle.red,
        emoji="🗑️",
        row=1,
    )
    async def delete_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.selected_channel_ids:
            await interaction.response.send_message(
                "Please select at least one channel first.",
                ephemeral=True,
            )
            return
        confirm_view = _DeleteConfirmView(
            self.ctx,
            channels=[
                (cid, self._option_names.get(cid, str(cid)))
                for cid in self.selected_channel_ids
            ],
            manager_message=self.manager_message,
        )
        await interaction.response.edit_message(
            embed=confirm_view.build_confirm_embed(),
            view=confirm_view,
        )
        self.stop()


class _DeleteConfirmView(BaseView):
    """Confirmation step before actually deleting the selected channels."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        channels: list[tuple[int, str]],
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=60)
        self.ctx = ctx
        self.channels = channels  # list of (channel_id, display_name)
        self.manager_message = manager_message

    def build_confirm_embed(self) -> discord.Embed:
        names = ", ".join(f"`{name}`" for _, name in self.channels)
        count = len(self.channels)
        return discord.Embed(
            title="⚠️ Confirm Deletion",
            description=(
                f"Are you sure you want to delete the following "
                f"{count} channel{'s' if count != 1 else ''}?\n\n"
                f"{names}\n\n**This action cannot be undone.**"
            ),
            color=ERROR_COLOR,
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        # See _DeleteSubView.on_error for the channels-view rationale.
        logger.error("DeleteConfirmView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        await safe_followup(interaction, msg, ephemeral=True)

    @discord.ui.button(
        label="Confirm Delete",
        style=discord.ButtonStyle.red,
        emoji="🗑️",
        row=0,
    )
    async def confirm_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Defer before the deletes: ChannelLifecycleService.apply() is not
        # instant and, across several channels, the subsequent edit_message
        # would race the 3 s interaction token.
        if not await safe_defer(interaction):
            return

        # Channel deletion is lifecycle-owned (docs/ownership.md): route through
        # the audited ChannelLifecycleService so the delete emits its audit
        # companion + channel.lifecycle_changed event, instead of calling
        # channel.delete() directly. The two-stage confirm flow is the operator
        # confirmation the service requires (confirmed=True).
        result = await ChannelLifecycleService().apply(
            interaction.guild,
            ChannelLifecycleRequest(
                operation="delete",
                channel_ids=tuple(cid for cid, _name in self.channels),
            ),
            interaction.user,
            confirmed=True,
            actor_type="admin",
        )

        result_embed = self._build_result_embed(result)

        for item in self.children:
            item.disabled = True
        result_embed.set_footer(text="Returning to the management panel…")
        await safe_edit(interaction, embed=result_embed, view=self)
        self.stop()

        await asyncio.sleep(2)
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        restored = await restore_parent_or_send_fresh(
            parent_message=self.manager_message,
            channel=interaction.channel,
            embed=manager.build_embed(),
            view=manager,
        )
        if restored is not None:
            manager.message = restored

    def _build_result_embed(self, result: LifecycleResult) -> discord.Embed:
        # Reconstruct the friendly per-channel buckets from the service's typed
        # steps. ``result.applied`` / ``result.failed`` partition the StepResults;
        # the service reports the channel id (not its name) for a not-found step,
        # so re-map to the display names the panel already captured.
        names = dict(self.channels)

        def _name(step: StepResult) -> str:
            return names.get(step.target_id, step.target_name or str(step.target_id))

        deleted = [_name(s) for s in result.applied]
        not_found: list[str] = []
        forbidden: list[str] = []
        failed: list[str] = []
        for s in result.failed:
            detail = (s.error or "").lower()
            if "not found" in detail:
                not_found.append(_name(s))
            elif "permission" in detail:
                forbidden.append(_name(s))
            else:
                failed.append(_name(s))

        if not deleted:
            title, color = "❌ Deletion Failed", ERROR_COLOR
        elif not_found or forbidden or failed:
            title, color = "🗑️ Deletion Results", WARNING_COLOR
        else:
            title, color = "✅ Channels Deleted", SUCCESS_COLOR
        embed = discord.Embed(title=title, color=color)
        if deleted:
            embed.add_field(
                name="✅ Deleted",
                value=", ".join(f"`{n}`" for n in deleted),
                inline=False,
            )
        if forbidden:
            embed.add_field(
                name="🚫 Permission denied",
                value=", ".join(f"`{n}`" for n in forbidden),
                inline=False,
            )
        if not_found:
            embed.add_field(
                name="❓ Not found (already deleted?)",
                value=", ".join(f"`{n}`" for n in not_found),
                inline=False,
            )
        if failed:
            embed.add_field(
                name="⚠️ Failed",
                value=", ".join(f"`{n}`" for n in failed),
                inline=False,
            )
        return embed

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.grey,
        emoji="❌",
        row=0,
    )
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        options = _build_channel_options(interaction.guild)
        sub = _DeleteSubView(
            self.ctx,
            options=options,
            manager_message=self.manager_message,
        )
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)
        self.stop()
