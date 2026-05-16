"""Authorization gate for all runtime actions.

This module is the single place where a runtime action (button press,
select-menu choice, modal submission) passes through governance before
executing.  It wraps governance_service.resolve_execution() with the
interaction's session context.

Cogs must NOT call governance_service directly for interaction handlers;
they call can_execute() here so that the authorization path is unified.

Public surface:
    can_execute(interaction, capability) → bool
    require_execution(interaction, capability) → None  (raises on denial)
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.runtime.permissions")


async def can_execute(interaction: discord.Interaction, capability: str) -> bool:
    """Return True if the interaction's user may execute *capability*.

    This is the authoritative authorization check for all runtime actions.
    It delegates to the governance policy engine and logs denials.
    """
    from services import governance_service

    if not interaction.guild_id:
        # DM interactions have no guild-level governance — permit.
        return True

    ctx = governance_service.GovernanceContext.from_interaction(interaction)
    result = await governance_service.resolve_execution(ctx, capability)

    if not result.allowed:
        logger.debug(
            "Execution denied | user=%d | capability=%s | reason=%s",
            interaction.user.id,
            capability,
            result.reason,
        )

    return result.allowed


async def require_execution(interaction: discord.Interaction, capability: str) -> None:
    """Assert that the interaction's user may execute *capability*.

    Sends an ephemeral error reply and raises PermissionError on denial so
    interaction handlers can short-circuit with a single ``await``.
    """
    if not await can_execute(interaction, capability):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ You don't have permission to use this feature.",
                ephemeral=True,
            )
        raise PermissionError(
            f"Capability {capability!r} denied for user {interaction.user.id}",
        )
