"""Resource provisioning launcher for the Settings Manager.

S7c counterpart of :mod:`views.settings.edit_binding`: this widget
lets a Settings Manager operator request that the bot provision a
resource (channel / role / category) declared as a
:class:`~core.runtime.resource_specs.ResourceRequirement` on the
subsystem schema.

Flow:

1. The SubsystemSettingsView's resource dropdown lists every
   declared :class:`ResourceRequirement` for the subsystem.
2. Picking one opens a :class:`ProvisionResourceView` with two
   buttons:

   * **Use existing** — opens the binding edit widget so the
     operator can point the slot at an already-present Discord
     resource (`BindingMutationPipeline` write).
   * **Create new** — runs the
     :class:`ResourceProvisioningPipeline` preview-then-confirm
     handshake and provisions a new Discord resource.

3. Outcomes (`reuse_existing`, `create_new`, `blocked`,
   permission errors) flow back as ephemeral messages; the parent
   subsystem panel is refreshed so the new binding state shows up
   without re-opening the panel.

This file is allowlisted by
``tests/unit/invariants/test_settings_cog_read_only.py`` because it
IS the resource-provisioning mutation surface for the Settings
Manager.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views.settings.provision_resource")


def _resource_kind_to_binding_kind(kind: str) -> str | None:
    """Map ``ResourceKind`` value to the corresponding binding-edit kind."""
    mapping = {
        "channel": "channel",
        "role": "role",
        "category": "category",
        "thread": "thread",
    }
    return mapping.get(kind.lower())


async def _provision_create(
    interaction: discord.Interaction,
    subsystem: str,
    binding_name: str,
    parent_message: discord.Message | None,
) -> None:
    """Run preview + confirmed provision through the resource pipeline."""
    from services.resource_provisioning import (
        ProvisioningConfirmationRequired,
        ProvisioningRequest,
        ResourceProvisioningError,
        ResourceProvisioningPipeline,
    )

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Provisioning requires a guild context.",
            ephemeral=True,
        )
        return

    pipeline = ResourceProvisioningPipeline()
    request = ProvisioningRequest(
        subsystem=subsystem,
        binding_name=binding_name,
        mode="create",
    )

    try:
        preview = await pipeline.preview(guild, request)
    except ResourceProvisioningError as exc:
        await interaction.response.send_message(
            f"❌ Preview failed: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    if not preview.allowed:
        warnings_text = "\n".join(f"• {w}" for w in preview.warnings) or "(no detail)"
        await interaction.response.send_message(
            f"⚠️ Provisioning blocked for `{subsystem}.{binding_name}` "
            f"(target=`{preview.target_name}`):\n{warnings_text}",
            ephemeral=True,
        )
        return

    try:
        result = await pipeline.provision(
            guild,
            request,
            interaction.user,
            confirmed=True,
        )
    except ProvisioningConfirmationRequired:
        # Should never happen — we passed confirmed=True — but the
        # pipeline raises it as part of its contract.  Surface a
        # readable error rather than crashing the UI.
        await interaction.response.send_message(
            "❌ Pipeline refused without explicit confirmation; "
            "this is a Settings Manager bug — please file an issue.",
            ephemeral=True,
        )
        return
    except ResourceProvisioningError as exc:
        await interaction.response.send_message(
            f"❌ Provision failed: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:  # noqa: BLE001 — defensive UI boundary
        logger.exception(
            "ProvisionResource: pipeline raised for %s.%s",
            subsystem,
            binding_name,
        )
        await interaction.response.send_message(
            f"❌ Unexpected error: {type(exc).__name__}: {exc}",
            ephemeral=True,
        )
        return

    if result.outcome == "success" and result.resource_id is not None:
        mention = (
            f"<#{result.resource_id}>"
            if result.kind in ("channel", "category", "thread")
            else f"<@&{result.resource_id}>"
        )
        verb = "Created" if result.created else "Reused"
        await interaction.response.send_message(
            f"✅ {verb} {mention} and bound it to `{subsystem}.{binding_name}`.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"⚠️ Provision finished with outcome `{result.outcome}` "
            f"(binding_written={result.binding_written}).",
            ephemeral=True,
        )

    await _refresh_parent(interaction, subsystem, parent_message)


class _UseExistingButton(discord.ui.Button):  # type: ignore[type-arg]
    """Opens the binding edit widget so the operator points at an existing resource."""

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        kind: str,
        parent_message: discord.Message | None,
    ) -> None:
        super().__init__(
            label="Use existing",
            style=discord.ButtonStyle.secondary,
            row=0,
        )
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.kind = kind
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.edit_binding import BindingEditView

        try:
            view = BindingEditView(
                self.subsystem,
                self.binding_name,
                self.kind,
                self.parent_message,
            )
        except ValueError as exc:
            await interaction.response.send_message(
                f"❌ Cannot edit binding: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Pick an existing {self.kind} for "
            f"`{self.subsystem}.{self.binding_name}`:",
            view=view,
            ephemeral=True,
        )


class _CreateNewButton(discord.ui.Button):  # type: ignore[type-arg]
    """Runs the resource provisioning pipeline (preview + confirmed provision)."""

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        parent_message: discord.Message | None,
    ) -> None:
        super().__init__(
            label="Create new",
            style=discord.ButtonStyle.success,
            row=0,
        )
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.parent_message = parent_message

    async def callback(self, interaction: discord.Interaction) -> None:
        await _provision_create(
            interaction,
            self.subsystem,
            self.binding_name,
            self.parent_message,
        )


class ProvisionResourceView(discord.ui.View):
    """Ephemeral view: Use existing | Create new for one resource slot."""

    def __init__(
        self,
        subsystem: str,
        binding_name: str,
        kind: str,
        parent_message: discord.Message | None = None,
    ) -> None:
        super().__init__(timeout=180)
        bind_kind = _resource_kind_to_binding_kind(kind)
        if bind_kind is not None:
            self.add_item(
                _UseExistingButton(subsystem, binding_name, bind_kind, parent_message),
            )
        self.add_item(
            _CreateNewButton(subsystem, binding_name, parent_message),
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
    except Exception:  # noqa: BLE001 — soft-fail; pipeline result is canonical
        logger.debug(
            "ProvisionResource: parent refresh failed for %s",
            subsystem,
            exc_info=True,
        )


__all__ = ["ProvisionResourceView"]
