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

from typing import ClassVar

import discord

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

    # RC-3 / ADR-004: when the panel's anchor row is missing we cannot verify
    # ownership.  Public / read-only panels keep allowing the interaction
    # (availability over strictness); owner-scoped or mutating panels override
    # this to True so they FAIL CLOSED — deny rather than let an unverified user
    # drive a privileged panel.  Default False = today's behavior (revert-safe).
    FAIL_CLOSED_ON_MISSING_ANCHOR: ClassVar[bool] = False

    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Allow only the panel's owner to interact."""
        from core.runtime import message_anchor_manager

        if not interaction.message:
            return True

        anchor = await message_anchor_manager.get_by_message_id(interaction.message.id)
        if anchor is None:
            if self.FAIL_CLOSED_ON_MISSING_ANCHOR:
                # Owner-scoped panel + unverifiable ownership → deny (ADR-004).
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "This panel can no longer be verified — please re-open it.",
                        ephemeral=True,
                    )
                return False
            return True

        if interaction.user.id != anchor["user_id"]:
            await interaction.response.send_message(
                "This panel isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        from views.base import handle_view_error

        await handle_view_error(self, interaction, error, item)


# ---------------------------------------------------------------------------
# Diagnostics registration — Phase S1.3
# ---------------------------------------------------------------------------

from services import diagnostics_service as _diag  # noqa: E402


def _diagnostics_snapshot() -> dict[str, object]:
    """Snapshot of registered persistent-view classes for ``!platform views``."""
    return {
        "registered_count": len(_REGISTRY),
        "subsystems": sorted(_REGISTRY.keys()),
    }


_diag.register("persistent_views", _diagnostics_snapshot)
