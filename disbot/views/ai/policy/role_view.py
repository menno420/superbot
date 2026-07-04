"""Role-scope AI policy write UI (PR4A).

Different shape from channel / category:

* ``decision`` is one of ``allow / deny / inherit`` — controls whether
  the role's members can invoke the AI at all.
* ``min_level_override`` is an optional integer that overrides the
  guild minimum_level_default for members of this role.
* ``bypass_cooldown`` is a boolean that lets the role skip the
  per-user cooldown (typed in the modal as ``yes`` / ``no``).

Submit calls :func:`services.ai_policy_mutation.set_role_policy`.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from views.ai.policy.channel_view import _parse_optional_int

logger = logging.getLogger("bot.views.ai.policy.role_view")

_VIEW_TIMEOUT_SECONDS = 180
_VALID_DECISIONS = ("allow", "deny", "inherit")

_TRUE_TOKENS = frozenset({"yes", "y", "true", "1", "on"})
_FALSE_TOKENS = frozenset({"no", "n", "false", "0", "off", ""})


def _parse_bool(raw: str, *, field: str) -> bool:
    """Parse ``yes``/``no`` (and friends) into a boolean.

    Blank counts as ``False`` (the safe default — bypassing the
    cooldown is the opt-in path). Unknown tokens raise a typed error.
    """
    cleaned = (raw or "").strip().lower()
    if cleaned in _TRUE_TOKENS:
        return True
    if cleaned in _FALSE_TOKENS:
        return False
    raise ValueError(
        f"{field}: expected yes/no (got {cleaned!r})",
    )


class RolePolicyModal(discord.ui.Modal):
    """Edit modal that writes one ``ai_role_policy`` row."""

    def __init__(self, role: Any) -> None:
        # ``role`` is typed as ``Any`` for symmetry with the channel /
        # category modals — Discord may hand us either ``discord.Role``
        # or ``app_commands.AppCommandRole``; the modal uses ``.id``,
        # ``.name``, and ``.mention`` only.
        super().__init__(title=f"AI policy · @{role.name}", timeout=180)
        self.role = role
        self.decision_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Decision",
            placeholder="allow | deny | inherit",
            required=True,
            min_length=4,
            max_length=10,
        )
        self.min_level_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Min level override (blank = inherit)",
            placeholder="0",
            required=False,
            max_length=4,
        )
        self.bypass_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Bypass cooldown (yes/no)",
            placeholder="no",
            required=False,
            max_length=5,
        )
        self.add_item(self.decision_input)
        self.add_item(self.min_level_input)
        self.add_item(self.bypass_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from services.ai_policy_mutation import (
            AIPolicyMutationError,
            set_role_policy,
        )

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Edit requires a guild context.",
                ephemeral=True,
            )
            return

        decision = (self.decision_input.value or "").strip().lower()
        if decision not in _VALID_DECISIONS:
            await interaction.response.send_message(
                "❌ decision must be one of: "
                + ", ".join(f"`{d}`" for d in _VALID_DECISIONS),
                ephemeral=True,
            )
            return
        try:
            min_level_override = _parse_optional_int(
                str(self.min_level_input.value or ""),
                field="min_level_override",
            )
            bypass_cooldown = _parse_bool(
                str(self.bypass_input.value or ""),
                field="bypass_cooldown",
            )
        except ValueError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return

        try:
            result = await set_role_policy(
                interaction.guild.id,
                self.role.id,
                decision=decision,
                min_level_override=min_level_override,
                bypass_cooldown=bypass_cooldown,
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
                "RolePolicyModal: mutation pipeline raised for guild=%s role=%s",
                interaction.guild.id,
                self.role.id,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        bits = [f"decision=`{decision}`"]
        if min_level_override is not None:
            bits.append(f"min_level_override=`{min_level_override}`")
        bits.append(f"bypass_cooldown=`{bypass_cooldown}`")
        await interaction.response.send_message(
            f"✅ Updated AI policy for {self.role.mention} · "
            + " · ".join(bits)
            + f" (generation {result.generation}).",
            ephemeral=True,
        )


class _RolePickSelect(discord.ui.RoleSelect):
    """Native role select with the same pick-one shape."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a role to configure…",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        # The pin test ``test_no_raw_guild_lookups_outside_resolver``
        # forbids bare ``guild.get_role`` in non-resolver code; route
        # through core.runtime.guild_resources.resolve_role instead so
        # missing-role handling stays uniform across the codebase.
        resolved = picked
        if interaction.guild is not None:
            from core.runtime import guild_resources

            full = guild_resources.resolve_role(
                interaction.guild,
                role_id=picked.id,
            )
            if full is not None:
                resolved = full
        await interaction.response.send_modal(RolePolicyModal(resolved))


class RolePolicySelectView(discord.ui.View):
    """Ephemeral select view for the role policy flow."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_RolePickSelect())

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
    "RolePolicyModal",
    "RolePolicySelectView",
]
