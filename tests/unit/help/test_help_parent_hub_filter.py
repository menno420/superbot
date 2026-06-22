"""Tests — Help menu hides ``parent_hub`` children at the top level.

Subsystems with a ``parent_hub`` (Blackjack, Mining, XP, Settings, …) are
hidden from the top-level Help category index — they remain
typed-accessible and reachable through their parent hub's panel.

These tests assert:

* The category index (``HelpCategoryView`` via
  ``resolve_help_panel_state``) lists only mother hubs, never their
  children. The Games hub *itself* still appears.
* The typed ``!help blackjack`` lookup still resolves to the subsystem —
  the filter only affects the category index, not the typed lookup.
* The ``parent_hub`` metadata assignments are pinned so a metadata edit
  cannot silently break the hub discovery contract.

(The legacy paginated "All Commands / Advanced" browser was removed in
PR #1294, so its `_build_page_embed` / `HelpPanelView` pins are gone.)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs import help_cog
from utils.subsystem_registry import SUBSYSTEMS


def _hub_children() -> list[str]:
    """Subsystems with any ``parent_hub`` set.

    Pre-PR-#3 this was only games children (6 entries). PR #3 added
    parent_hub on inventory, leaderboard, xp, role, cleanup, logging,
    proof_channel, and general — so this filter now expands to cover
    every subsystem expected to be hidden from the top-level overview.
    The existing per-test loops naturally extend to the larger set.
    """
    return [
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub")
    ]


def _all_visible_set() -> set[str]:
    """Visible set covering every subsystem — governance allows everything."""
    return set(SUBSYSTEMS.keys())


# ---------------------------------------------------------------------------
# Category index — lists hubs, never their children
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_help_panel_state_returns_category_view(monkeypatch):
    """``resolve_help_panel_state`` returns :class:`HelpCategoryView` (the
    mother-hub category index). The dropdown lists mother hubs only —
    individual hub children (Blackjack, RPS, etc.) only appear after the
    user selects the relevant hub.
    """
    import discord as _discord

    interaction = MagicMock()
    interaction.client = MagicMock()

    vis_result = MagicMock()
    vis_result.visible_subsystems = _all_visible_set()
    vis_result.member_tier = "owner"

    fake_resolve = AsyncMock(return_value=vis_result)
    monkeypatch.setattr(
        help_cog.governance_service,
        "resolve_visibility",
        fake_resolve,
    )
    monkeypatch.setattr(
        help_cog.GovernanceContext,
        "from_interaction",
        lambda i: MagicMock(),
    )

    embed, view = await help_cog.resolve_help_panel_state(interaction)
    assert isinstance(view, help_cog.HelpCategoryView)

    # The top-level dropdown must never expose individual hub children
    # (e.g. Blackjack, RPS, Mining) — those are reached via the parent
    # hub category, not from Help directly.
    option_values: set[str] = set()
    for child in view.children:
        if isinstance(child, _discord.ui.Select):
            option_values.update(opt.value for opt in child.options)
    for child in _hub_children():
        assert child not in option_values, (
            f"hub child {child!r} leaked into HelpCategoryView dropdown"
        )
    # The Games hub itself IS in the dropdown.
    assert "games" in option_values


# ---------------------------------------------------------------------------
# Typed ``!help <category>`` still works for hub children
# ---------------------------------------------------------------------------


def test_typed_help_route_for_hub_child_resolves_to_subsystem():
    """``!help blackjack`` must resolve to the Blackjack subsystem so the
    panel opens — never to a parent-hub filter that would silently drop
    hub children. This is a runtime assertion against the resolver
    rather than a source-text grep; the previous implementation lived
    inside ``help_command`` and is now centralized in ``_resolve_route``.
    """
    from unittest.mock import MagicMock

    bot = MagicMock()
    bot.get_command = MagicMock(return_value=None)

    route = help_cog._resolve_route("blackjack", bot=bot)
    assert route.kind == "subsystem"
    assert route.target == "blackjack"

    # Mining is another canonical hub child — same expectation.
    route = help_cog._resolve_route("mining", bot=bot)
    assert route.kind == "subsystem"
    assert route.target == "mining"


# ---------------------------------------------------------------------------
# PR #3 — new parent_hub assignments for S7-S10 children
# ---------------------------------------------------------------------------


def test_pr3_metadata_assignments_present():
    """Pin the exact 8 parent_hub assignments PR #3 declares so future
    metadata edits cannot silently break the Help filter or the hub
    panel discovery contracts.
    """
    expected = {
        "inventory": "economy",
        "leaderboard": "economy",
        "xp": "community",
        "role": "community",
        "cleanup": "moderation",
        "logging": "moderation",
        "proof_channel": "moderation",
        "general": "utility",
    }
    for child, parent in expected.items():
        actual = SUBSYSTEMS[child].get("parent_hub")
        assert actual == parent, (
            f"SUBSYSTEMS[{child!r}].parent_hub: expected {parent!r}, got {actual!r}"
        )


@pytest.mark.asyncio
async def test_pr3_new_children_hidden_from_category_index(monkeypatch):
    """Every subsystem promoted in PR #3 must not appear in the top-level
    Help category index — they are reachable only through their parent hub.
    """
    interaction = MagicMock()
    interaction.client = MagicMock()

    vis_result = MagicMock()
    vis_result.visible_subsystems = _all_visible_set()
    vis_result.member_tier = "owner"

    monkeypatch.setattr(
        help_cog.governance_service,
        "resolve_visibility",
        AsyncMock(return_value=vis_result),
    )
    monkeypatch.setattr(
        help_cog.GovernanceContext,
        "from_interaction",
        lambda i: MagicMock(),
    )

    import discord as _discord

    _embed, view = await help_cog.resolve_help_panel_state(interaction)
    option_values: set[str] = set()
    for child in view.children:
        if isinstance(child, _discord.ui.Select):
            option_values.update(opt.value for opt in child.options)

    pr3_children = {
        "inventory",
        "leaderboard",
        "xp",
        "role",
        "cleanup",
        "logging",
        "proof_channel",
        "general",
    }
    for child in pr3_children:
        assert child not in option_values, (
            f"PR #3 child {child!r} leaked into the Help category index"
        )


def test_pr3_typed_routes_still_resolve_to_subsystem():
    """Typed ``!help <child>`` for each PR #3 child must still resolve
    to its subsystem so the panel opens. The filter hides them from the
    OVERVIEW, not from direct lookup.
    """
    from unittest.mock import MagicMock

    bot = MagicMock()
    bot.get_command = MagicMock(return_value=None)

    for name in (
        "inventory",
        "leaderboard",
        "xp",
        "role",
        "cleanup",
        "logging",
        "proof_channel",
        "general",
    ):
        route = help_cog._resolve_route(name, bot=bot)
        assert route.kind == "subsystem", f"{name!r} resolved as {route.kind!r}"
        assert route.target == name, f"{name!r} resolved to target {route.target!r}"
