"""Unit tests for the mining navigation fix (PR 4).

Before PR 4, picking a direction on ``MineView`` swapped the message
view to ``None`` — a dead end.  PR 4 introduces ``_MineResultsView``
(Mine Again / ↩ Mining Menu / 📚 Back to Help) so the user always
has an on-message way to continue.

These tests cover:

- the new prompt embed helper;
- ``_MineResultsView`` shape (3 buttons on row 0);
- the result of ``MineView._handle_mine`` swaps to
  ``_MineResultsView`` (not ``view=None``);
- Mine Again returns to a fresh ``MineView`` with the prompt embed;
- Mining Menu swaps to ``MiningHubView``;
- Help button resolves governance + opens ``HelpPanelView``;
- Help button falls back to an orange embed on governance failure.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.mining.mine_view import (
    MineView,
    _build_mine_prompt_embed,
    _MineResultsView,
)


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


# ---------------------------------------------------------------------------
# Prompt embed helper
# ---------------------------------------------------------------------------


def test_prompt_embed_describes_direction_choice():
    embed = _build_mine_prompt_embed()
    assert embed.title == "Mining"
    assert "direction" in (embed.description or "")


# ---------------------------------------------------------------------------
# _MineResultsView shape
# ---------------------------------------------------------------------------


def test_results_view_has_three_navigation_buttons_on_row_zero():
    view = _MineResultsView(user_id=1, guild_id=2)
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 3
    rows = {b.row for b in buttons}
    assert rows == {0}
    labels = " | ".join(b.label or "" for b in buttons)
    assert "Mine Again" in labels
    assert "Mining Menu" in labels
    assert "Help" in labels


def test_results_view_locks_to_invoking_user():
    view = _MineResultsView(user_id=42, guild_id=2)
    assert view.user_id == 42


@pytest.mark.asyncio
async def test_results_view_interaction_check_rejects_other_user():
    view = _MineResultsView(user_id=42, guild_id=2)
    interaction = MagicMock()
    interaction.user.id = 99
    assert await view.interaction_check(interaction) is False


# ---------------------------------------------------------------------------
# MineView._handle_mine swaps to _MineResultsView (no dead-end)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_mine_swaps_to_results_view_not_none():
    view = MineView(user_id=1, guild_id=2)
    interaction = MagicMock()
    interaction.user.mention = "@user"
    interaction.message = MagicMock()
    interaction.message.id = 12345
    interaction.followup.edit_message = AsyncMock()

    with patch(
        "views.mining.mine_view.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "views.mining.mine_view.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"pickaxe": 1},
    ), patch(
        "views.mining.mine_view.db.update_mining_item",
        new_callable=AsyncMock,
    ), patch(
        "views.mining.mine_view.roll_mine_loot",
        return_value=("stone", 5),
    ):
        await view._handle_mine(interaction, "left")

    interaction.followup.edit_message.assert_awaited_once()
    kwargs = interaction.followup.edit_message.await_args.kwargs
    # Crucial: view is not None.  This is the dead-end fix.
    swapped_view = kwargs["view"]
    assert swapped_view is not None
    assert isinstance(swapped_view, _MineResultsView)
    embed = kwargs["embed"]
    assert "stone" in (embed.description or "")
    assert "5" in (embed.description or "")
    assert kwargs["content"] is None


# ---------------------------------------------------------------------------
# Mine Again button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mine_again_button_swaps_to_fresh_mine_view():
    results = _MineResultsView(user_id=1, guild_id=2)
    btn = _find_button(results, "Mine Again")
    interaction = MagicMock()
    interaction.user.id = 1
    interaction.response.edit_message = AsyncMock()
    interaction.message = MagicMock()

    await btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    new_view = kwargs["view"]
    assert isinstance(new_view, MineView)
    assert new_view.user_id == 1
    assert new_view.guild_id == 2
    assert kwargs["embed"].title == "Mining"


# ---------------------------------------------------------------------------
# Mining Menu button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mining_menu_button_swaps_to_mining_hub_view():
    results = _MineResultsView(user_id=1, guild_id=2)
    btn = _find_button(results, "Mining Menu")
    interaction = MagicMock()
    interaction.user.id = 1
    interaction.response.edit_message = AsyncMock()

    await btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    swapped_view = kwargs["view"]
    # MiningHubView is a PersistentView — assert by class name to
    # avoid coupling to the import path.
    assert type(swapped_view).__name__ == "MiningHubView"
    embed = kwargs["embed"]
    assert "Mining Hub" in (embed.title or "")


# ---------------------------------------------------------------------------
# Help button — governance + HelpPanelView dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_button_opens_help_panel_with_visible_subsystems():
    results = _MineResultsView(user_id=1, guild_id=2)
    btn = _find_button(results, "Help")
    interaction = MagicMock()
    interaction.user.id = 1

    vis_result = MagicMock()
    vis_result.visible_subsystems = {"mining", "economy"}
    vis_result.member_tier = "everyone"
    fake_panel_view = discord.ui.View()
    fake_embed = discord.Embed(title="Help")

    with patch(
        "views.mining.mine_view.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ), patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "cogs.help_cog.all_subsystems_sorted",
        return_value=[
            ("mining", {}),
            ("economy", {}),
            ("admin", {}),
        ],
    ), patch(
        "cogs.help_cog.HelpPanelView",
        return_value=fake_panel_view,
    ) as panel_cls, patch(
        "cogs.help_cog._build_page_embed",
        return_value=fake_embed,
    ), patch(
        "views.mining.mine_view.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    panel_cls.assert_called_once()
    visible_list_arg = panel_cls.call_args.args[0]
    # admin is filtered out because it's not in visible_subsystems.
    assert visible_list_arg == ["mining", "economy"]
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is fake_panel_view


@pytest.mark.asyncio
async def test_help_button_falls_back_on_governance_failure():
    results = _MineResultsView(user_id=1, guild_id=2)
    btn = _find_button(results, "Help")
    interaction = MagicMock()
    interaction.user.id = 1

    with patch(
        "views.mining.mine_view.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        side_effect=RuntimeError("gov down"),
    ), patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "views.mining.mine_view.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    edit.assert_awaited_once()
    embed = edit.await_args.kwargs["embed"]
    assert "Help unavailable" in (embed.title or "")
    # Stay on the results view.
    assert edit.await_args.kwargs["view"] is results


@pytest.mark.asyncio
async def test_help_button_bails_when_defer_fails():
    results = _MineResultsView(user_id=1, guild_id=2)
    btn = _find_button(results, "Help")
    interaction = MagicMock()
    interaction.user.id = 1
    with patch(
        "views.mining.mine_view.safe_defer",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
    ) as resolver:
        await btn.callback(interaction)
    resolver.assert_not_called()
