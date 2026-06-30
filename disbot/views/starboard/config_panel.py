"""Interactive starboard config panel (idea B1; PR 2, plan §6).

A :class:`BaseView` admin panel for the Hall-of-Fame config that PR 1 only
exposed as text commands — set the board channel, threshold, the self-star
policy, and the ignore-channel list without typing commands. Every write routes
through the audited :mod:`services.starboard_service` (no DB writes in views, per
``docs/architecture.md``); ``manage_guild`` authority is re-checked at callback
time (``.claude/rules/discord-views.md``), because opening a panel does not
authorize later callbacks.

Layout (Discord's 5 action rows):
  row 0  set board channel (native ChannelSelect)
  row 1  toggle a channel's ignore state (native ChannelSelect)
  row 2  ✏️ Threshold (modal) · ⭐ Self-star toggle · 🚫 Disable
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from views.base import BaseView

STAR_COLOR = discord.Color.gold()


def _can_manage(interaction: discord.Interaction) -> bool:
    from config import is_platform_owner

    if is_platform_owner(getattr(interaction.user, "id", None)):
        return True
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms is not None and (perms.manage_guild or perms.administrator))


async def _deny(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "You need the **Manage Server** permission to do that.",
        ephemeral=True,
    )


class StarboardConfigPanel(BaseView):
    """Set channel / threshold / self-star / ignore-channels for the starboard."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent
        self.add_item(_BoardChannelSelect(self))
        self.add_item(_IgnoreChannelSelect(self))

    # -- presentation -------------------------------------------------------

    async def build_embed(self) -> discord.Embed:
        from services import starboard_service

        settings = await starboard_service.get_settings(self.ctx.guild.id)
        ignored = await starboard_service.list_ignore_channels(self.ctx.guild.id)

        embed = discord.Embed(title="⭐ Starboard config", color=STAR_COLOR)
        if settings and settings["enabled"]:
            board = resources.resolve_channel(
                self.ctx.guild,
                channel_id=int(settings["channel_id"]),
            )
            where = board.mention if board else f"`{settings['channel_id']}`"
            embed.description = (
                f"**Channel:** {where}\n"
                f"**Threshold:** {settings['emoji']} ≥ **{settings['threshold']}**\n"
                f"**Self-stars:** {'counted' if settings['self_star'] else 'ignored'}"
            )
        else:
            embed.description = (
                "Starboard is **off**. Pick a hall-of-fame channel below to turn "
                "it on (default threshold **3**, then tap **✏️ Threshold** to change)."
            )
        if ignored:
            mentions = []
            for cid in sorted(ignored):
                ch = resources.resolve_channel(self.ctx.guild, channel_id=cid)
                mentions.append(ch.mention if ch else f"`{cid}`")
            embed.add_field(
                name="🚫 Ignored channels",
                value=", ".join(mentions)[:1024],
                inline=False,
            )
        embed.set_footer(text="Pick a channel below to toggle its ignore state.")
        return embed

    async def _rerender(self, interaction: discord.Interaction) -> None:
        """Edit the panel message in place with a fresh embed."""
        try:
            await interaction.response.edit_message(
                embed=await self.build_embed(),
                view=self,
            )
        except discord.InteractionResponded:
            if self.message:
                await self.message.edit(embed=await self.build_embed(), view=self)

    async def _current_settings(self) -> dict | None:
        from services import starboard_service

        return await starboard_service.get_settings(self.ctx.guild.id)

    # -- threshold (modal) --------------------------------------------------

    @discord.ui.button(label="✏️ Threshold", style=discord.ButtonStyle.blurple, row=2)
    async def threshold_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        settings = await self._current_settings()
        if settings is None:
            await interaction.response.send_message(
                "Set a hall-of-fame channel first (pick one below).",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(_ThresholdModal(self, settings))

    # -- self-star toggle ---------------------------------------------------

    @discord.ui.button(label="⭐ Self-star", style=discord.ButtonStyle.grey, row=2)
    async def selfstar_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from services import starboard_service

        settings = await self._current_settings()
        new_value = not (settings and settings["self_star"])
        await starboard_service.set_self_star(
            guild_id=self.ctx.guild.id,
            self_star=new_value,
            actor_id=interaction.user.id,
        )
        await self._rerender(interaction)

    # -- disable ------------------------------------------------------------

    @discord.ui.button(label="🚫 Disable", style=discord.ButtonStyle.red, row=2)
    async def disable_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from services import starboard_service

        await starboard_service.disable(
            guild_id=self.ctx.guild.id,
            actor_id=interaction.user.id,
        )
        await self._rerender(interaction)


class _BoardChannelSelect(discord.ui.ChannelSelect):
    """Pick (or re-point) the hall-of-fame channel; enables the starboard."""

    def __init__(self, panel: StarboardConfigPanel) -> None:
        super().__init__(
            placeholder="Set the hall-of-fame channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        self.panel = panel

    async def callback(self, interaction: discord.Interaction) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from services import starboard_service

        settings = await self.panel._current_settings()
        threshold = int(settings["threshold"]) if settings else 3
        emoji = settings["emoji"] if settings else "⭐"
        await starboard_service.configure(
            guild_id=self.panel.ctx.guild.id,
            channel_id=self.values[0].id,
            threshold=threshold,
            emoji=emoji,
            actor_id=interaction.user.id,
        )
        await self.panel._rerender(interaction)


class _IgnoreChannelSelect(discord.ui.ChannelSelect):
    """Toggle a channel's ignore state — picking adds if absent, removes if set."""

    def __init__(self, panel: StarboardConfigPanel) -> None:
        super().__init__(
            placeholder="Toggle an ignored channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=1,
        )
        self.panel = panel

    async def callback(self, interaction: discord.Interaction) -> None:
        if not _can_manage(interaction):
            await _deny(interaction)
            return
        from services import starboard_service

        guild_id = self.panel.ctx.guild.id
        channel_id = self.values[0].id
        ignored = await starboard_service.list_ignore_channels(guild_id)
        if channel_id in ignored:
            await starboard_service.remove_ignore_channel(
                guild_id=guild_id,
                channel_id=channel_id,
                actor_id=interaction.user.id,
            )
        else:
            await starboard_service.add_ignore_channel(
                guild_id=guild_id,
                channel_id=channel_id,
                actor_id=interaction.user.id,
            )
        await self.panel._rerender(interaction)


class _ThresholdModal(discord.ui.Modal):
    """Edit the star threshold for an already-configured starboard."""

    def __init__(self, panel: StarboardConfigPanel, settings: dict) -> None:
        super().__init__(title="Starboard threshold", timeout=180)
        self.panel = panel
        self.settings = settings
        self.threshold_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Stars needed to enter the board",
            placeholder=str(settings["threshold"]),
            default=str(settings["threshold"]),
            required=True,
            min_length=1,
            max_length=4,
        )
        self.add_item(self.threshold_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from services import starboard_service

        raw = (self.threshold_input.value or "").strip()
        try:
            threshold = int(raw)
        except ValueError:
            await interaction.response.send_message(
                "❌ Threshold must be a whole number.",
                ephemeral=True,
            )
            return
        await starboard_service.configure(
            guild_id=self.panel.ctx.guild.id,
            channel_id=int(self.settings["channel_id"]),
            threshold=threshold,
            emoji=self.settings["emoji"],
            actor_id=interaction.user.id,
        )
        await self.panel._rerender(interaction)
