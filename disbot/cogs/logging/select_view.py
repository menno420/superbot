"""LogChannelSelectView — S7b existing-channel selection for logging bindings.

Ephemeral view that lets an operator pick an existing TextChannel to
bind as ``logging.mod_channel`` or ``logging.cleanup_channel``.  All
writes route through :class:`BindingMutationPipeline` — no direct
binding writes.

The view is launched from the ``!logging set <mod|cleanup>`` typed
command (S7b) and will also be embedded in the logging admin panel
introduced in S7d.

Strict scope (S7b):
- existing-channel selection only; channel creation is S7c.
- bindings only; no scalar settings writes here.
- ephemeral confirmation messages so the operator gets immediate
  feedback without anchoring a panel.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.subsystem_schema import BindingKind

logger = logging.getLogger("bot.cogs.logging.select_view")


# Route tables — kept in sync with ``services.server_logging``'s
# ``_ROUTE_TO_BINDING``. A consistency test pins them together.
_KIND_TO_BINDING: dict[str, str] = {
    "mod": "mod_channel",
    "cleanup": "cleanup_channel",
    # Phase 9a routes — accept the new severity/audit kinds.
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
    # Server event logging v1 (Q-0109) — passive-event routes. Kept in sync
    # with ``_KIND_TO_BINDING`` (and ``provision_view._KIND_TO_LABEL``) by
    # ``test_logging_routes_panel.test_route_labels_cover_every_kind``. These
    # were missing until the Routes "Set Channel" crash: ``_LogChannelSelect``
    # indexed ``_KIND_TO_LABEL[kind]`` for the placeholder and raised KeyError
    # for every event route, surfacing as the generic view-error ephemeral.
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
    """Human label for *kind* — **total**, never raises.

    Falls back to a derived ``"<kind> log"`` for any route not explicitly
    named, so a future route added to ``_KIND_TO_BINDING`` can never crash the
    channel picker the way the Q-0109 event routes did (added to the binding
    map but not this label map → KeyError at the ``_LogChannelSelect``
    placeholder). The pin test still requires an explicit, nicer label for
    every known kind — this is the defence-in-depth backstop, not a licence to
    skip the map.
    """
    return _KIND_TO_LABEL.get(kind, f"{kind.replace('_', ' ')} log")


class _LogChannelSelect(discord.ui.ChannelSelect):  # type: ignore[type-arg]
    """Channel picker constrained to TextChannels in the current guild."""

    def __init__(self, kind: str) -> None:
        # Validate up front so a bad caller sees ValueError rather
        # than a confusing KeyError from the label lookup below.
        _binding_name_for(kind)
        self.kind = kind
        super().__init__(
            placeholder=f"Pick the {_label_for(kind)} channel…",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _commit_selection(
            interaction,
            kind=self.kind,
            target=self.values[0],
        )


class _ClearBindingButton(discord.ui.Button):
    """Clear the current binding (sets target to NULL)."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(
            label="Clear binding",
            style=discord.ButtonStyle.secondary,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await _commit_clear(interaction, kind=self.kind)


# Extends discord.ui.View directly (not BaseView): specialized lifecycle —
# a single-shot ephemeral select flow that self-stops after a successful
# interaction and edits no parent message; the ephemeral message is
# auto-dismissed by Discord, so BaseView's on_timeout edit has no target.
class LogChannelSelectView(discord.ui.View):
    """Invoker-locked view with one ChannelSelect + a Clear button.

    The view does not edit a parent message; selection callbacks send
    ephemeral confirmation messages.  The view itself self-stops after
    a successful interaction.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        kind: str,
    ) -> None:
        super().__init__(timeout=120)
        self._author = author
        self.kind = kind
        self.add_item(_LogChannelSelect(kind))
        self.add_item(_ClearBindingButton(kind))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self._author.id:
            await interaction.response.send_message(
                "This selector isn't yours.",
                ephemeral=True,
            )
            return False
        return True


# ---------------------------------------------------------------------------
# Commit helpers — both go through BindingMutationPipeline
# ---------------------------------------------------------------------------


async def _commit_selection(
    interaction: discord.Interaction,
    *,
    kind: str,
    target: (
        discord.abc.GuildChannel
        | discord.app_commands.AppCommandChannel
        | discord.app_commands.AppCommandThread
    ),
) -> None:
    """Write the binding via :class:`BindingMutationPipeline`.

    ``target`` accepts the interaction-time channel forms produced by
    :class:`discord.ui.ChannelSelect` (``AppCommandChannel`` /
    ``AppCommandThread``) as well as resolved guild channels — only
    ``.id`` and ``.mention`` are used.

    Always responds ephemerally with success/failure.  Caller-facing
    errors carry the exception class name; the full traceback is
    logged.
    """
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Binding logging channels requires a guild context.",
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

    from services.binding_mutation import (
        BindingMutationError,
        BindingMutationPipeline,
    )

    try:
        result = await BindingMutationPipeline().set_binding(
            guild=guild,
            subsystem="logging",
            binding_name=binding_name,
            kind=BindingKind.CHANNEL,
            target_id=target.id,
            actor=actor,
        )
    except BindingMutationError as exc:
        logger.warning(
            "logging.%s bind failed (guild=%d, target=%d, actor=%d): %s",
            binding_name,
            guild.id,
            target.id,
            actor.id,
            exc,
        )
        await interaction.response.send_message(
            f"❌ Could not bind {_label_for(kind)} channel: "
            f"`{type(exc).__name__}`: {exc!s:.200}",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title=f"✅ {_label_for(kind).title()} channel bound",
        description=(
            f"Bound `logging.{binding_name}` → {target.mention}.\n"
            f"Status: `{result.new_status.value}`."
        ),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def _commit_clear(
    interaction: discord.Interaction,
    *,
    kind: str,
) -> None:
    """Clear the binding via :class:`BindingMutationPipeline`."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Clearing logging bindings requires a guild context.",
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

    from services.binding_mutation import (
        BindingMutationError,
        BindingMutationPipeline,
    )

    try:
        await BindingMutationPipeline().clear_binding(
            guild=guild,
            subsystem="logging",
            binding_name=binding_name,
            kind=BindingKind.CHANNEL,
            actor=actor,
        )
    except BindingMutationError as exc:
        logger.warning(
            "logging.%s clear failed (guild=%d, actor=%d): %s",
            binding_name,
            guild.id,
            actor.id,
            exc,
        )
        await interaction.response.send_message(
            f"❌ Could not clear {_label_for(kind)} channel: "
            f"`{type(exc).__name__}`: {exc!s:.200}",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title=f"✅ {_label_for(kind).title()} channel cleared",
        description=(
            f"Cleared `logging.{binding_name}`.  Falls back to "
            "the legacy scalar key (or, for cleanup, to the mod "
            "channel binding)."
        ),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


__all__ = ["LogChannelSelectView"]
