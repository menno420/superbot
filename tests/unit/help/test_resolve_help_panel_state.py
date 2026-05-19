"""Unit tests for cogs.help_cog.resolve_help_panel_state.

The helper consolidates the governance-resolve + HelpPanelView-open
flow used by navigation buttons in other cogs / views
(admin_cog.help_btn, mine_view._MineResultsView.help_btn).  These
tests pin the helper's contract:

- it resolves the visibility set via governance and filters
  all_subsystems_sorted() to that set;
- it instantiates HelpPanelView with the filtered list at page=0;
- it builds the page embed via _build_page_embed with the resolved
  member tier;
- it returns (embed, view) — never raises on the happy path;
- exceptions from governance_service propagate so callers can render
  their own fallback (no swallowing inside the helper).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.help_cog import HelpPanelView, resolve_help_panel_state


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.client = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 1
    return interaction


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolves_visible_subsystems_and_returns_panel_state():
    interaction = _interaction()
    vis_result = MagicMock()
    vis_result.visible_subsystems = {"economy", "mining"}
    vis_result.member_tier = "user"

    fake_panel_view = HelpPanelView(visible_list=[], page=0)
    fake_embed = discord.Embed(title="Help")

    with patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ), patch(
        "cogs.help_cog.all_subsystems_sorted",
        return_value=[("economy", {}), ("mining", {}), ("admin", {})],
    ), patch(
        "cogs.help_cog.HelpPanelView",
        return_value=fake_panel_view,
    ) as panel_cls, patch(
        "cogs.help_cog._build_page_embed",
        return_value=fake_embed,
    ) as page_builder:
        embed, view = await resolve_help_panel_state(interaction)

    # admin must be filtered out (not in visible_subsystems).
    panel_cls.assert_called_once()
    visible_list_arg = panel_cls.call_args.args[0]
    assert visible_list_arg == ["economy", "mining"]
    assert panel_cls.call_args.kwargs.get("page") == 0

    page_builder.assert_called_once()
    # _build_page_embed(bot, visible_list, page=0, member_tier).
    pb_args = page_builder.call_args.args
    assert pb_args[0] is interaction.client
    assert pb_args[1] == ["economy", "mining"]
    assert pb_args[2] == 0
    assert pb_args[3] == "user"

    assert embed is fake_embed
    assert view is fake_panel_view


@pytest.mark.asyncio
async def test_empty_visible_subsystems_yields_empty_visible_list():
    interaction = _interaction()
    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
    vis_result.member_tier = "user"

    fake_panel_view = HelpPanelView(visible_list=[], page=0)
    fake_embed = discord.Embed(title="Help")

    with patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ), patch(
        "cogs.help_cog.all_subsystems_sorted",
        return_value=[("economy", {}), ("mining", {})],
    ), patch(
        "cogs.help_cog.HelpPanelView",
        return_value=fake_panel_view,
    ) as panel_cls, patch(
        "cogs.help_cog._build_page_embed",
        return_value=fake_embed,
    ):
        embed, view = await resolve_help_panel_state(interaction)
    assert panel_cls.call_args.args[0] == []
    assert embed is fake_embed
    assert view is fake_panel_view


# ---------------------------------------------------------------------------
# Failure mode — governance exception propagates (callers render fallback)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_governance_exception_propagates_to_caller():
    """The helper does NOT swallow governance failures.  Each caller
    (admin_cog, mine_view) wraps the call in its own try/except to
    render a contextual orange embed."""
    interaction = _interaction()
    with patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        side_effect=RuntimeError("gov down"),
    ):
        with pytest.raises(RuntimeError, match="gov down"):
            await resolve_help_panel_state(interaction)


# ---------------------------------------------------------------------------
# Visibility filtering preserves all_subsystems_sorted ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_visible_list_preserves_registry_ordering():
    """The filtered list must keep the order produced by
    all_subsystems_sorted, not the iteration order of the visibility
    set (which is unordered)."""
    interaction = _interaction()
    vis_result = MagicMock()
    vis_result.visible_subsystems = {"c", "a", "b"}
    vis_result.member_tier = "user"

    fake_panel_view = HelpPanelView(visible_list=[], page=0)
    with patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ), patch(
        "cogs.help_cog.all_subsystems_sorted",
        return_value=[("a", {}), ("b", {}), ("c", {})],
    ), patch(
        "cogs.help_cog.HelpPanelView",
        return_value=fake_panel_view,
    ) as panel_cls, patch(
        "cogs.help_cog._build_page_embed",
        return_value=discord.Embed(),
    ):
        await resolve_help_panel_state(interaction)
    assert panel_cls.call_args.args[0] == ["a", "b", "c"]
