"""Settings Manager — Command Access panel (PR-6).

Operator-facing UI for the per-guild command-access policy:

* mode (``all_channels`` / ``selected_channels`` /
  ``disabled_except_bootstrap``) — one button per mode
* allowed channel list — multi-channel ``discord.ui.ChannelSelect``
  that runs the atomic
  :func:`services.command_access_service.replace_allowed_channels`
  composite when changed
* Back-to-Hub navigation matching the rest of the Settings Manager

Every mutation routes through ``services.command_access_service`` so
cache invalidation + audit emission happen in the canonical path.
The panel never touches ``utils.db.command_access`` directly.

The setting is admin-only: ``!settings`` already gates entry to
this view via ``@commands.has_permissions(administrator=True)``,
but the per-callback guard below is the defence-in-depth (the view
anchor message can outlive the original invocation context if the
panel is shared).
"""

from __future__ import annotations

import logging

import discord

from views.base import HubView

logger = logging.getLogger("bot.views.settings.command_access")


_MODE_LABELS: dict[str, str] = {
    "all_channels": "All channels",
    "selected_channels": "Selected channels",
    "disabled_except_bootstrap": "Disabled except bootstrap",
}

_MODE_DESCRIPTIONS: dict[str, str] = {
    "all_channels": (
        "Normal prefix + slash commands work in every guild channel "
        "(subject to per-command permissions and governance)."
    ),
    "selected_channels": (
        "Normal commands only work in the channels you list below. "
        "Bootstrap commands (`/setup`, `/help`, `/settings`, etc.) "
        "still work everywhere for guild operators."
    ),
    "disabled_except_bootstrap": (
        "Normal commands are denied. Only bootstrap commands "
        "remain reachable so an operator can re-enable from "
        "`!setup` or this panel."
    ),
}


def _format_channel_list(channel_ids: frozenset[int]) -> str:
    if not channel_ids:
        return "*(none configured)*"
    rendered = " ".join(f"<#{cid}>" for cid in sorted(channel_ids))
    # Discord embeds cap field values at 1024 chars; truncate with a
    # trailing count rather than letting the embed render fail.
    if len(rendered) > 950:
        head = " ".join(f"<#{cid}>" for cid in sorted(channel_ids)[:30])
        return f"{head} … (+{len(channel_ids) - 30} more)"
    return rendered


async def build_command_access_embed(guild_id: int | None) -> discord.Embed:
    """Render the current policy as an embed.

    ``guild_id=None`` (the panel was opened in a DM somehow) yields a
    placeholder embed — the panel itself shouldn't open in DM but
    the helper stays defensive.
    """
    embed = discord.Embed(
        title="🚪 Command Access",
        description=(
            "Configure where prefix and slash commands are allowed in "
            "this server.  Applies to **both** invocation surfaces — "
            "the same channels permit `!bj` and `/blackjack` alike.\n\n"
            "Bootstrap commands (`/setup`, `/help`, `/settings`, "
            "`/platform`, `/diagnostics`) always remain reachable "
            "for guild operators so you cannot lock yourself out."
        ),
        color=discord.Color.blurple(),
    )

    if guild_id is None:
        embed.add_field(
            name="Current mode",
            value="*Guild context not available.*",
            inline=False,
        )
        return embed

    from services.command_access_service import get_policy_snapshot

    snapshot = await get_policy_snapshot(guild_id)
    mode_label = (
        _MODE_LABELS.get(snapshot.mode, snapshot.mode)
        if snapshot.mode is not None
        else "All channels (default — no policy row)"
    )
    mode_description = (
        _MODE_DESCRIPTIONS.get(snapshot.mode, "—")
        if snapshot.mode is not None
        else _MODE_DESCRIPTIONS["all_channels"]
    )

    embed.add_field(
        name="Current mode",
        value=f"**{mode_label}**\n{mode_description}",
        inline=False,
    )
    embed.add_field(
        name=f"Allowed channels ({len(snapshot.allowed_channels)})",
        value=_format_channel_list(snapshot.allowed_channels),
        inline=False,
    )
    embed.add_field(
        name="Delete blocked commands",
        value=(
            "**On** — a command typed in a not-allowed channel is deleted "
            "on sight, with a brief auto-deleting notice."
            if snapshot.delete_blocked_commands
            else "**Off** — commands in not-allowed channels are ignored "
            "(the command doesn't run, but the message stays)."
        ),
        inline=False,
    )

    if snapshot.mode == "disabled_except_bootstrap":
        embed.add_field(
            name="Recovery",
            value=(
                "Normal commands are currently denied.  Pick **All "
                "channels** or **Selected channels** above to re-enable, "
                "or run `!setup` to revisit onboarding."
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            "Applies to prefix + slash commands.  "
            "Mode buttons + the channel selector are admin-only."
        ),
    )
    return embed


