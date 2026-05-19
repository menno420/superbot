"""Unit tests for cogs.help_cog.resolve_help_panel_state.

S3: the helper now returns a :class:`HelpCategoryView` — the new
mother-hub category index — instead of the legacy paginated
:class:`HelpPanelView`. Callers (``admin_cog.help_btn``,
``mine_view._MineResultsView.help_btn``) edit the message with the
returned ``(embed, view)`` pair; they don't care which class the
view is, only that it represents the top of Help.

Pinned contract:

- governance is resolved at every call;
- the returned view is :class:`HelpCategoryView`;
- the embed is built by :func:`build_categories_overview_embed` with
  the member tier from governance;
- exceptions from ``governance_service`` propagate so callers can
  render their own fallback (no swallowing inside the helper).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.help_cog import HelpCategoryView, resolve_help_panel_state


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
async def test_resolves_visibility_and_returns_category_view():
    """S3: the helper resolves governance, builds a category-index
    embed for the resolved tier, and returns the new
    :class:`HelpCategoryView` (not the legacy paginated view).
    """
    interaction = _interaction()
    vis_result = MagicMock()
    vis_result.visible_subsystems = {"economy", "mining"}
    vis_result.member_tier = "user"

    fake_view = HelpCategoryView(member_tier="user")
    fake_embed = discord.Embed(title="Help")

    with patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ), patch(
        "cogs.help_cog.HelpCategoryView",
        return_value=fake_view,
    ) as view_cls, patch(
        "cogs.help_cog.build_categories_overview_embed",
        return_value=fake_embed,
    ) as embed_builder:
        embed, view = await resolve_help_panel_state(interaction)

    view_cls.assert_called_once_with("user")
    embed_builder.assert_called_once_with("user")
    assert embed is fake_embed
    assert view is fake_view


@pytest.mark.asyncio
async def test_admin_tier_yields_category_view_with_admin_options():
    """An administrator-tier user sees admin-restricted hubs in the
    category dropdown — verifies the tier flows through governance
    into the view constructor.
    """
    interaction = _interaction()
    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
    vis_result.member_tier = "administrator"

    with patch(
        "services.governance_service.GovernanceContext.from_interaction",
        return_value=MagicMock(),
    ), patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vis_result,
    ):
        embed, view = await resolve_help_panel_state(interaction)

    assert isinstance(view, HelpCategoryView)
    assert view._member_tier == "administrator"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Failure mode — governance exception propagates (callers render fallback)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_governance_exception_propagates_to_caller():
    """The helper does NOT swallow governance failures. Each caller
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
