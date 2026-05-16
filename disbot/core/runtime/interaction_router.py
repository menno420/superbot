"""Central dispatcher for Discord component interactions.

All button presses, select-menu choices, and modal submissions that belong to
the runtime platform flow through this router.  Each handler is registered
under a *custom_id prefix*; the router strips the prefix and passes the
remainder as the ``action`` argument.

Custom ID convention (set by the panel/view that creates each component):

    <prefix>:<action>[:<opaque-data>]

    e.g.  "economy:daily_claim"
          "mining:mine:iron_ore"

Handlers are registered with:

    router.register("economy", economy_handler)

Where economy_handler has the signature:

    async def economy_handler(
        interaction: discord.Interaction,
        action: str,
        session: Session | None,
        request_id: str,
    ) -> None: ...

All registered handlers are called inside a governance authorization guard.
Handlers that need per-action capability checks should call
ui_permissions.can_execute() or ui_permissions.require_execution() themselves.

Public surface:
    register(prefix, handler)          → None
    dispatch(interaction)              → None
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

import discord

from core.runtime import session_manager

logger = logging.getLogger("bot.runtime.router")

# Handler signature: (interaction, action, session, request_id) → Awaitable[None]
_Handler = Callable[
    [discord.Interaction, str, "session_manager.Session | None", str],
    Awaitable[None],
]

_handlers: dict[str, _Handler] = {}


def register(prefix: str, handler: _Handler) -> None:
    """Register *handler* to receive interactions whose custom_id starts with *prefix*."""
    if prefix in _handlers:
        logger.warning("Overwriting existing handler for prefix %r", prefix)
    _handlers[prefix] = handler
    logger.debug("Registered interaction handler for prefix %r", prefix)


async def dispatch(interaction: discord.Interaction) -> None:
    """Route an incoming interaction to the correct registered handler.

    Generates a unique request_id for traceability, resolves the user's
    session, and delegates to the matching handler.  Unknown prefixes are
    silently ignored (they belong to ephemeral or non-runtime views).
    """
    custom_id: str = getattr(interaction, "custom_id", None) or ""
    if not custom_id:
        # Modals and some select menus carry custom_id differently.
        # Try data attribute as fallback.
        data = getattr(interaction, "data", {}) or {}
        custom_id = data.get("custom_id", "")

    if not custom_id:
        return

    prefix, _, rest = custom_id.partition(":")
    handler = _handlers.get(prefix)
    if handler is None:
        # Not a runtime-managed interaction — ignore.
        return

    request_id = str(uuid.uuid4())
    logger.info(
        "INTERACTION | req=%s | prefix=%s | action=%s | user=%s | guild=%s",
        request_id,
        prefix,
        rest,
        getattr(interaction.user, "id", None),
        interaction.guild_id,
    )

    # Governance gate (Phase 1.3 — centralized enforcement).
    # Check subsystem visibility BEFORE resolving a session or calling the handler.
    # This ensures that disabling a subsystem blocks interactions (button presses,
    # modal submissions) just as it blocks command invocations.
    if interaction.guild_id:
        try:
            from governance import GovernanceContext, get_visible_subsystems

            gov_ctx = GovernanceContext.from_interaction(interaction)
            visible = await get_visible_subsystems(gov_ctx)
            if prefix not in visible:
                logger.debug(
                    "INTERACTION DENIED | req=%s | subsystem=%s | user=%s | "
                    "reason=subsystem_disabled",
                    request_id,
                    prefix,
                    getattr(interaction.user, "id", None),
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ This feature is currently disabled here.",
                        ephemeral=True,
                    )
                return
        except Exception as exc:
            logger.warning(
                "Governance gate failed for req=%s | prefix=%s: %s — allowing (fail-open fallback)",
                request_id,
                prefix,
                exc,
            )

    # Resolve the session for this user+channel+subsystem (subsystem = prefix).
    session: session_manager.Session | None = None
    if interaction.guild_id and interaction.channel_id:
        try:
            session = await session_manager.get_or_create(
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                subsystem=prefix,
            )
        except Exception as exc:
            logger.warning("Session resolution failed for req=%s: %s", request_id, exc)

    try:
        await handler(interaction, rest, session, request_id)
    except PermissionError:
        # ui_permissions.require_execution() already sent the ephemeral reply.
        pass
    except Exception as exc:
        logger.error(
            "Handler error | req=%s | prefix=%s | action=%s: %s",
            request_id,
            prefix,
            rest,
            exc,
            exc_info=True,
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "⚠️ An unexpected error occurred. Please try again.",
                ephemeral=True,
            )
