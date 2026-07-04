"""Category-scope AI policy write UI (PR4A).

Mirrors :mod:`views.ai.policy.channel_view` for the category scope.
Discord's ``ChannelSelect`` accepts ``channel_types=[ChannelType.category]``
so the operator picks a category by name; the rest of the flow is
identical: a modal with mode / min_level / cooldown_seconds, submit
calls :func:`services.ai_policy_mutation.set_category_policy`.

Category mode applies to every channel in the category as the default;
per-channel overrides win when set. The valid modes are identical to
the channel scope (``inherit / always_reply / mention_only /
disabled``).
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from views.ai.policy.channel_view import _parse_optional_int

logger = logging.getLogger("bot.views.ai.policy.category_view")

_VIEW_TIMEOUT_SECONDS = 180

_VALID_MODES = ("inherit", "always_reply", "mention_only", "disabled")


class CategoryPolicyModal(discord.ui.Modal):
    """Edit modal that writes one ``ai_category_policy`` row.

    Same shape as :class:`views.ai.policy.channel_view.ChannelPolicyModal`;
    the only differences are the mutation target table and the title.
    """

    def __init__(self, category: Any) -> None:
        # See ChannelPolicyModal for the rationale behind the ``Any``
        # annotation — Discord may hand us either ``CategoryChannel``
        # or ``AppCommandChannel``; the modal only uses ``.id`` and
        # ``.name``.
        super().__init__(title=f"AI policy · {category.name}", timeout=180)
        self.category = category
        self.mode_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Mode",
            placeholder="inherit | always_reply | mention_only | disabled",
            required=True,
            min_length=4,
            max_length=20,
        )
        self.min_level_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Min level (blank = inherit)",
            placeholder="0",
            required=False,
            max_length=4,
        )
        self.cooldown_input: discord.ui.TextInput = discord.ui.TextInput(
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
            set_category_policy,
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

        from services.ai_policy_mutation import UNCHANGED

        try:
            result = await set_category_policy(
                interaction.guild.id,
                self.category.id,
                mode=mode,
                min_level=min_level,
                cooldown_seconds=cooldown_seconds,
                instruction_profile_id=UNCHANGED,
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
                "CategoryPolicyModal: mutation pipeline raised for "
                "guild=%s category=%s",
                interaction.guild.id,
                self.category.id,
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
            f"✅ Updated AI policy for category **{self.category.name}** · "
            + " · ".join(bits)
            + f" (generation {result.generation}).",
            ephemeral=True,
        )


class _CategoryPickSelect(discord.ui.ChannelSelect):
    """Native channel select restricted to category channels."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a category to configure…",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        category: Any = picked
        if interaction.guild is not None:
            from core.runtime import guild_resources

            full = guild_resources.resolve_channel(
                interaction.guild,
                channel_id=picked.id,
                kind="category",
            )
            if full is not None:
                category = full
        await interaction.response.send_modal(CategoryPolicyModal(category))


class CategoryPolicySelectView(discord.ui.View):
    """Ephemeral select view for the category policy flow."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_CategoryPickSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (Q-0212).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = [
    "CategoryPolicyModal",
    "CategoryPolicySelectView",
]
