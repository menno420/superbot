"""Shared panel navigation helper — Phase 3.5.

Centralises the back-button + cross-panel transition logic that
previously lived inline in `help_cog._attach_back_to_help_button`,
`admin_cog.attach_back_to_admin_button`, `settings.subsystem_view.
attach_back_to_settings_button`, `games.hub.attach_back_to_games_button`,
and `LoggingRoutesView.btn_back`. Each of those re-implemented the
same three concerns:

1. The 25-component cap (Discord rejects views with >25 children).
2. A parent-builder call at click time — needed for governance-aware
   pagination, route-table refreshes, and resource re-resolution.
3. Defer → build → edit-in-place with consistent error handling so a
   parent-build failure surfaces as an ephemeral rather than a silent
   crash.

This module is intentionally small. It is **not** a UI framework — no
new view classes, no inheritance hierarchy, no decorator. Just two
functions and one type alias.

Phase 3.5 scope: ship the helper + migrate the safest call sites
(help cog's back injection + LoggingRoutesView back-to-logging).
Other duplicated factories (admin / settings / games) stay as-is
and migrate one PR at a time, on demand, when their owners are
already touched.

Cross-references — duplicated patterns in the codebase today:

* `disbot/cogs/help_cog.py:147-209` — back-to-help with governance
  re-resolve.
* `disbot/cogs/admin_cog.py:229-273` — back-to-admin (cog lookup +
  state mutation).
* `disbot/views/settings/subsystem_view.py:240-281` — back-to-settings
  with re-resolve.
* `disbot/views/games/hub.py:114-150` — back-to-games (no governance
  re-resolve; rebuilds from `SUBSYSTEMS`).
* `disbot/cogs/logging/routes_panel.py:btn_back` — back-to-logging.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias

import discord

from utils.subsystem_registry import SUBSYSTEMS

logger = logging.getLogger("bot.views.navigation")

# Canonical custom_ids for the two standard-nav controls auto-attached to every
# subsystem panel (the "never stranded" contract — owner directive 2026-06-23).
# Stable strings so they survive persistent-view restart matching and so the
# idempotency guard in :func:`attach_back_button` dedupes against any external
# back-pusher (Help / hub child openers) that targets the same destination.
NAV_HELP_ID = "nav:help"
NAV_HUB_ID_PREFIX = "nav:hub:"

# Public type alias: callers pass an async function that, given the
# current interaction, returns the parent panel's ``(embed, view)``
# pair. The function may re-resolve governance, refetch state, or
# walk pagination — Phase 3.5's helper neither cares nor knows.
ParentBuilder: TypeAlias = Callable[
    [discord.Interaction],
    Awaitable[tuple[discord.Embed, discord.ui.View]],
]


def help_nav_card(view: discord.ui.View | None) -> discord.File | None:
    """The optional image card a help-nav hub panel wants rendered.

    The visual card engine (H3) renders showpiece image cards for hubs opened by
    their **direct command** (the XP hub via ``!xpmenu``, ``!rank``, …). The same
    hub reached *through Help / hub navigation* goes through the
    ``build_help_menu_view`` hook, which is embed-only by contract across the
    codebase — so the showpiece disappears on exactly the discovery path Help is.

    This is the seam that closes that split **without** changing the return shape
    of all ~47 hooks: a hook that has a card sets it on the view it returns
    (``view.help_nav_card = card``); every help-nav render site forwards the
    result here as ``file=`` (fresh send) or ``attachments=`` (in-place edit —
    ``safe_edit`` already supports it, built for exactly this PIL-card-on-one-
    anchor case). A view without the attribute — every embed-only hub, the
    default — yields ``None`` → unchanged embed-only behaviour, so the seam rolls
    out hub-by-hub and any render site not yet wired keeps working.

    Defensive: a non-``discord.File`` value (or a missing attribute) → ``None``,
    never raises, so a stray attribute can't crash navigation.
    """
    card = getattr(view, "help_nav_card", None)
    return card if isinstance(card, discord.File) else None


def help_nav_attachments(view: discord.ui.View | None) -> list[discord.File]:
    """``attachments=`` value for an **in-place edit** that opens ``view``.

    ``[card]`` when the panel carries a help-nav card (sets it), else ``[]``
    (clears any prior screen's attachment so a card from the panel we navigated
    *away* from does not linger — the documented ``safe_edit`` convention). Fresh
    sends use :func:`help_nav_card` directly as ``file=``.
    """
    card = help_nav_card(view)
    return [card] if card is not None else []


def help_nav_send_kwargs(view: discord.ui.View | None) -> dict[str, discord.File]:
    """``**kwargs`` carrying ``file=`` for a **fresh send** that opens ``view``.

    ``{"file": card}`` when the panel has a help-nav card, else ``{}``. Used as
    ``await ctx.send(..., **help_nav_send_kwargs(view))`` /
    ``interaction.response.send_message(..., **help_nav_send_kwargs(view))`` so a
    cardless hub never passes ``file=None`` — ``InteractionResponse.send_message``
    treats ``None`` as a real (broken) attachment rather than "no file".
    """
    card = help_nav_card(view)
    return {"file": card} if card is not None else {}


@dataclass(frozen=True)
class BackTarget:
    """A captured "what comes above me" for back-chain composition (AB2).

    Each opener in a Help → X → Y chain can stash a ``BackTarget`` on
    the child it opens (typically as ``child_view._back_target``). The
    child's own opener, when it builds back-to-Y, uses
    :func:`chain_back` to compose: pressing back rebuilds Y AND
    re-attaches the captured ``BackTarget`` on the rebuilt Y. This
    lets a deep navigation unwind all the way back to Help with each
    intermediate parent's back button still attached, without inventing
    a router or a stack.

    Persistent-view fail-safe: ``BackTarget`` MUST NOT be persisted
    across bot restarts (the ``builder`` closure cannot be
    serialized). Persistent-view re-registration must construct views
    without a ``_back_target``; in that case the panel still works
    as the top-of-stack and click-time governance recheck (PR D) is
    the correctness safety net.
    """

    builder: ParentBuilder
    label: str
    custom_id: str


# Discord's per-view component cap. Pulled out as a constant so tests
# don't hard-code the magic number.
MAX_COMPONENTS = 25


def attach_back_button(
    view: discord.ui.View,
    *,
    label: str,
    custom_id: str,
    parent_builder: ParentBuilder,
    row: int = 4,
    style: discord.ButtonStyle = discord.ButtonStyle.secondary,
    error_message: str = "Couldn't load the parent panel — see bot logs.",
) -> bool:
    """Append a Back button to ``view``.

    Args:
        view: the live view instance to mutate.
        label: button label (e.g. ``"↩ Back to Help"``).
        custom_id: stable Discord custom_id (kept distinct per parent so
            multiple back buttons don't collide on the same view).
        parent_builder: async function that, when called at click time,
            returns the parent panel's ``(embed, view)`` pair. The
            function receives the click-time ``Interaction`` so it can
            inspect ``interaction.guild`` / ``.user`` and re-resolve
            anything that changed since the view was rendered.
        row: Discord row index for the button (default 4 — bottom row).
        style: Discord button style (default secondary).
        error_message: ephemeral text surfaced if ``parent_builder``
            raises. Defaults to a generic operator-facing message.

    Returns:
        ``True`` if the button was added. ``False`` if the view is
        already at Discord's 25-component cap; a WARNING is logged in
        that case so operators can see why a panel lost its back nav.

    Failure handling: if ``parent_builder`` raises at click time, the
    exception is logged with ``exc_info=True`` and the user receives an
    ephemeral fallback. The original message is NOT edited (preserving
    whatever the user was looking at).

    The callback defers before invoking ``parent_builder`` so slow
    rebuilds do not exhaust Discord's initial response window.
    """
    # Idempotency guard: a button with this custom_id is already present (e.g.
    # the standard Help/Back-to-hub auto-attach ran in __init__, then a Help or
    # hub child-opener tried to push the same destination). Skip silently so the
    # panel never shows a duplicate back control. This is what lets the universal
    # auto-attach (attach_standard_nav) coexist with the legacy external pushers.
    if any(getattr(child, "custom_id", None) == custom_id for child in view.children):
        return True

    if len(view.children) >= MAX_COMPONENTS:
        logger.warning(
            "navigation.attach_back_button: %s already has %d children — "
            "%r button skipped. User cannot return from this panel.",
            type(view).__name__,
            len(view.children),
            label,
        )
        return False

    btn = discord.ui.Button(  # type: ignore[var-annotated]
        label=label,
        custom_id=custom_id,
        style=style,
        row=row,
    )

    async def _back_callback(interaction: discord.Interaction) -> None:
        from core.runtime.interaction_helpers import safe_defer, safe_edit

        if not await safe_defer(interaction):
            return
        try:
            embed, parent_view = await parent_builder(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash
            logger.warning(
                "navigation back-button: parent_builder failed (custom_id=%r): %s",
                custom_id,
                exc,
                exc_info=True,
            )
            try:
                await interaction.followup.send(error_message, ephemeral=True)
            except Exception as send_exc:  # noqa: BLE001 — log + swallow
                logger.warning(
                    "navigation back-button: ephemeral fallback also failed: %s",
                    send_exc,
                )
            return
        await safe_edit(
            interaction,
            embed=embed,
            view=parent_view,
            attachments=help_nav_attachments(parent_view),
        )

    btn.callback = _back_callback  # type: ignore[method-assign]
    try:
        view.add_item(btn)
    except ValueError:
        # Discord rejects a row that already holds 5 components. A panel that
        # packs its bottom row full can't take a back button there — log and
        # skip rather than crash the whole panel build.
        logger.warning(
            "navigation.attach_back_button: %s row %d is full — %r button skipped.",
            type(view).__name__,
            row,
            label,
        )
        return False

    # Record a re-attach closure so a panel that REDRAWS onto a fresh view
    # instance (the ``edit_in_place`` idiom — e.g. farm Collect → ``FarmMenuView()``)
    # can carry this externally-attached back button forward via :func:`carry_back`.
    # Without it, the Back-to-[hub] / Back-to-Help button vanishes on the next
    # action because it lived on the *original* instance (the games/admin panel
    # back-loss class).
    reattachers = getattr(view, "_back_reattachers", None)
    if reattachers is None:
        reattachers = []
        view._back_reattachers = reattachers  # type: ignore[attr-defined]
    reattachers.append(
        lambda v: attach_back_button(
            v,
            label=label,
            custom_id=custom_id,
            parent_builder=parent_builder,
            row=row,
            style=style,
            error_message=error_message,
        ),
    )
    return True


def carry_back(old_view: discord.ui.View, new_view: discord.ui.View) -> None:
    """Re-attach to ``new_view`` every back button that was attached to ``old_view``.

    The fix for the games/admin panel back-loss class: a panel that redraws onto a
    **fresh view instance** on an action (the ``edit_in_place`` idiom) drops the
    Back-to-[hub] / Back-to-Help button the hub attached to the *original* instance.
    Call ``carry_back(self, new_view)`` immediately before ``edit_message`` so the
    navigation survives the redraw. No-op when ``old_view`` carries no recorded back.
    """
    for reattach in getattr(old_view, "_back_reattachers", ()):  # type: ignore[attr-defined]
        try:
            reattach(new_view)
        except Exception:  # noqa: BLE001 — a failed carry must never crash a redraw
            logger.warning(
                "navigation.carry_back: a back re-attacher failed",
                exc_info=True,
            )
    target = getattr(old_view, "_back_target", None)
    if target is not None and getattr(new_view, "_back_target", None) is None:
        new_view._back_target = target  # type: ignore[attr-defined]


async def _open_help_home(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, discord.ui.View]:
    """Click-time builder for the universal Help button → the Help home menu.

    Function-local cogs import (the ``hub_children`` house idiom): the views
    layer must not import ``cogs`` at module scope, but a click-time closure
    resolving the Help home is the established seam. Rebuilds the governance
    projection so Home reflects live visibility, never the open-time snapshot.
    """
    from cogs.help.panels import HelpCategoryView  # noqa: PLC0415
    from cogs.help_cog import (  # noqa: PLC0415 — views→cogs click-time seam
        _resolve_projection,
        build_categories_overview_embed,
    )
    from services.governance_service import GovernanceContext  # noqa: PLC0415

    gctx = GovernanceContext.from_interaction(interaction)
    projection = await _resolve_projection(gctx)
    embed = build_categories_overview_embed(projection=projection)
    return embed, HelpCategoryView(projection=projection)


def _make_hub_opener(hub_key: str) -> ParentBuilder:
    """Return a click-time builder that rebuilds the ``hub_key`` mother hub.

    Resolves the hub's cog via the runtime client and calls its
    ``build_help_menu_view`` hook — the same universal hub-rebuild seam
    :class:`views.hub_children.HubChildButton` uses, so a Back-to-hub button
    re-renders the live, governance-filtered hub panel.
    """

    async def _open(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        from cogs.help_cog import _cog_for_subsystem  # noqa: PLC0415

        cog = _cog_for_subsystem(interaction.client, hub_key)  # type: ignore[arg-type]
        builder = getattr(cog, "build_help_menu_view", None) if cog else None
        if not callable(builder):
            raise RuntimeError(f"hub {hub_key!r} has no build_help_menu_view")
        return await builder(interaction)

    return _open


def has_standard_nav(view: discord.ui.View) -> bool:
    """True when ``view`` already carries a standard-nav control.

    Used by the legacy external back-pushers (Help's Back-to-Help, the hub
    child openers) to skip their push when :func:`attach_standard_nav` already
    gave the panel its Help / Back-to-hub buttons — preventing duplicate
    controls without either side knowing about the other.
    """
    for child in view.children:
        cid = getattr(child, "custom_id", None) or ""
        if cid == NAV_HELP_ID or cid.startswith(NAV_HUB_ID_PREFIX):
            return True
    return False


def _self_navigates(view: discord.ui.View) -> bool:
    """True when ``view`` already provides its own hub/help/**parent** navigation.

    The mother-hub and operator panels (admin, utility, settings, …) define
    their own ``📚 Help`` / ``↩ Back to <hub>`` buttons as decorated
    components, so they keep that nav across redraws on their own and must NOT
    receive a duplicate from :func:`attach_standard_nav`. The panels that
    genuinely lose nav (the leaf panels — farm, mining, the game panels, the
    AI/channel/ux_lab panels) have *no* parent-nav button of their own and
    relied on an externally-attached back; those are exactly the ones that get
    auto-nav.

    An ``↩ Overview`` button does **not** count: it is a *self-refresh*
    (re-renders the same panel in place), not navigation to a parent, so a
    panel whose only nav-shaped control is Overview is genuinely stranded and
    must still receive auto-nav. Treating "overview" as self-navigation was the
    bug that stranded ``LoggingPanelView`` / ``EconomyPanelView``: they declare
    a ``SUBSYSTEM`` (so the ``back_button`` linter assumes auto-nav covers
    them) yet opted themselves *out* of it here, leaving only a fragile
    externally-attached back that vanished on the first redraw.

    Detection is label-based (the codebase uses stable ``Help`` / ``Back to``
    button copy) plus the canonical nav custom_ids. Heuristic — if a future
    panel's button copy diverges this may misfire; revisit if a
    self-navigating panel ever shows a duplicate or a leaf panel stays
    stranded.
    """
    for child in view.children:
        cid = getattr(child, "custom_id", None) or ""
        if cid == NAV_HELP_ID or cid.startswith(NAV_HUB_ID_PREFIX):
            return True
        label = (getattr(child, "label", None) or "").lower()
        # "overview" is deliberately absent — it is a self-refresh, not
        # parent-nav (the LoggingPanelView / EconomyPanelView stranding class).
        if "help" in label or "back to" in label:
            return True
    return False


def attach_standard_nav(view: discord.ui.View) -> None:
    """Auto-attach the universal Help (+ Back-to-hub) controls to a panel.

    The "never stranded" mechanism (owner directive 2026-06-23): every panel
    that declares a ``SUBSYSTEM`` gets, on construction, a **📚 Help** button
    (opens the Help home) and — when the subsystem has a ``parent_hub`` — a
    **↩ <hub>** button (rebuilds its mother hub). Because this runs in the base
    view ``__init__``, the controls reappear on every redraw onto a fresh view
    instance (the ``edit_in_place`` idiom that previously dropped them), and any
    panel reachable by *any* command stays one click from Help and its hub.

    Idempotent (via :func:`attach_back_button`'s custom_id guard) and a no-op
    for views without a ``SUBSYSTEM`` (confirmations, transient sub-views) or
    with ``STANDARD_NAV = False``. Best-effort: never raises into a constructor.
    """
    subsystem = getattr(view, "SUBSYSTEM", "") or ""
    if not subsystem or not getattr(view, "STANDARD_NAV", True):
        return
    meta = SUBSYSTEMS.get(subsystem)
    if meta is None:
        return
    # A panel that already defines its own Help / Overview / Back-to-hub nav
    # keeps it across redraws on its own — don't duplicate it. Auto-nav exists
    # for the leaf panels that have no nav of their own.
    if _self_navigates(view):
        return
    try:
        # The Help button is universal — except on the Help menu itself, which
        # would otherwise link to its own home.
        if subsystem != "help":
            attach_back_button(
                view,
                label="📚 Help",
                custom_id=NAV_HELP_ID,
                parent_builder=_open_help_home,
                row=4,
                error_message="Could not load the Help menu. Please try again.",
            )
        parent_hub = meta.get("parent_hub")
        if parent_hub:
            hub_meta = SUBSYSTEMS.get(parent_hub) or {}
            hub_name = hub_meta.get("display_name", parent_hub)
            attach_back_button(
                view,
                label=f"↩ {hub_name}",
                custom_id=f"{NAV_HUB_ID_PREFIX}{parent_hub}",
                parent_builder=_make_hub_opener(parent_hub),
                row=4,
                error_message=f"Could not reload {hub_name}. Please try again.",
            )
    except Exception:  # noqa: BLE001 — nav attach must never break a panel ctor
        logger.warning(
            "navigation.attach_standard_nav: failed for subsystem %r",
            subsystem,
            exc_info=True,
        )


async def transition_to(
    interaction: discord.Interaction,
    *,
    builder: ParentBuilder,
    error_message: str = "Couldn't open that panel — see bot logs.",
) -> None:
    """Defer the interaction, build a new ``(embed, view)``, and edit
    the message in place.

    Used by buttons that already exist on a view (via ``@discord.ui.button``
    or runtime construction) when their callback needs to swap to a
    sibling or parent panel. For Back buttons constructed *by this
    helper*, prefer :func:`attach_back_button` which builds the same
    flow into the button itself.

    Failure handling mirrors :func:`attach_back_button`: builder
    exceptions are logged with ``exc_info=True`` and surface as an
    ephemeral; the original message is left untouched.
    """
    from core.runtime.interaction_helpers import safe_defer, safe_edit

    if not await safe_defer(interaction):
        return
    try:
        embed, view = await builder(interaction)
    except Exception as exc:  # noqa: BLE001 — navigation must not crash
        logger.warning(
            "navigation.transition_to: builder failed: %s",
            exc,
            exc_info=True,
        )
        try:
            await interaction.followup.send(error_message, ephemeral=True)
        except Exception as send_exc:  # noqa: BLE001 — log + swallow
            logger.warning(
                "navigation.transition_to: followup also failed: %s",
                send_exc,
            )
        return
    await safe_edit(
        interaction,
        embed=embed,
        view=view,
        attachments=help_nav_attachments(view),
    )


def attach_back_target(view: discord.ui.View, target: BackTarget) -> bool:
    """Convenience: :func:`attach_back_button` driven by a :class:`BackTarget`.

    Equivalent to::

        attach_back_button(
            view,
            label=target.label,
            custom_id=target.custom_id,
            parent_builder=target.builder,
        )

    Also sets ``view._back_target = target`` when the button is added so
    that views rebuilt via :func:`chain_back` can propagate the back chain
    to their own children on subsequent navigation (e.g. Games hub rebuilt
    by Back-to-Games still exposes ``_back_target`` so Blackjack can add
    "Back to Help").

    Returns the same value as :func:`attach_back_button` — ``True`` if
    the button was added, ``False`` if the view was at the 25-component
    cap.
    """
    result = attach_back_button(
        view,
        label=target.label,
        custom_id=target.custom_id,
        parent_builder=target.builder,
    )
    if result:
        view._back_target = target  # type: ignore[attr-defined]
    return result


def chain_back(
    builder: ParentBuilder,
    grandparent: BackTarget | None,
) -> ParentBuilder:
    """Return a wrapped builder that re-attaches ``grandparent`` after rebuild.

    Composition rule: the wrapped builder calls ``builder`` to obtain
    ``(embed, view)``, then — if ``grandparent`` is not ``None`` —
    invokes :func:`attach_back_target` on the rebuilt view. The
    grandparent itself may be a :class:`BackTarget` whose builder was
    also produced by :func:`chain_back`, so arbitrary depth composes
    naturally through the closure tree.

    If ``grandparent`` is ``None`` this is the identity transform —
    the builder is returned unchanged. That keeps top-of-stack openers
    (direct ``!cleanup``, ``!economymenu``) from gaining an unwanted
    spurious back button.

    Persistent-view fail-safe: the wrapped builder is in-memory only.
    Persistent views must re-register without a chain; click-time
    checks remain the correctness safety net.
    """
    if grandparent is None:
        return builder

    async def _chained_builder(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        embed, view = await builder(interaction)
        attach_back_target(view, grandparent)
        return embed, view

    return _chained_builder


__all__ = [
    "MAX_COMPONENTS",
    "NAV_HELP_ID",
    "NAV_HUB_ID_PREFIX",
    "BackTarget",
    "ParentBuilder",
    "attach_back_button",
    "attach_back_target",
    "attach_standard_nav",
    "carry_back",
    "chain_back",
    "has_standard_nav",
    "help_nav_attachments",
    "help_nav_card",
    "help_nav_send_kwargs",
    "transition_to",
]
