"""Channel-restriction sub-panel.

Pick one or more channels, then lock (deny send_messages for @everyone)
or unlock (restore send_messages).  Auto-returns to the manager hub
after the action lands.

The channel picker is the shared ``views.selectors.MultiSelect``
primitive (repo-wide audit P1-10): admins routinely lock/unlock a batch
of channels at once, so forcing one-at-a-time was needless friction.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.panel_recovery import restore_parent_or_send_fresh
from utils.ui_constants import CHANNEL_COLOR, ERROR_COLOR, SUCCESS_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.selectors import MultiSelect

logger = logging.getLogger("bot")


class _RestrictSubView(BaseView):
    """Restriction management: pick channel(s), then choose lock or unlock."""

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
        # id -> display name, sourced from the option labels so the result
        # embed can name channels without re-resolving each one.
        self._option_names: dict[int, str] = {}
        for opt in options:
            try:
                self._option_names[int(opt.value)] = opt.label
            except ValueError:
                continue

        self.channel_select = MultiSelect(
            options,
            self._on_channels_selected,
            placeholder="Select one or more channels to manage…",
            min_values=1,
            row=0,
        )
        self.add_item(self.channel_select)

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
            custom_id="channels:restrict:back",
            parent_builder=_build_parent,
            row=2,
        )

    async def _on_channels_selected(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        # ``MultiSelect`` hands back option *value* strings; our options
        # carry int channel ids, so coerce. ``_option_names`` is int-keyed
        # — without this the "Selected" field and result embeds fall back
        # to raw ids instead of channel names.
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
        logger.error("RestrictSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        await safe_followup(interaction, msg, ephemeral=True)

    def _selected_names(self) -> list[str]:
        return [
            self._option_names.get(cid, str(cid)) for cid in self.selected_channel_ids
        ]

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔒 Manage Restrictions",
            description=(
                "Select one or more channels, then choose a restriction action.\n\n"
                "**🔒 Lock** — disable send messages for @everyone\n"
                "**🔓 Unlock** — restore send messages for @everyone"
            ),
            color=CHANNEL_COLOR,
        )
        names = self._selected_names()
        embed.add_field(
            name=f"Selected channel{'s' if len(names) != 1 else ''}",
            value=(", ".join(f"`{n}`" for n in names) if names else "*(none)*"),
            inline=False,
        )
        return embed

    async def _apply_restriction(
        self,
        interaction: discord.Interaction,
        *,
        send_messages: bool,
        action_label: str,
        past_tense: str,
        embed_color: discord.Color,
    ) -> None:
        if not self.selected_channel_ids:
            await interaction.response.send_message(
                "Please select at least one channel first.",
                ephemeral=True,
            )
            return

        # Defer before the Discord permission writes: set_permissions is
        # not instant under load and across several channels the subsequent
        # edit_message would race the 3 s interaction token.
        if not await safe_defer(interaction):
            return

        succeeded: list[str] = []
        forbidden: list[str] = []
        failed: list[str] = []
        for channel_id in self.selected_channel_ids:
            name = self._option_names.get(channel_id, str(channel_id))
            channel = resources.resolve_channel(
                interaction.guild,
                channel_id=channel_id,
                kind="any",
            )
            if channel is None:
                failed.append(name)
                continue
            try:
                await channel.set_permissions(
                    interaction.guild.default_role,
                    send_messages=send_messages,
                )
            except discord.Forbidden:
                forbidden.append(name)
            except discord.HTTPException as exc:
                logger.warning(
                    "Restrict apply failed | channel=%r exc=%s",
                    name,
                    exc,
                )
                failed.append(name)
            else:
                succeeded.append(name)

        result_embed = self._build_result_embed(
            action_label=action_label,
            past_tense=past_tense,
            embed_color=embed_color,
            succeeded=succeeded,
            forbidden=forbidden,
            failed=failed,
        )

        for item in self.children:
            item.disabled = True

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

    def _build_result_embed(
        self,
        *,
        action_label: str,
        past_tense: str,
        embed_color: discord.Color,
        succeeded: list[str],
        forbidden: list[str],
        failed: list[str],
    ) -> discord.Embed:
        # All failed and nothing succeeded → show an error-coloured embed.
        any_ok = bool(succeeded)
        embed = discord.Embed(
            title=f"{action_label} Applied" if any_ok else f"{action_label} Failed",
            color=embed_color if any_ok else ERROR_COLOR,
        )
        if succeeded:
            embed.add_field(
                name=f"✅ {past_tense.capitalize()}",
                value=", ".join(f"`{n}`" for n in succeeded),
                inline=False,
            )
        if forbidden:
            embed.add_field(
                name="🚫 Missing permission",
                value=", ".join(f"`{n}`" for n in forbidden),
                inline=False,
            )
        if failed:
            embed.add_field(
                name="⚠️ Not found / failed",
                value=", ".join(f"`{n}`" for n in failed),
                inline=False,
            )
        embed.set_footer(text="Returning to the management panel…")
        return embed

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="🔒", row=1)
    async def lock_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=False,
            action_label="🔒 Lock",
            past_tense="locked (send messages disabled for @everyone)",
            embed_color=ERROR_COLOR,
        )

    @discord.ui.button(
        label="Unlock",
        style=discord.ButtonStyle.green,
        emoji="🔓",
        row=1,
    )
    async def unlock_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=True,
            action_label="🔓 Unlock",
            past_tense="unlocked (send messages restored for @everyone)",
            embed_color=SUCCESS_COLOR,
        )
