"""Cleanup hub panel — Phase 5 of the interface-completion roadmap.

A read-mostly router that surfaces existing cleanup functionality
through a single ``!cleanup`` entry. The panel itself owns no
mutation paths; every button hands off to a subsystem that already
exists:

* **Prohibited Words** → reuses ``_WordMenuView`` from ``cleanup_cog``
  (the current ``!wordmenu`` UX). The view is rendered in place via
  ``interaction.response.edit_message``.
* **Logging Status** → routes to :class:`cogs.logging.panel.LoggingPanelView`.
  Cleanup events flow through the logging subsystem, so this is the
  natural diagnostic next step from a cleanup operator's perspective.
* **Settings** → opens :class:`views.settings.subsystem_view.SubsystemSettingsView`
  for the ``cleanup`` subsystem. There are no scalar settings registered
  for cleanup today, so the page currently has no edit/reset selects;
  this hook gives the wiring a stable place to live once the
  channel-policy storage in the open question for Phase 5 lands.
* **Refresh** rebuilds the read-only overview.

The view contains no mutation, no auto-create, and no new settings —
mirroring the roadmap's "first iteration mostly read-only" constraint.
All cog imports are function-local to keep this module import-safe
(it can be loaded before ``cogs.cleanup_cog`` finishes initialising
without triggering a circular import).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import help_ctx_shim
from utils.ui_constants import ADMIN_COLOR
from views.base import HubView

if TYPE_CHECKING:
    from cogs.cleanup_cog import Cleanup


logger = logging.getLogger("bot.cogs.cleanup.panel")


def build_cleanup_overview_embed(
    cog: Cleanup,
    guild_id: int | None,
) -> discord.Embed:
    """Read-only summary of cleanup state for the current guild.

    Cleanup currently has no DB-persisted scalar knobs — its
    user-visible state is the prohibited-words list (per-guild) and a
    static whitelist of channels read from configuration at startup
    (``config.CLEANUP_WHITELIST_CHANNELS``). The overview surfaces
    both without touching any state.
    """
    word_count = len(cog._word_cache.get(guild_id, [])) if guild_id is not None else 0
    whitelist_channels = list(cog.whitelisted_channels or ())

    embed = discord.Embed(
        title="🧹 Cleanup Hub",
        description=(
            "Auto-moderation policies for command-style messages and "
            "prohibited content. Channels you explicitly whitelist below "
            "are exempt from the command-pattern check."
        ),
        color=ADMIN_COLOR,
    )
    embed.add_field(
        name="Prohibited Words",
        value=f"{word_count} configured" if word_count else "_None configured_",
        inline=True,
    )
    embed.add_field(
        name="Whitelisted Channels",
        value=(
            "\n".join(f"<#{cid}>" for cid in whitelist_channels)
            if whitelist_channels
            else "_None_"
        ),
        inline=True,
    )
    embed.add_field(
        name="Auto-Delete",
        value=(
            "Command-style messages outside whitelisted channels are "
            "removed. Prohibited-word matches are removed with a brief "
            "warning."
        ),
        inline=False,
    )
    embed.set_footer(
        text="Read-only summary. Use the buttons below to manage policies.",
    )
    return embed


class CleanupPanelView(HubView):
    """Top-level Cleanup hub view — routes to existing subsystem panels."""

    SUBSYSTEM = "cleanup"

    def __init__(
        self,
        author: discord.Member | discord.User,
        cog: Cleanup,
        guild_id: int | None,
    ) -> None:
        super().__init__(author)
        self.cog = cog
        self.guild_id = guild_id

    def build_embed(self) -> discord.Embed:
        return build_cleanup_overview_embed(self.cog, self.guild_id)

    @discord.ui.button(
        label="🔤 Prohibited Words",
        style=discord.ButtonStyle.blurple,
        custom_id="cleanup:words",
        row=0,
    )
    async def btn_words(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        from cogs.cleanup_cog import _WordMenuView

        # ``_WordMenuView`` reads the live word cache; ensure the guild
        # has been loaded before rendering. ``_load_guild`` is idempotent.
        if self.guild_id is not None and self.guild_id not in self.cog._word_cache:
            await self.cog._load_guild(self.guild_id)
        view = _WordMenuView(help_ctx_shim(interaction), self.cog)
        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view,
        )

    @discord.ui.button(
        label="📝 Logging Status",
        style=discord.ButtonStyle.secondary,
        custom_id="cleanup:logging",
        row=0,
    )
    async def btn_logging(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        # Local import keeps this module import-safe — the logging panel
        # ultimately pulls in ``core.runtime`` symbols we don't want at
        # cleanup-panel module load time.
        from cogs.logging.panel import LoggingPanelView

        logging_cog = interaction.client.get_cog("LoggingCog")  # type: ignore[attr-defined]
        if logging_cog is None:
            await interaction.response.send_message(
                "The logging cog is not loaded.",
                ephemeral=True,
            )
            return
        build_hook = getattr(logging_cog, "build_help_menu_view", None)
        if callable(build_hook):
            try:
                embed, view = await build_hook(interaction)
            except Exception as exc:  # noqa: BLE001 — navigation must not crash
                logger.warning(
                    "Cleanup panel → logging: build_help_menu_view failed: %s",
                    exc,
                    exc_info=True,
                )
                await interaction.response.send_message(
                    "Couldn't open the logging panel.",
                    ephemeral=True,
                )
                return
            await interaction.response.edit_message(embed=embed, view=view)
            return
        # Fallback — construct the panel directly. Mirrors the contract
        # the cog itself uses, so any future signature changes propagate.
        view = LoggingPanelView(interaction.user)  # type: ignore[arg-type]
        embed = await view.build_embed(interaction)  # type: ignore[attr-defined]
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        label="⚙️ Settings",
        style=discord.ButtonStyle.secondary,
        custom_id="cleanup:settings",
        row=0,
    )
    async def btn_settings(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        from views.settings.subsystem_view import (
            SubsystemSettingsView,
            build_subsystem_embed,
        )

        view = SubsystemSettingsView(interaction.user, "cleanup")
        embed = await build_subsystem_embed(interaction, "cleanup")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        label="🔄 Refresh",
        style=discord.ButtonStyle.secondary,
        custom_id="cleanup:refresh",
        row=1,
    )
    async def btn_refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if self.guild_id is not None:
            await self.cog._load_guild(self.guild_id)
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )
