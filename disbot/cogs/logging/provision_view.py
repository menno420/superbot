"""LogChannelProvisionView — S7c create-channel flow for logging bindings.

Ephemeral view that shows the operator a preview of the channel
about to be created, then requires an explicit Confirm click before
calling :class:`ResourceProvisioningPipeline`.  The pipeline's
11-step contract handles the create + bind + audit atomically (the
binding write composes through :class:`BindingMutationPipeline` as
part of step 8).

Strict scope (S7c):
- channel creation only; existing-channel selection is S7b.
- no preview side effects (the pipeline's preview is side-effect-free).
- explicit confirmation required — no silent provisioning.
- the pipeline emits both the resource_provisioning_audit row and
  the canonical advisory ``resource.provisioned`` event.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.cogs.logging.provision_view")


# Route tables — kept in sync with ``services.server_logging``'s
# ``_ROUTE_TO_BINDING``. A consistency test pins them together.
_KIND_TO_BINDING: dict[str, str] = {
    "mod": "mod_channel",
    "cleanup": "cleanup_channel",
    "debug": "debug_channel",
    "info": "info_channel",
    "warning": "warning_channel",
    "error": "error_channel",
    "audit": "audit_channel",
    # Server event logging v1 (Q-0109) — passive-event routes.
    "events": "events_channel",
    "message_log": "message_channel",
    "member_log": "member_channel",
    "role_log": "role_channel",
}

_KIND_TO_LABEL: dict[str, str] = {
    "mod": "moderation log",
    "cleanup": "cleanup log",
    "debug": "debug log",
    "info": "info log",
    "warning": "warning log",
    "error": "error log",
    "audit": "audit log",
    "events": "server event log",
    "message_log": "message event log",
    "member_log": "member event log",
    "role_log": "role event log",
}


def _binding_name_for(kind: str) -> str:
    binding_name = _KIND_TO_BINDING.get(kind)
    if binding_name is None:
        raise ValueError(f"unknown logging channel kind: {kind!r}")
    return binding_name


def _label_for(kind: str) -> str:
    """Human label for *kind* — **total**, never raises (mirror of
    ``select_view._label_for``). Every known kind still gets an explicit,
    nicer label (pinned by ``test_route_labels_cover_every_kind``); the
    derived fallback only guards a future kind added to the binding map but
    not here.
    """
    return _KIND_TO_LABEL.get(kind, f"{kind.replace('_', ' ')} log")


async def build_preview_embed(
    guild: discord.Guild,
    kind: str,
) -> tuple[discord.Embed, bool]:
    """Return ``(embed, allowed)`` for the preview shown before Confirm.

    Calls :meth:`ResourceProvisioningPipeline.preview` — no side
    effects.  When ``allowed=False`` the embed surfaces the warnings
    so the operator sees the cause (permission missing, slot already
    bound, name collision, etc.) without having to click Confirm and
    fail.
    """
    binding_name = _binding_name_for(kind)
    from services.resource_provisioning import (
        ProvisioningRequest,
        ResourceProvisioningPipeline,
    )

    request = ProvisioningRequest(
        subsystem="logging",
        binding_name=binding_name,
        mode="create",
    )
    preview = await ResourceProvisioningPipeline().preview(guild, request)

    color = discord.Color.green() if preview.allowed else discord.Color.orange()
    label = _label_for(kind)
    embed = discord.Embed(
        title=f"🆕 Provision {label} channel — preview",
        description=(
            "This will create a new Discord channel and bind it to "
            f"`logging.{binding_name}`.  All writes route through "
            "`ResourceProvisioningPipeline` + `BindingMutationPipeline`, "
            "and an audit row is recorded."
        ),
        color=color,
    )
    embed.add_field(
        name="Action",
        value=f"`{preview.action}`",
        inline=True,
    )
    embed.add_field(
        name="Target name",
        value=f"`{preview.target_name}`" if preview.target_name else "*(unset)*",
        inline=True,
    )
    embed.add_field(
        name="Allowed",
        value="✅ yes" if preview.allowed else "⚪ no",
        inline=True,
    )
    if preview.warnings:
        embed.add_field(
            name="Warnings",
            value="\n".join(f"• {w}" for w in preview.warnings)[:1024],
            inline=False,
        )
    embed.set_footer(
        text=(
            "Click Confirm Create to provision.  Cancel to abort."
            if preview.allowed
            else "Address the warnings above before retrying."
        ),
    )
    return embed, preview.allowed


class _ConfirmCreateButton(discord.ui.Button):
    """Confirm + run the audited create + bind transaction."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(
            label="Confirm Create",
            style=discord.ButtonStyle.success,
            row=0,
            emoji="🆕",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _commit_provision(interaction, kind=self.kind)


