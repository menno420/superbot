"""Binding edit widget for the Settings Manager.

S5 (read-only Settings Manager) listed bindings inline in the
subsystem embed but offered no edit path.  S6 added scalar edit
flows that route through :class:`SettingsMutationPipeline`.  This
module is the S7 counterpart for ``BindingSpec`` slots: operators
pick a channel / role / category target for a declared binding and
the write flows through
:class:`services.binding_mutation.BindingMutationPipeline`.

Dispatch:

1. Operator picks a binding in the SubsystemSettingsView's binding
   dropdown.
2. The dispatcher reads :attr:`BindingSpec.kind` and replies with an
   ephemeral message hosting :class:`BindingEditView`.
3. Operator picks a target (channel/role/category) from the native
   select OR clicks **Clear** to remove the binding.
4. The callback writes through
   :class:`BindingMutationPipeline.set_binding` / ``clear_binding``
   and confirms ephemerally.

This file is allowlisted by
``tests/unit/invariants/test_settings_cog_read_only.py`` because it
IS the binding mutation surface for the Settings Manager.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.edit_binding")


async def _commit_binding(
    interaction: discord.Interaction,
    subsystem: str,
    binding_name: str,
    kind: str,
    target_id: int,
    parent_message: discord.Message | None,
) -> None:
    """Write a binding via :class:`BindingMutationPipeline`."""
    from core.runtime.subsystem_schema import BindingKind
    from services.binding_mutation import (
        BindingMutationError,
        BindingMutationPipeline,
    )

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Binding edit requires a guild context.",
            ephemeral=True,
        )
        return

    try:
        binding_kind = BindingKind(kind)
    except ValueError:
        await interaction.response.send_message(
            f"❌ Unknown binding kind `{kind}`.",
            ephemeral=True,
        )
        return

    try:
        result = await BindingMutationPipeline().set_binding(
            guild,
            subsystem,
            binding_name,
            binding_kind,
            target_id,
            interaction.user,
        )
    except BindingMutationError as exc:
        await interaction.response.send_message(
            f"❌ {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:  # noqa: BLE001 — defensive UI boundary
        logger.exception(
            "BindingEdit: pipeline raised for %s.%s",
            subsystem,
            binding_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    mention = _format_target_mention(kind, target_id)
    await interaction.response.send_message(
        f"✅ Bound `{subsystem}.{binding_name}` → {mention} "
        f"(was `{result.old_target_id}`).",
        ephemeral=True,
    )
    await _refresh_parent(interaction, subsystem, parent_message)


async def _commit_clear(
    interaction: discord.Interaction,
    subsystem: str,
    binding_name: str,
    kind: str,
    parent_message: discord.Message | None,
) -> None:
    """Clear a binding via :class:`BindingMutationPipeline`."""
    from core.runtime.subsystem_schema import BindingKind
    from services.binding_mutation import (
        BindingMutationError,
        BindingMutationPipeline,
    )

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Binding edit requires a guild context.",
            ephemeral=True,
        )
        return

    try:
        binding_kind = BindingKind(kind)
    except ValueError:
        await interaction.response.send_message(
            f"❌ Unknown binding kind `{kind}`.",
            ephemeral=True,
        )
        return

    try:
        result = await BindingMutationPipeline().clear_binding(
            guild,
            subsystem,
            binding_name,
            binding_kind,
            interaction.user,
        )
    except BindingMutationError as exc:
        await interaction.response.send_message(
            f"❌ {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:  # noqa: BLE001 — defensive UI boundary
        logger.exception(
            "BindingEdit: pipeline raised on clear for %s.%s",
            subsystem,
            binding_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Cleared `{subsystem}.{binding_name}` (was `{result.old_target_id}`).",
        ephemeral=True,
    )
    await _refresh_parent(interaction, subsystem, parent_message)


def _format_target_mention(kind: str, target_id: int) -> str:
    if kind in ("channel", "category", "thread"):
        return f"<#{target_id}>"
    if kind == "role":
        return f"<@&{target_id}>"
    if kind == "member":
        return f"<@{target_id}>"
    return f"`{target_id}`"


class _BindingChannelPick(discord.ui.ChannelSelect):  # type: ignore[type-arg]
    """Native channel select; channel_types narrowed to the binding kind."""

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        kind: str,
        parent_message: discord.Message | None,
    ) -> None:
        if kind == "category":
            channel_types = [discord.ChannelType.category]
        elif kind == "thread":
            channel_types = [
                discord.ChannelType.public_thread,
                discord.ChannelType.private_thread,
            ]
        else:
            channel_types = [discord.ChannelType.text]
        super().__init__(
            placeholder=f"Pick a {kind}…",
            channel_types=channel_types,
            min_values=1,
            max_values=1,
            row=0,
        )
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.kind = kind
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        await _commit_binding(
            interaction,
            self.subsystem,
            self.binding_name,
            self.kind,
            picked.id,
            self.parent_message,
        )


class _BindingRolePick(discord.ui.RoleSelect):  # type: ignore[type-arg]
    """Native role select for ``BindingKind.ROLE`` slots."""

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        parent_message: discord.Message | None,
    ) -> None:
        super().__init__(
            placeholder="Pick a role…",
            min_values=1,
            max_values=1,
            row=0,
        )
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        await _commit_binding(
            interaction,
            self.subsystem,
            self.binding_name,
            "role",
            picked.id,
            self.parent_message,
        )


class _ClearBindingButton(discord.ui.Button):  # type: ignore[type-arg]
    """Clear the binding by routing through ``clear_binding``."""

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        kind: str,
        parent_message: discord.Message | None,
    ) -> None:
        super().__init__(
            label="Clear",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.kind = kind
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        await _commit_clear(
            interaction,
            self.subsystem,
            self.binding_name,
            self.kind,
            self.parent_message,
        )


class BindingEditView(discord.ui.View):
    """Ephemeral follow-up view hosting the binding select + clear button.

    Renders a different native select based on ``kind``:

    * ``CHANNEL`` / ``CATEGORY`` / ``THREAD`` → :class:`ChannelSelect`
      with appropriate ``channel_types``.
    * ``ROLE`` → :class:`RoleSelect`.
    * ``MEMBER`` is NOT supported here (the Settings Manager does not
      surface member bindings; they live elsewhere).

    Unsupported kinds raise ``ValueError`` at construction so the
    caller can fall back to a "not yet editable" message rather than
    silently rendering an empty view.
    """

    SUPPORTED_KINDS: frozenset[str] = frozenset(
        {"channel", "role", "category", "thread"},
    )

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        kind: str,
        parent_message: discord.Message | None = None,
    ) -> None:
        if kind not in self.SUPPORTED_KINDS:
            raise ValueError(
                f"BindingEditView does not support kind={kind!r}; "
                f"supported: {sorted(self.SUPPORTED_KINDS)}",
            )
        super().__init__(timeout=180)
        if kind == "role":
            self.add_item(_BindingRolePick(subsystem, binding_name, parent_message))
        else:
            self.add_item(
                _BindingChannelPick(subsystem, binding_name, kind, parent_message),
            )
        self.add_item(
            _ClearBindingButton(subsystem, binding_name, kind, parent_message),
        )


async def _refresh_parent(
    interaction: discord.Interaction,
    subsystem: str,
    parent_message: discord.Message | None,
) -> None:
    if parent_message is None:
        return
    try:
        from views.settings.subsystem_view import build_subsystem_embed

        embed = await build_subsystem_embed(interaction, subsystem)
        await parent_message.edit(embed=embed)
    except Exception:  # noqa: BLE001 — soft-fail; the write already succeeded
        logger.debug(
            "BindingEdit: parent refresh failed for %s",
            subsystem,
            exc_info=True,
        )


__all__ = ["BindingEditView"]
