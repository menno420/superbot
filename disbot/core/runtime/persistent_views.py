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
    iter_registered_view_classes() — every registered class, in registration
                                     order (faithful; not deduped by subsystem)
    panel_id_of(cls)           — the manifest panel id for a class
    PersistentView             — base class to extend
"""

from __future__ import annotations

from typing import ClassVar

import discord

# Subsystem → class, used by restart recovery (one class per subsystem anchor).
_REGISTRY: dict[str, type[PersistentView]] = {}
# Registration-ordered list of *every* registered class — faithful even when two
# panels share a subsystem (the recovery dict above collapses those). The panel
# manifest (manifest spine PR2) enumerates this so both panels surface.
_REGISTERED_CLASSES: list[type[PersistentView]] = []


def register(cls: type[PersistentView]) -> type[PersistentView]:
    """Register a PersistentView subclass for restart recovery."""
    _REGISTRY[cls.SUBSYSTEM] = cls
    if cls not in _REGISTERED_CLASSES:
        _REGISTERED_CLASSES.append(cls)
    return cls


def get_view_class(subsystem: str) -> type[PersistentView] | None:
    """Return the registered PersistentView class for *subsystem*, or None."""
    return _REGISTRY.get(subsystem)


def iter_registered_view_classes() -> tuple[type[PersistentView], ...]:
    """Every registered persistent-view class, in registration order.

    Unlike :func:`get_view_class` this does **not** dedupe by subsystem, so a
    subsystem that owns more than one persistent panel (e.g. ``help``) yields
    all of them — the faithful enumeration the panel manifest needs.
    """
    return tuple(_REGISTERED_CLASSES)


def panel_id_of(cls: type[PersistentView]) -> str:
    """The manifest panel id for *cls* — its declared ``PANEL_ID`` or the
    ``SUBSYSTEM`` fallback (unique when a subsystem owns one panel).
    """
    return cls.PANEL_ID or cls.SUBSYSTEM


class PersistentView(discord.ui.View):
    """Base class for views that survive bot restarts.

    Stateless: callbacks receive all context via the ``interaction`` argument.
    Ownership: ``interaction_check`` queries the anchor table to verify the
    interacting user owns the panel.
    """

    SUBSYSTEM: ClassVar[str] = ""

    # Manifest spine (PR2): the stable id this panel is addressed by in the
    # PanelManifest / panel-layout editor. Empty ⇒ falls back to SUBSYSTEM
    # (unique when a subsystem owns exactly one persistent panel). Set it
    # explicitly only when a subsystem registers more than one panel (e.g.
    # the two ``help`` panels) so each gets a distinct manifest id.
    PANEL_ID: ClassVar[str] = ""

    # RC-3 / ADR-004: when the panel's anchor row is missing we cannot verify
    # ownership.  Default False keeps today's behavior (allow).  Opt in to True
    # ONLY for panels where a missing anchor could let a non-owner take a
    # privileged / owner-affecting action (admin/config, or guild mutations like
    # role management).  Stateless per-clicker panels (economy, mining, btd6,
    # help) stay False: every button acts on interaction.user.id, so a non-owner
    # click only touches their own data and the ownership check is cosmetic.
    FAIL_CLOSED_ON_MISSING_ANCHOR: ClassVar[bool] = False

    # Standard nav opt-out (mirrors views.base.BaseView). When the subsystem
    # has a parent_hub, a ↩ Back-to-hub button is auto-attached; a 📚 Help
    # button is auto-attached on every SUBSYSTEM panel. Set False to opt out.
    STANDARD_NAV: ClassVar[bool] = True

    def __init__(self) -> None:
        super().__init__(timeout=None)
        # Auto-attach the universal Help / Back-to-hub controls (owner directive
        # 2026-06-23). Function-local views import — core must not import views at
        # module scope; this mirrors the on_error → handle_view_error seam below.
        # The nav buttons carry stable custom_ids, so they satisfy the persistent
        # view contract and survive restart matching.
        from views.navigation import attach_standard_nav

        attach_standard_nav(self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Allow only the panel's owner to interact."""
        from core.runtime import message_anchor_manager

        if not interaction.message:
            return True

        # Ephemeral messages are private to the user who triggered them — Discord
        # guarantees nobody else can see or click them, so ownership is implicit
        # and there is no anchor row to verify against (ephemerals are never
        # anchored). Allow before the fail-closed branch: otherwise a
        # FAIL_CLOSED_ON_MISSING_ANCHOR panel surfaced through an ephemeral
        # help/nav path (e.g. /help → Roles, which renders RoleHubPanelView via
        # role_cog.build_help_menu_view) would deny its own opener with
        # "This panel can no longer be verified". A shared/public panel still
        # has no ephemeral flag, so its anchor check is unchanged.
        flags = getattr(interaction.message, "flags", None)
        if flags is not None and getattr(flags, "ephemeral", False):
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