class _CancelButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            row=0,
            emoji="✖",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Cancelled",
            description="No channel created.  No audit row recorded.",
            color=discord.Color.greyple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        view = self.view
        if view is not None:
            view.stop()


class LogChannelProvisionView(discord.ui.View):
    """Invoker-locked preview-then-confirm view.

    The preview embed is built by the caller and shown when the
    view opens.  The Confirm button calls
    :meth:`ResourceProvisioningPipeline.provision(confirmed=True)`,
    which runs the 11-step contract: option resolution, permission
    check, name validation, optional collision handling, Discord
    create, binding write via :class:`BindingMutationPipeline`,
    audit row, event emission.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        kind: str,
        *,
        confirm_enabled: bool,
    ) -> None:
        # Validate kind up front so a bad caller sees ValueError.
        _binding_name_for(kind)
        super().__init__(timeout=120)
        self._author = author
        self.kind = kind
        confirm = _ConfirmCreateButton(kind)
        if not confirm_enabled:
            confirm.disabled = True
        self.add_item(confirm)
        self.add_item(_CancelButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self._author.id:
            await interaction.response.send_message(
                "This selector isn't yours.",
                ephemeral=True,
            )
            return False
        return True


# ---------------------------------------------------------------------------
# Commit — routes through ResourceProvisioningPipeline.provision(confirmed=True)
# ---------------------------------------------------------------------------


async def _commit_provision(
    interaction: discord.Interaction,
    *,
    kind: str,
) -> None:
    """Run the audited create + bind transaction."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Provisioning logging channels requires a guild context.",
            ephemeral=True,
        )
        return

    binding_name = _binding_name_for(kind)
    actor = interaction.user
    if not isinstance(actor, discord.Member):
        await interaction.response.send_message(
            "Could not resolve your guild membership for the audit row.",
            ephemeral=True,
        )
        return

    from services.resource_provisioning import (
        ProvisioningRequest,
        ResourceProvisioningError,
        ResourceProvisioningPipeline,
    )

    request = ProvisioningRequest(
        subsystem="logging",
        binding_name=binding_name,
        mode="create",
    )

    try:
        result = await ResourceProvisioningPipeline().provision(
            guild,
            request,
            actor,
            confirmed=True,
        )
    except ResourceProvisioningError as exc:
        logger.warning(
            "logging.%s provision failed (guild=%d, actor=%d): %s",
            binding_name,
            guild.id,
            actor.id,
            exc,
        )
        await interaction.response.send_message(
            f"❌ Provision failed: `{type(exc).__name__}`: {exc!s:.200}",
            ephemeral=True,
        )
        return

    channel_mention = (
        f"<#{result.resource_id}>" if result.resource_id is not None else "*(unknown)*"
    )
    embed = discord.Embed(
        title=f"✅ {_label_for(kind).title()} channel provisioned",
        description=(
            f"Created {channel_mention} and bound it to "
            f"`logging.{binding_name}`.\n"
            f"Outcome: `{result.outcome}` · "
            f"binding_written: `{result.binding_written}` · "
            f"audit_id: `{result.audit_id}`."
        ),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


__all__ = ["LogChannelProvisionView", "build_preview_embed"]
