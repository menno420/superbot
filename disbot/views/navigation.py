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

logger = logging.getLogger("bot.views.navigation")

# Public type alias: callers pass an async function that, given the
# current interaction, returns the parent panel's ``(embed, view)``
# pair. The function may re-resolve governance, refetch state, or
# walk pagination — Phase 3.5's helper neither cares nor knows.
ParentBuilder: TypeAlias = Callable[
    [discord.Interaction],
    Awaitable[tuple[discord.Embed, discord.ui.View]],
]


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
        await safe_edit(interaction, embed=embed, view=parent_view)

    btn.callback = _back_callback  # type: ignore[method-assign]
    view.add_item(btn)

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
    await safe_edit(interaction, embed=embed, view=view)


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
    "BackTarget",
    "ParentBuilder",
    "attach_back_button",
    "attach_back_target",
    "chain_back",
    "transition_to",
]