def _is_admin(member: discord.abc.User | discord.Member) -> bool:
    """Return True iff the invoker has Administrator or Manage Guild.

    Defence-in-depth — the ``!settings`` group is already admin-gated.
    The configured platform owner (config.BOT_OWNER_USER_ID) always qualifies
    so the bot owner can configure command channels in any guild.
    """
    from config import is_platform_owner

    if is_platform_owner(getattr(member, "id", None)):
        return True
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return False
    return bool(
        getattr(perms, "administrator", False) or getattr(perms, "manage_guild", False),
    )


async def _refresh_panel(
    interaction: discord.Interaction,
    view: CommandAccessView,
) -> None:
    """Rebuild the embed after a successful mutation."""
    guild_id = interaction.guild_id
    embed = await build_command_access_embed(guild_id)
    try:
        await interaction.edit_original_response(embed=embed, view=view)
    except Exception as exc:  # noqa: BLE001 — soft-fail
        logger.debug(
            "CommandAccessView: panel refresh failed for guild=%s: %s",
            guild_id,
            exc,
        )


async def _apply_mode(
    interaction: discord.Interaction,
    mode: str,
    view: CommandAccessView,
) -> None:
    """Shared mode-button callback path."""
    if not _is_admin(interaction.user):
        await interaction.response.send_message(
            "❌ Administrator or Manage Guild permission required.",
            ephemeral=True,
        )
        return
    if interaction.guild_id is None:
        await interaction.response.send_message(
            "❌ Command access can only be configured inside a server.",
            ephemeral=True,
        )
        return

    from services.command_access_service import (
        CommandAccessMutationError,
        set_mode,
    )

    try:
        await set_mode(
            guild_id=interaction.guild_id,
            mode=mode,
            actor_id=interaction.user.id,
        )
    except CommandAccessMutationError as exc:
        await interaction.response.send_message(
            f"❌ {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.exception(
            "CommandAccessView: set_mode pipeline raised for guild=%s mode=%s",
            interaction.guild_id,
            mode,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    # safe_defer (INV-L): swallows token-expiry / HTTP errors and
    # returns False so the panel doesn't crash on an aged-out token.
    from core.runtime.interaction_helpers import safe_defer

    if not await safe_defer(interaction):
        return
    await _refresh_panel(interaction, view)
    await interaction.followup.send(
        f"✅ Command access mode set to **{_MODE_LABELS[mode]}**.",
        ephemeral=True,
    )


class _AllChannelsButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="All channels",
            style=discord.ButtonStyle.success,
            emoji="🌐",
            custom_id="settings_command_access.mode.all_channels",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _apply_mode(interaction, "all_channels", _view_of(self))


class _SelectedChannelsButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Selected channels",
            style=discord.ButtonStyle.primary,
            emoji="📋",
            custom_id="settings_command_access.mode.selected_channels",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _apply_mode(interaction, "selected_channels", _view_of(self))


class _DisabledButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Disabled except bootstrap",
            style=discord.ButtonStyle.danger,
            emoji="🚫",
            custom_id="settings_command_access.mode.disabled_except_bootstrap",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _apply_mode(
            interaction,
            "disabled_except_bootstrap",
            _view_of(self),
        )


class _ChannelAllowlistSelect(discord.ui.ChannelSelect):
    """Multi-channel select that drives ``replace_allowed_channels``.

    A blank selection clears the list (atomic delete in the service
    layer).  This is the same shape the future setup-wizard section
    would have used, so we get the UX in this PR without splitting
    the integration across two surfaces.
    """

    def __init__(self) -> None:
        super().__init__(
            placeholder="Set allowed channels (selected_channels mode)…",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=25,
            row=1,
            custom_id="settings_command_access.channels",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not _is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Administrator or Manage Guild permission required.",
                ephemeral=True,
            )
            return
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ Command access can only be configured inside a server.",
                ephemeral=True,
            )
            return

        from services.command_access_service import (
            CommandAccessMutationError,
            replace_allowed_channels,
        )

        channel_ids = [int(c.id) for c in self.values]
        try:
            await replace_allowed_channels(
                guild_id=interaction.guild_id,
                channel_ids=channel_ids,
                actor_id=interaction.user.id,
            )
        except CommandAccessMutationError as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "CommandAccessView: replace_allowed_channels raised for guild=%s",
                interaction.guild_id,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        # safe_defer (INV-L) — same rationale as the mode-button path.
        from core.runtime.interaction_helpers import safe_defer

        if not await safe_defer(interaction):
            return
        await _refresh_panel(interaction, _view_of(self))
        if channel_ids:
            await interaction.followup.send(
                f"✅ Allowed channels updated ({len(channel_ids)} "
                f"channel{'s' if len(channel_ids) != 1 else ''}).",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "✅ Allowed channel list cleared.",
                ephemeral=True,
            )


