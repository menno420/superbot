"""Shared hub child-discovery primitive.

A *mother hub* (Games, Community, Utility, …) surfaces the subsystems that
declare ``parent_hub == <hub key>`` as child buttons on its panel.  Before this
module each hub re-implemented the same "filter ``SUBSYSTEMS`` by ``parent_hub``,
sort deterministically" discovery by hand (``views.games.hub.discover_game_children``,
``views.community.hub.discover_community_children``,
``cogs.utility_cog.discover_utility_children``).  Three copies meant a hub could
silently drift — the exact class behind the *discoverability audit* general-cog
bug, where the Utility panel rendered none of its children.

This is the **one** discovery seam every hub now delegates to, and (since the
"first consolidation") the **one** child-forwarding button seam too:
:class:`HubChildButton` holds the shared open-child-in-place logic (click-time
governance recheck → resolve the child cog → ``build_help_menu_view`` →
back-nav → edit in place), parametrized by ``hub_key`` (custom_id), a per-hub
``back_attacher``, and an optional ``fallback_builder``.  The per-hub button
classes (``_CommunityChildButton`` / ``_UtilityChildButton`` / the Games button)
are thin subclasses that bind those parameters — one source, several consumers,
the centralization the consolidation/ultracode fleet converges on
(``docs/planning/consolidation-fleet-plan-2026-06-23.md``).

:func:`discover_hub_children` is pure (no Discord objects, no I/O) — a
deterministic read of the registry, safe to call at view-construction time.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping

import discord

from services import governance_service
from services.governance_service import GovernanceContext
from utils.subsystem_registry import SUBSYSTEMS
from views.navigation import (
    BackTarget,
    attach_back_target,
    has_standard_nav,
    help_nav_attachments,
)

logger = logging.getLogger("bot.views.hub_children")

# A per-hub back-button attacher: ``(child_view, author, *, grandparent) -> bool``
# (e.g. ``attach_back_to_community_button``).  Kept as a parameter so the shared
# button never imports a specific hub module (no import cycle).
BackAttacher = Callable[..., bool]
# Builds the in-place fallback embed when a child has no panel
# (``(subsystem, meta) -> discord.Embed``); ``None`` → fail with an ephemeral.
FallbackBuilder = Callable[[str, dict], discord.Embed]

__all__ = ["HubChildButton", "discover_hub_children"]


def discover_hub_children(
    hub_key: str,
    *,
    group_order: Mapping[str, int] | None = None,
) -> list[tuple[str, dict]]:
    """Return the registry children of ``hub_key`` in deterministic UI order.

    A *child* is any ``SUBSYSTEMS`` entry whose ``parent_hub`` equals
    ``hub_key``.  Each result is ``(subsystem_key, dict(meta))`` — the meta is
    copied so callers can mutate it freely.

    Ordering is fully deterministic so the rendered button order is stable:

    * when ``group_order`` is given (the Games hub passes its
      ``hub_group`` → rank map), entries sort by **group rank first**, then
      ``ui_priority``, then key — competitive games before activities, etc.;
    * otherwise (Community / Utility and every future hub) entries sort by
      ``ui_priority`` then key.

    Unknown ``hub_group`` values rank last (99); missing ``ui_priority`` ranks
    last (99).  Mirrors the three hand-rolled copies this replaces exactly, so
    their existing tests pin the behaviour.
    """
    children = [
        (name, dict(meta))
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == hub_key
    ]
    if group_order is None:
        children.sort(key=lambda item: (item[1].get("ui_priority", 99), item[0]))
    else:
        children.sort(
            key=lambda item: (
                group_order.get(item[1].get("hub_group") or "", 99),
                item[1].get("ui_priority", 99),
                item[0],
            ),
        )
    return children


class HubChildButton(discord.ui.Button):
    """A mother-hub button that opens a child subsystem's panel in place.

    The shared child-forwarding button every hub uses (the consolidation's
    "first consolidation"). On click it: rechecks governance, resolves the child
    cog, calls its ``build_help_menu_view`` hook, attaches the hub's Back-nav
    (threading any Back-to-Help grandparent the hub carries), and edits the
    message in place.

    Bind a hub by subclassing — the per-hub button stays a thin shell::

        class _CommunityChildButton(HubChildButton):
            def __init__(self, *, subsystem, label, style, row):
                super().__init__(
                    hub_key="community", subsystem=subsystem, label=label,
                    style=style, row=row,
                    back_attacher=attach_back_to_community_button,
                )

    ``custom_id`` is ``f"{hub_key}:open:{subsystem}"`` — stable so persistent
    anchors keep routing. ``fallback_builder`` (optional) edits a graceful
    in-place embed when the child has no panel — the Games hub's behaviour;
    community / utility pass ``None`` and fail closed with an ephemeral instead.
    """

    def __init__(
        self,
        *,
        hub_key: str,
        subsystem: str,
        label: str,
        style: discord.ButtonStyle,
        row: int,
        back_attacher: BackAttacher,
        fallback_builder: FallbackBuilder | None = None,
    ) -> None:
        super().__init__(
            label=label,
            style=style,
            custom_id=f"{hub_key}:open:{subsystem}",
            row=row,
        )
        self._subsystem = subsystem
        self._back_attacher = back_attacher
        self._fallback_builder = fallback_builder

    async def _no_panel(self, interaction: discord.Interaction, message: str) -> None:
        """Handle a child with no panel — in-place fallback embed or ephemeral.

        ``fallback_builder`` set (Games) → edit the hub message to a graceful
        "no panel" embed; otherwise (community / utility) fail closed with an
        ephemeral, leaving the hub untouched.
        """
        if self._fallback_builder is not None:
            meta = dict(SUBSYSTEMS.get(self._subsystem) or {})
            await interaction.response.edit_message(
                embed=self._fallback_builder(self._subsystem, meta),
                view=self.view,
            )
        else:
            await interaction.response.send_message(message, ephemeral=True)

    async def callback(self, interaction: discord.Interaction) -> None:
        # Click-time governance recheck: a child that became invisible since
        # render fails closed with an ephemeral (resolve is cached → ~free).
        gctx = GovernanceContext.from_interaction(interaction)
        vis_result = await governance_service.resolve_visibility(gctx)
        if self._subsystem not in vis_result.visible_subsystems:
            await interaction.response.send_message(
                "That feature is no longer available in this channel.",
                ephemeral=True,
            )
            return

        # Local import keeps the help cog out of module-import time (a
        # module-level views→cogs import is a layer violation; this is the
        # existing house idiom the per-hub buttons already used).
        from cogs.help_cog import _cog_for_subsystem

        cog = _cog_for_subsystem(interaction.client, self._subsystem)  # type: ignore[arg-type]
        if cog is None:
            await self._no_panel(
                interaction,
                f"The {self._subsystem!r} subsystem is not loaded right now.",
            )
            return

        build_panel = getattr(cog, "build_help_menu_view", None)
        if not callable(build_panel):
            await self._no_panel(
                interaction,
                f"The {self._subsystem!r} subsystem has no panel yet.",
            )
            return

        try:
            embed, sub_view = await build_panel(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash
            logger.warning(
                "HubChildButton: build_help_menu_view failed for %r: %s",
                self._subsystem,
                exc,
                exc_info=True,
            )
            await self._no_panel(
                interaction,
                f"Could not open the {self._subsystem!r} panel — see bot logs.",
            )
            return

        # Attach the hub's Back button to the child view, threading any
        # Back-to-Help grandparent the hub carries so a Help → hub → child → back
        # round-trip keeps Back-to-Help. Skipped when the child already carries
        # standard nav (attach_standard_nav ran in its __init__ — a SUBSYSTEM
        # panel): it already has its own ↩ Back-to-hub + 📚 Help, so pushing the
        # hub's external back here would only duplicate it.
        if not has_standard_nav(sub_view):
            back_target: BackTarget | None = getattr(self.view, "_back_target", None)
            self._back_attacher(sub_view, interaction.user, grandparent=back_target)
            if back_target is not None:
                attach_back_target(sub_view, back_target)
            sub_view._back_target = back_target  # type: ignore[attr-defined]

        await interaction.response.edit_message(
            embed=embed,
            view=sub_view,
            attachments=help_nav_attachments(sub_view),
        )
