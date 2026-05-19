"""Phase 4 tests — Help menu hides ``parent_hub`` children.

After Phase 3 lands, six game subsystems (Blackjack, RPS Tournament,
Deathmatch, Mining, Counting, Chain) carry ``parent_hub == "games"``.
Phase 4 hides them from the top-level Help menu — they remain
typed-accessible and reachable through the Games hub.

These tests assert:

* The overview embed (``build_overview_embed``) excludes any subsystem
  with ``parent_hub`` set.
* The paginated overview (``_build_page_embed``) does the same.
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
    return [
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "games"
    ]


def _all_visible_set() -> set[str]:
    """Visible set covering every subsystem — governance allows everything."""
    return set(SUBSYSTEMS.keys())


# ---------------------------------------------------------------------------
# Overview embed (non-paginated)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_overview_embed_excludes_parent_hub_children():
    bot = MagicMock()
    ctx = MagicMock()
    embed = await help_cog.build_overview_embed(
        bot,
        ctx,
        visible=_all_visible_set(),
        member_tier="owner",
    )

    rendered = "\n".join(field.value for field in embed.fields)
    for child in _hub_children():
        display = SUBSYSTEMS[child]["display_name"]
        assert display not in rendered, (
            f"hub child {child!r} ({display!r}) leaked into overview embed"
        )


@pytest.mark.asyncio
async def test_build_overview_embed_still_shows_games_hub():
    bot = MagicMock()
    ctx = MagicMock()
    embed = await help_cog.build_overview_embed(
        bot,
        ctx,
        visible=_all_visible_set(),
        member_tier="owner",
    )

    rendered = "\n".join(field.value for field in embed.fields)
    assert "Games" in rendered


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
    for child in _hub_children():
        display = SUBSYSTEMS[child]["display_name"]
        assert display not in rendered, (
            f"hub child {child!r} leaked into page-embed render"
        )


# ---------------------------------------------------------------------------
# visible_list construction sites
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_help_panel_state_visible_list_excludes_hub_children(
    monkeypatch,
):
    """``resolve_help_panel_state`` must filter hub children out of the
    visible_list it passes to HelpPanelView, otherwise pagination and
    the select would still include them.
    """
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
    visible_list = view._visible  # type: ignore[attr-defined]

    for child in _hub_children():
        assert child not in visible_list, (
            f"hub child {child!r} leaked into resolve_help_panel_state visible_list"
        )
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
    visible_list, member_tier = await view._resolve_visible(interaction)
    assert member_tier == "owner"
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
        name
        for name, meta in SUBSYSTEMS.items()
        if not meta.get("parent_hub")
    ]
    view = help_cog.HelpPanelView(visible_list=visible_list, page=0)

    select_options: set[str] = set()
    import discord as _discord

    for child in view.children:
        if isinstance(child, _discord.ui.Select):
            select_options.update(opt.value for opt in child.options)
    for child in _hub_children():
        assert child not in select_options, (
            f"hub child {child!r} leaked into HelpPanelView select options"
        )


# ---------------------------------------------------------------------------
# Typed ``!help <category>`` still works for hub children
# ---------------------------------------------------------------------------


def test_typed_help_category_lookup_unchanged_for_hub_children():
    """``!help blackjack`` resolves by iterating SUBSYSTEMS directly —
    the visible_set check still passes (governance allows blackjack),
    and there is no parent_hub filter on the category lookup branch.

    This test is a code-survey assertion rather than a runtime call: it
    inspects ``help_cog.HelpCog.help_command`` source to confirm the
    category branch doesn't filter on ``parent_hub``.
    """
    import inspect

    # ``help_command`` is wrapped by ``@commands.command`` into a Command
    # object — read the underlying callback source.
    src = inspect.getsource(help_cog.HelpCog.help_command.callback)
    # The overview branch builds visible_list with the parent_hub filter
    # (this is the line whose comment we want to find).
    assert "parent_hub" in src, (
        "help_command source no longer mentions parent_hub — filter likely removed"
    )
    # The category branch iterates ``SUBSYSTEMS.items()`` and skips
    # invisible names. It must NOT skip on parent_hub.
    # Match the actual ``if category:`` statement, not occurrences
    # inside docstrings or comments — code indentation is 8 spaces.
    category_branch_start = src.find("\n        if category:")
    assert category_branch_start != -1
    category_branch = src[category_branch_start:]
    # ``parent_hub`` must not appear inside the category branch.
    # (If a future refactor adds such a filter, this test will tell us.)
    assert "parent_hub" not in category_branch, (
        "category lookup branch now filters by parent_hub — that would "
        "break typed ``!help blackjack`` access"
    )
