"""Phase 4 tests — Help menu hides ``parent_hub`` children.

After Phase 3 lands, six game subsystems (Blackjack, RPS Tournament,
Deathmatch, Mining, Counting, Chain) carry ``parent_hub == "games"``.
Phase 4 hides them from the top-level Help menu — they remain
typed-accessible and reachable through the Games hub.

These tests assert:

* The paginated overview (``_build_page_embed``) excludes any subsystem
  with ``parent_hub`` set. (The legacy non-paginated
  ``build_overview_embed`` was production-dead and deleted in Batch 6 —
  HLP-2; its pins moved to the live surfaces.)
* The visible list assembled by ``resolve_help_panel_state``,
  ``_resolve_visible``, and the ``HelpCog.help_command`` typed entry
  excludes hub children.
* ``HelpPanelView`` constructed with a visible_list that already
  excludes hub children does not show them in the select options.
* The Games hub *itself* still appears in the menu.
* The typed ``!help blackjack`` lookup still resolves — the filter
  only affects the overview/select, not the category lookup.
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
    return [name for name, meta in SUBSYSTEMS.items() if meta.get("parent_hub")]


def _all_visible_set() -> set[str]:
    """Visible set covering every subsystem — governance allows everything."""
    return set(SUBSYSTEMS.keys())


# ---------------------------------------------------------------------------
# Paginated overview embed
# ---------------------------------------------------------------------------


def test_build_page_embed_excludes_parent_hub_children():
    bot = MagicMock()
    # Pass every subsystem name as the visible list so the filter, not
    # the visibility set, is what hides hub children.
    visible_list = list(SUBSYSTEMS.keys())
    embed = help_cog._build_page_embed(
        bot,
        visible_list=visible_list,
        page=0,
        member_tier="owner",
    )
    rendered = "\n".join(field.value for field in embed.fields)
    # Match the bolded display form so descriptions can't collide with
    # a hub child's display_name (see overview test above).
    for child in _hub_children():
        display = SUBSYSTEMS[child]["display_name"]
        assert (
            f"**{display}**" not in rendered
        ), f"hub child {child!r} leaked into page-embed render"


# ---------------------------------------------------------------------------
# visible_list construction sites
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_help_panel_state_returns_category_view(monkeypatch):
    """S3: ``resolve_help_panel_state`` returns the new
    :class:`HelpCategoryView` (mother-hub category index), not the
    legacy paginated subsystem list. The category view's dropdown lists
    mother hubs + the permanent "All Commands / Advanced" fallback —
    individual hub children (Blackjack, RPS, etc.) only appear after
    the user selects the relevant hub.
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
        assert (
            child not in option_values
        ), f"hub child {child!r} leaked into HelpCategoryView dropdown"
    # The Games hub itself IS in the dropdown.
    assert "games" in option_values


@pytest.mark.asyncio
async def test_help_category_view_all_commands_branch_filters_hub_children(
    monkeypatch,
):
    """Selecting "All Commands / Advanced" inside :class:`HelpCategoryView`
    swaps the view to :class:`HelpPanelView` populated with a
    parent_hub-filtered list — so the paginated fallback never leaks
    hub children into the top-level command list.
    """
    interaction = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.data = {"values": [help_cog.ALL_COMMANDS_KEY]}

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

    view = help_cog.HelpCategoryView(member_tier="owner")
    await view._on_select(interaction)

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    new_view = kwargs["view"]
    assert isinstance(new_view, help_cog.HelpPanelView)
    visible_list = new_view._visible  # type: ignore[attr-defined]
    for child in _hub_children():
        assert (
            child not in visible_list
        ), f"hub child {child!r} leaked into the All Commands view"
    assert "games" in visible_list


@pytest.mark.asyncio
async def test_help_panel_view_resolve_visible_excludes_hub_children(
    monkeypatch,
):
    interaction = MagicMock()

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

    view = help_cog.HelpPanelView(visible_list=list(SUBSYSTEMS.keys()), page=0)
    # HLP-3: _resolve_visible now returns the fresh projection (renames need
    # presentations downstream), not just the bare tier.
    visible_list, projection = await view._resolve_visible(interaction)
    assert projection.member_tier == "owner"
    for child in _hub_children():
        assert child not in visible_list, child
    assert "games" in visible_list


# ---------------------------------------------------------------------------
# Select options on HelpPanelView
# ---------------------------------------------------------------------------


def test_help_panel_view_select_omits_hub_children_when_visible_list_excludes_them():
    """When the visible_list passed to HelpPanelView excludes hub
    children, the select options also exclude them. (This is the
    natural consequence of the upstream filter — the test pins the
    contract.)
    """
    # Build a visible_list as the helper functions would: filtered.
    visible_list = [
        name for name, meta in SUBSYSTEMS.items() if not meta.get("parent_hub")
    ]
    view = help_cog.HelpPanelView(visible_list=visible_list, page=0)

    select_options: set[str] = set()
    import discord as _discord

    for child in view.children:
        if isinstance(child, _discord.ui.Select):
            select_options.update(opt.value for opt in child.options)
    for child in _hub_children():
        assert (
            child not in select_options
        ), f"hub child {child!r} leaked into HelpPanelView select options"


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
        assert (
            actual == parent
        ), f"SUBSYSTEMS[{child!r}].parent_hub: expected {parent!r}, got {actual!r}"


@pytest.mark.asyncio
async def test_pr3_new_children_hidden_from_overview():
    """Every subsystem promoted in PR #3 must not appear in the
    top-level Help overview (the Phase 4 filter is parent_hub-driven).

    Pinned against ``_build_page_embed`` — the live paginated overview —
    since the legacy ``build_overview_embed`` was deleted (Batch 6).
    Renders every page of the full subsystem list so the parent_hub
    filter (not pagination) is what excludes the children.
    """
    import math

    bot = MagicMock()
    visible_list = list(SUBSYSTEMS.keys())
    pages = max(1, math.ceil(len(visible_list) / help_cog._PAGE_SIZE))
    rendered = "\n".join(
        field.value
        for page in range(pages)
        for field in help_cog._build_page_embed(
            bot,
            visible_list=visible_list,
            page=page,
            member_tier="owner",
        ).fields
    )

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
    # Match the bolded display form to avoid substring collisions
    # (e.g. "General" appearing in Utility's description).
    for child in pr3_children:
        display = SUBSYSTEMS[child]["display_name"]
        assert f"**{display}**" not in rendered, (
            f"PR #3 child {child!r} ({display!r}) leaked into overview embed — "
            f"parent_hub filter is broken"
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
