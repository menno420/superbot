"""Community hub view (S9).

The Community subsystem is a router-only hub with no business logic
of its own. Per the mother-hub map, it groups progression and
community-activity subsystems whose primary owners are spread across
the codebase:

* **XP** and **Roles** are the primary children. Discovered from
  ``SUBSYSTEMS`` where ``parent_hub == "community"``.
* **Counting**, **Chain**, and **Leaderboard** appear as **cross-links**
  — their primary homes stay under Games (counting/chain) and Economy
  (leaderboard). Discovered from
  ``utils.hub_registry.get_hub("community").cross_link_children``.

Mirrors the Games hub pattern (``views.games.hub:discover_game_children``)
so the source of truth is the registry, not a hardcoded view-local
tuple. PR #4 migrated the view here from the previous ``_HUB_CHILDREN``
literal.

Layout: primary children fill rows from 0 (5 per row — Discord's row
cap) with primary style; cross-links continue on the next free row with
secondary style (so the grid wraps gracefully as the hub grows past five
primaries). Back-nav is attached by ``HelpCategoryView`` when
the hub is surfaced from ``!help``; the direct ``!community`` entry
shows the hub without a back button, matching the ``!games`` pattern.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from services import governance_service
from services.governance_service import GovernanceContext
from utils.hub_registry import get_hub
from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import GENERAL_COLOR
from views.base import HubView
from views.hub_children import HubChildButton, discover_hub_children
from views.navigation import (
    BackTarget,
    attach_back_button,
    chain_back,
)

logger = logging.getLogger("bot.views.community")

# Discord allows at most 5 buttons per action row.
_BUTTONS_PER_ROW = 5


def discover_community_children() -> tuple[
    list[tuple[str, dict]], list[tuple[str, dict]]
]:
    """Return ``(primary, cross_link)`` lists of (subsystem, meta) pairs.

    Primary children come from ``SUBSYSTEMS`` filtered by
    ``parent_hub == "community"``, sorted by ``ui_priority`` then key
    for determinism (matches the Games hub ordering rule).

    Cross-link children come from
    ``hub_registry.get_hub("community").cross_link_children`` in
    declared order. Unknown / missing subsystem keys are dropped with
    a WARNING — the hub stays functional even if a cross-link points
    at a subsystem that was unloaded.
    """
    primary = discover_hub_children("community")

    cross_link: list[tuple[str, dict]] = []
    hub = get_hub("community")
    if hub is not None:
        for key in hub.cross_link_children:
            meta = SUBSYSTEMS.get(key)
            if meta is None:
                logger.warning(
                    "community hub cross_link_children %r is not in SUBSYSTEMS",
                    key,
                )
                continue
            cross_link.append((key, dict(meta)))

    return primary, cross_link


def _format_child_label(subsystem: str, meta: dict) -> str:
    """Build a button label from registry metadata.

    Mirrors the Games hub which uses
    ``meta.get("display_name") or name`` plus the subsystem emoji.
    """
    emoji = meta.get("emoji") or "•"
    display = meta.get("display_name") or subsystem
    return f"{emoji} {display}"


def build_community_hub_embed(
    primary: list[tuple[str, dict]] | None = None,
    cross_link: list[tuple[str, dict]] | None = None,
) -> discord.Embed:
    """Build the embed shown by :class:`CommunityHubView`.

    Description is generated from the discovered children so it stays
    in sync with the registry. The "Progression" / "Community games &
    standings" group headings are hardcoded — they are presentational
    framing, not metadata.

    PR D: when ``primary`` and ``cross_link`` are supplied (typically
    pre-filtered by :func:`build_community_hub_panel`), the embed only
    describes those subsystems. When either is ``None``, falls back to
    unfiltered discovery — used by callers that construct the view
    directly (tests, persistent re-registration).
    """
    if primary is None or cross_link is None:
        primary, cross_link = discover_community_children()
    parts = ["Pick a community feature below."]

    if primary:
        parts.append("\n**Progression**")
        for name, meta in primary:
            emoji = meta.get("emoji") or "•"
            display = meta.get("display_name") or name
            desc = meta.get("description") or ""
            parts.append(f"• {emoji} **{display}** — {desc}".rstrip(" —"))

    if cross_link:
        parts.append("\n**Community games & standings**")
        for name, meta in cross_link:
            emoji = meta.get("emoji") or "•"
            display = meta.get("display_name") or name
            desc = meta.get("description") or ""
            parts.append(f"• {emoji} **{display}** — {desc}".rstrip(" —"))

    embed = discord.Embed(
        title="🌱 Community Hub",
        description="\n".join(parts),
        color=GENERAL_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


async def build_community_hub_panel(
    author: discord.Member | discord.User,
    *,
    interaction: discord.Interaction | None = None,
    ctx: commands.Context | None = None,
    visible: set[str] | None = None,
) -> tuple[discord.Embed, CommunityHubView]:
    """Resolve governance, filter children, and build the hub panel.

    Single source of truth for opening the Community hub. Callers:

    * ``!community`` prefix command → pass ``ctx``.
    * ``CommunityCog.build_help_menu_view`` (help hook) → pass ``interaction``.
    * Back-to-Community closure rebuilds → pass ``interaction``.

    When ``visible`` is supplied the caller has already resolved
    visibility and we skip the re-resolution. Otherwise the factory
    builds a :class:`GovernanceContext` from whichever of
    ``interaction`` / ``ctx`` was provided and calls
    ``governance_service.resolve_visibility``.

    Both primary and cross-link children are filtered through the
    visible set. Cross-links that point at a hidden subsystem are
    dropped silently — operators see them again as soon as the
    subsystem becomes visible.
    """
    if visible is None:
        if interaction is not None:
            gctx = GovernanceContext.from_interaction(interaction)
        elif ctx is not None:
            gctx = GovernanceContext.from_ctx(ctx)
        else:
            raise ValueError(
                "build_community_hub_panel requires interaction or ctx "
                "when visible is not pre-resolved",
            )
        result = await governance_service.resolve_visibility(gctx)
        visible = result.visible_subsystems

    primary, cross_link = discover_community_children()
    primary = [(name, meta) for name, meta in primary if name in visible]
    cross_link = [(name, meta) for name, meta in cross_link if name in visible]

    embed = build_community_hub_embed(primary, cross_link)
    view = CommunityHubView(author, primary=primary, cross_link=cross_link)
    return embed, view


def attach_back_to_community_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
    *,
    grandparent: BackTarget | None = None,
) -> bool:
    """Append a "↩ Back to Community" control to a child view.

    Mirrors :func:`disbot.views.games.hub.attach_back_to_games_button`.
    The parent-builder closure routes through
    :func:`build_community_hub_panel` so the rebuilt hub is filtered
    through governance at click time.

    When ``grandparent`` is supplied (AB2 — e.g. a Back-to-Help target),
    :func:`chain_back` wraps the builder so the rebuilt Community hub also
    re-attaches the grandparent's back button. Without this the user lost
    "↩ Back to Help" the moment they stepped into a Community child and back
    (the asymmetry the Games hub already fixed).
    """

    async def _build_community_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        return await build_community_hub_panel(author, interaction=interaction)

    builder = chain_back(_build_community_parent, grandparent)

    return attach_back_button(
        view,
        label="↩ Back to Community",
        custom_id="community:back",
        parent_builder=builder,
        row=4,
        style=discord.ButtonStyle.secondary,
        error_message="Could not reload the Community hub. Please try again.",
    )


class _CommunityChildButton(HubChildButton):
    """A button on the Community hub that opens a child cog's panel in place.

    Thin subclass of the shared :class:`views.hub_children.HubChildButton` (the
    consolidation's "first consolidation"): it binds the Community ``hub_key`` +
    the Back-to-Community attacher, and inherits all the forwarding logic
    (click-time governance recheck → ``build_help_menu_view`` → back-nav → edit
    in place). Community fails closed with an ephemeral when a child has no panel
    (no ``fallback_builder``).
    """

    def __init__(
        self,
        *,
        subsystem: str,
        label: str,
        style: discord.ButtonStyle,
        row: int,
    ) -> None:
        super().__init__(
            hub_key="community",
            subsystem=subsystem,
            label=label,
            style=style,
            row=row,
            back_attacher=attach_back_to_community_button,
        )


class CommunityHubView(HubView):
    """Router-only hub for the Community subsystem.

    Discovers primary children from ``SUBSYSTEMS`` (``parent_hub ==
    "community"``) and cross-links from ``hub_registry.get_hub
    ("community").cross_link_children``. Every button forwards to the
    target cog's existing ``build_help_menu_view`` hook — no business
    logic lives in this view.
    """

    SUBSYSTEM = "community"

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        primary: list[tuple[str, dict]] | None = None,
        cross_link: list[tuple[str, dict]] | None = None,
    ) -> None:
        super().__init__(author)
        # PR D: ``primary`` and ``cross_link`` are normally pre-filtered
        # by :func:`build_community_hub_panel` so only
        # governance-visible subsystems render. Either being ``None``
        # falls back to unfiltered discovery — used by tests and any
        # caller that constructs the view directly. Click-time recheck
        # in :class:`_CommunityChildButton.callback` still gates
        # correctly even on the unfiltered path.
        if primary is None or cross_link is None:
            primary, cross_link = discover_community_children()
        # Discord caps a button row at 5. Primary children fill rows from 0
        # (primary style); cross-links continue on the next free row after the
        # last primary row (secondary style). This wraps gracefully as the hub
        # grows past 5 primaries instead of overflowing a single row.
        for idx, (subsystem, meta) in enumerate(primary):
            self.add_item(
                _CommunityChildButton(
                    subsystem=subsystem,
                    label=_format_child_label(subsystem, meta),
                    style=discord.ButtonStyle.primary,
                    row=idx // _BUTTONS_PER_ROW,
                ),
            )
        primary_rows = -(-len(primary) // _BUTTONS_PER_ROW)  # ceil division
        for idx, (subsystem, meta) in enumerate(cross_link):
            self.add_item(
                _CommunityChildButton(
                    subsystem=subsystem,
                    label=_format_child_label(subsystem, meta),
                    style=discord.ButtonStyle.secondary,
                    row=primary_rows + idx // _BUTTONS_PER_ROW,
                ),
            )


__all__ = [
    "CommunityHubView",
    "attach_back_to_community_button",
    "build_community_hub_embed",
    "build_community_hub_panel",
    "discover_community_children",
]
