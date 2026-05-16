"""Base class and registry for persistent Discord UI views.

A PersistentView survives bot restarts because:
  1. timeout=None — discord.py never calls on_timeout.
  2. All components have explicit static custom_ids — discord.py can match
     incoming interactions to registered view instances even after restart.
  3. A sentinel instance is registered with bot.add_view(view, message_id=X)
     at startup for every active panel anchor in the DB.

Subclass contract:
  • Set SUBSYSTEM class variable to the subsystem name (e.g. "economy").
  • Give EVERY component an explicit custom_id in "{SUBSYSTEM}:{action}" format.
  • Call persistent_views.register(MyView) after the class definition.
  • Do NOT store per-user mutable state in instance variables — views are
    reused across users after restart.  Fetch all needed data from DB using
    interaction.user.id and interaction.guild_id inside callbacks.
  • interaction_check() in this base class enforces ownership via anchor lookup.

Public surface:
    register(cls)              — decorator/call to register a view class
    get_view_class(subsystem)  — retrieve registered class by subsystem name
    PersistentView             — base class to extend
"""

from __future__ import annotations

import logging
from typing import ClassVar

import discord

logger = logging.getLogger("bot.runtime.views")

_REGISTRY: dict[str, type[PersistentView]] = {}


def register(cls: type[PersistentView]) -> type[PersistentView]:
    """Register a PersistentView subclass for restart recovery."""
    _REGISTRY[cls.SUBSYSTEM] = cls
    return cls


def get_view_class(subsystem: str) -> type[PersistentView] | None:
    """Return the registered PersistentView class for *subsystem*, or None."""
    return _REGISTRY.get(subsystem)


class PersistentView(discord.ui.View):
    """Base class for views that survive bot restarts.

    Stateless: callbacks receive all context via the ``interaction`` argument.
    Ownership: ``interaction_check`` queries the anchor table to verify the
    interacting user owns the panel.
    """

    SUBSYSTEM: ClassVar[str] = ""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Allow only the panel's owner to interact."""
        from core.runtime import message_anchor_manager

        if not interaction.message:
            return True

        anchor = await message_anchor_manager.get_by_message_id(interaction.message.id)
        if anchor is None:
            return True

        if interaction.user.id != anchor["user_id"]:
            await interaction.response.send_message(
                "This panel isn't yours.", ephemeral=True
            )
            return False
        return True

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        logger.error(
            "PersistentView error | view=%s item_type=%s custom_id=%r label=%r "
            "user=%s guild=%s channel=%s message=%s",
            type(self).__name__,
            type(item).__name__,
            getattr(item, "custom_id", None),
            getattr(item, "label", None),
            getattr(interaction.user, "id", None),
            interaction.guild_id,
            interaction.channel_id,
            interaction.message.id if interaction.message else None,
            exc_info=error,
        )
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "An error occurred. Please try again.", ephemeral=True
                )
            except Exception:
                pass
