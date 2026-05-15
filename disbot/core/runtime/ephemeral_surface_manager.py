"""Ephemeral overlay surfaces — confirmations and alerts.

These send ephemeral Discord messages that layer over persistent panels
without replacing them.  The underlying panel message is unaffected;
only the invoking user sees the overlay.

Public surface:
    send_confirmation(interaction, message, ...) → None
    send_alert(interaction, message, ...)        → None
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import discord


class _ConfirmView(discord.ui.View):
    """Ephemeral yes/no confirmation widget."""

    def __init__(
        self,
        on_confirm: Callable[..., Coroutine[Any, Any, None]] | None,
        on_cancel: Callable[..., Coroutine[Any, Any, None]] | None,
        confirm_label: str,
        cancel_label: str,
    ) -> None:
        super().__init__(timeout=60)
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        yes = discord.ui.Button(
            label=confirm_label,
            style=discord.ButtonStyle.danger,
            custom_id="surface:confirm",
        )
        yes.callback = self._confirm
        self.add_item(yes)

        no = discord.ui.Button(
            label=cancel_label,
            style=discord.ButtonStyle.secondary,
            custom_id="surface:cancel",
        )
        no.callback = self._cancel
        self.add_item(no)

    def _disable_all(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[union-attr]

    async def _confirm(self, interaction: discord.Interaction) -> None:
        self._disable_all()
        await interaction.response.edit_message(view=self)
        if self._on_confirm:
            await self._on_confirm(interaction)

    async def _cancel(self, interaction: discord.Interaction) -> None:
        self._disable_all()
        await interaction.response.edit_message(view=self)
        if self._on_cancel:
            await self._on_cancel(interaction)

    async def on_timeout(self) -> None:
        self._disable_all()


async def send_confirmation(
    interaction: discord.Interaction,
    message: str,
    *,
    on_confirm: Callable[..., Coroutine[Any, Any, None]] | None = None,
    on_cancel: Callable[..., Coroutine[Any, Any, None]] | None = None,
    confirm_label: str = "✅ Confirm",
    cancel_label: str = "✖ Cancel",
) -> None:
    """Send an ephemeral yes/no confirmation overlay.

    The panel beneath is unaffected — only the invoking user sees the dialog.
    ``on_confirm`` and ``on_cancel`` receive the follow-up interaction.
    """
    view = _ConfirmView(on_confirm, on_cancel, confirm_label, cancel_label)
    await interaction.response.send_message(message, view=view, ephemeral=True)


async def send_alert(
    interaction: discord.Interaction,
    message: str,
    *,
    ephemeral: bool = True,
) -> None:
    """Send a one-off informational message without disturbing the panel.

    Uses ``followup`` if the interaction has already been responded to.
    """
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(message, ephemeral=ephemeral)