class _DeleteBlockedToggleButton(discord.ui.Button):
    """Flip the per-guild ``delete_blocked_commands`` toggle.

    Reads the current value, writes the opposite through the audited
    service, then refreshes the panel.  Label/state are surfaced in the
    embed (the button stays static like the mode buttons).
    """

    def __init__(self) -> None:
        super().__init__(
            label="Delete blocked commands (toggle)",
            style=discord.ButtonStyle.secondary,
            emoji="🗑️",
            custom_id="settings_command_access.delete_blocked",
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not _is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Administrator or Manage Guild permission required.",
                ephemeral=True,
            )
            return
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ Command access can only be configured inside a server.",
                ephemeral=True,
            )
            return

        from services.command_access_service import (
            CommandAccessMutationError,
            get_policy_snapshot,
            set_delete_blocked_commands,
        )

        snapshot = await get_policy_snapshot(interaction.guild_id)
        new_value = not snapshot.delete_blocked_commands
        try:
            await set_delete_blocked_commands(
                guild_id=interaction.guild_id,
                enabled=new_value,
                actor_id=interaction.user.id,
            )
        except CommandAccessMutationError as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "CommandAccessView: set_delete_blocked_commands raised for guild=%s",
                interaction.guild_id,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        from core.runtime.interaction_helpers import safe_defer

        if not await safe_defer(interaction):
            return
        await _refresh_panel(interaction, _view_of(self))
        state = "On" if new_value else "Off"
        await interaction.followup.send(
            f"✅ Delete blocked commands is now **{state}**.",
            ephemeral=True,
        )


class _BackToHubButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Back to Hub",
            style=discord.ButtonStyle.secondary,
            emoji="↩",
            custom_id="settings_command_access.back",
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.hub import SettingsHubView

        view = await SettingsHubView.create(
            interaction.user,
            interaction.guild_id,
        )
        await interaction.response.edit_message(
            embed=SettingsHubView.build_embed(),
            view=view,
        )


def _view_of(item: discord.ui.Item) -> CommandAccessView:
    """Type-narrowing helper: returns the parent view as
    :class:`CommandAccessView`.

    discord.py exposes ``item.view`` as ``View | None``; every callback
    here only runs while the item is attached to its parent, so the
    narrow is safe at runtime.
    """
    view = item.view
    if not isinstance(view, CommandAccessView):
        raise TypeError(
            f"Expected CommandAccessView parent, got {type(view).__name__}",
        )
    return view


class CommandAccessView(HubView):
    """Settings Manager panel for per-guild command-access policy."""

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        self.add_item(_AllChannelsButton())
        self.add_item(_SelectedChannelsButton())
        self.add_item(_DisabledButton())
        self.add_item(_ChannelAllowlistSelect())
        self.add_item(_DeleteBlockedToggleButton())
        self.add_item(_BackToHubButton())


__all__ = ["CommandAccessView", "build_command_access_embed"]
