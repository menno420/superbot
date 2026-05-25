"""Channel-scope AI policy write UI (PR4A).

Two-step flow:

1. :class:`ChannelPolicySelectView` shows a native
   ``discord.ui.ChannelSelect`` (paginated server-side, no 25-cap
   issue). Operator picks one text channel.
2. :class:`ChannelPolicyModal` opens with mode / min_level /
   cooldown text inputs. Submit calls
   :func:`services.ai_policy_mutation.set_channel_policy`, which
   already enforces the admin gate, runs validation, invalidates
   the resolver cache, and emits ``ai.policy.channel_changed``.

The view never writes to the DB directly — every mutation goes
through ``ai_policy_mutation``.

instruction_profile_id is intentionally omitted from this modal:
profile creation / assignment is a separate surface tracked in a
follow-up PR; channel policy upserts pass ``None`` so the column
clears any prior assignment. That matches the principle "one
modal, one job".
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.ai.policy.channel_view")

_VIEW_TIMEOUT_SECONDS = 180

_VALID_MODES = ("inherit", "always_reply", "mention_only", "disabled")


def _parse_optional_int(raw: str, *, field: str, minimum: int = 0) -> int | None:
    """Treat empty input as ``None`` (clear the override); reject non-int
    or negative values with a typed error message.
    """
    cleaned = (raw or "").strip()
    if not cleaned:
        return None
    try:
        value = int(cleaned)
    except ValueError as exc:
        raise ValueError(f"{field}: must be an integer (got {cleaned!r})") from exc
    if value < minimum:
        raise ValueError(f"{field}: must be >= {minimum} (got {value})")
    return value


class ChannelPolicyModal(discord.ui.Modal):
    """Edit modal that writes one ``ai_channel_policy`` row.

    Fields:

    * ``mode`` — one of ``inherit / always_reply / mention_only / disabled``.
    * ``min_level`` — optional integer XP-level floor for this channel.
    * ``cooldown_seconds`` — optional per-user cooldown.

    Submit calls :func:`services.ai_policy_mutation.set_channel_policy`.
    """

    def __init__(self, channel: discord.abc.GuildChannel) -> None:
        super().__init__(title=f"AI policy · #{channel.name}", timeout=180)
        self.channel = channel
        self.mode_input = discord.ui.TextInput(
            label="Mode",
            placeholder="inherit | always_reply | mention_only | disabled",
            required=True,
            min_length=4,
            max_length=20,
        )
        self.min_level_input = discord.ui.TextInput(
            label="Min level (blank = inherit)",
            placeholder="0",
            required=False,
            max_length=4,
        )
        self.cooldown_input = discord.ui.TextInput(
            label="Cooldown seconds (blank = inherit)",
            placeholder="30",
            required=False,
            max_length=6,
        )
        self.add_item(self.mode_input)
        self.add_item(self.min_level_input)
        self.add_item(self.cooldown_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from services.ai_policy_mutation import (
            AIPolicyMutationError,
            set_channel_policy,
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Edit requires a guild context.",
                ephemeral=True,
            )
            return

        mode = (self.mode_input.value or "").strip()
        if mode not in _VALID_MODES:
            await interaction.response.send_message(
                "❌ mode must be one of: " + ", ".join(f"`{m}`" for m in _VALID_MODES),
                ephemeral=True,
            )
            return
        try:
            min_level = _parse_optional_int(
                str(self.min_level_input.value or ""),
                field="min_level",
            )
            cooldown_seconds = _parse_optional_int(
                str(self.cooldown_input.value or ""),
                field="cooldown_seconds",
            )
        except ValueError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return

        try:
            result = await set_channel_policy(
                interaction.guild.id,
                self.channel.id,
                mode=mode,
                min_level=min_level,
                cooldown_seconds=cooldown_seconds,
                instruction_profile_id=None,
                actor=interaction.user,
            )
        except AIPolicyMutationError as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "ChannelPolicyModal: mutation pipeline raised for guild=%s channel=%s",
                interaction.guild.id,
                self.channel.id,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        bits = [f"mode=`{mode}`"]
        if min_level is not None:
            bits.append(f"min_level=`{min_level}`")
        if cooldown_seconds is not None:
            bits.append(f"cooldown=`{cooldown_seconds}s`")
        await interaction.response.send_message(
            f"✅ Updated AI policy for {self.channel.mention} · "
            + " · ".join(bits)
            + f" (generation {result.generation}).",
            ephemeral=True,
        )


class _ChannelPickSelect(discord.ui.ChannelSelect):
    """Native channel select restricted to text channels."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel to configure…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        # ``ChannelSelect`` resolves to a ``app_commands.AppCommandChannel``;
        # we need the underlying guild channel for ``channel.mention`` in
        # the modal title and for ``channel.id`` in the mutation call.
        resolved = picked
        if interaction.guild is not None:
            full = interaction.guild.get_channel(picked.id)
            if full is not None:
                resolved = full
        await interaction.response.send_modal(ChannelPolicyModal(resolved))


class ChannelPolicySelectView(discord.ui.View):
    """Ephemeral select view for the channel policy flow."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_ChannelPickSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        perms = getattr(interaction.user, "guild_permissions", None)
        if perms is None or not getattr(perms, "administrator", False):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = [
    "ChannelPolicyModal",
    "ChannelPolicySelectView",
]
