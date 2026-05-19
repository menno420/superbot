"""Unit tests for HelpCategoryView (S3 — Help category index).

Pins the S3 behaviour:

- ``!help`` opens a category-grouped view, not the legacy paginated
  subsystem list.
- The dropdown shows one option per visible mother hub + the permanent
  ALL_COMMANDS fallback. Hub children never appear at this level.
- Selecting a hub category opens the hub's ``build_help_menu_view``
  and attaches Back-to-Help (which rebuilds the category view).
- Selecting ALL_COMMANDS swaps the view to :class:`HelpPanelView`
  populated with a parent_hub-filtered visible list.
- Permission/role matrix: admin-restricted hubs hide from non-admin
  users; the ALL_COMMANDS option is always visible.
- Failure paths surface as ephemerals; the message is never left
  half-edited.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs import help_cog
from cogs.help_cog import (
    ALL_COMMANDS_KEY,
    HelpCategoryView,
    HelpPanelView,
    build_categories_overview_embed,
)


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 7
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _select(view: HelpCategoryView) -> discord.ui.Select:
    return next(c for c in view.children if isinstance(c, discord.ui.Select))


# ---------------------------------------------------------------------------
# Embed shape — orientation rule from the mother-hub map
# ---------------------------------------------------------------------------


def test_categories_embed_lists_each_visible_hub_with_purpose_and_entry_cmd():
    """Per the orientation rule: every category states what it is for,
    who/what it includes, and its typed entry command.
    """
    embed = build_categories_overview_embed(member_tier="administrator")
    field_names = [f.name for f in embed.fields]
    field_values = [f.value for f in embed.fields]

    # The four S3-v1 hubs must each appear as a top-level field.
    assert any("Games" in n for n in field_names)
    assert any("Admin" in n for n in field_names)
    assert any("Settings" in n for n in field_names)
    assert any("Platform" in n for n in field_names)

    # Each field value contains the typed entry command.
    joined = "\n".join(field_values)
    assert "!games" in joined
    assert "!adminmenu" in joined
    assert "!settings" in joined
    assert "!platform" in joined


def test_categories_embed_always_includes_all_commands_fallback():
    embed = build_categories_overview_embed(member_tier="user")
    field_names = [f.name for f in embed.fields]
    assert any("All Commands" in n for n in field_names)


def test_categories_embed_hides_admin_only_hubs_from_normal_users():
    embed = build_categories_overview_embed(member_tier="user")
    field_names = [f.name for f in embed.fields]
    # Normal-tier users must not see administrator-restricted hubs as
    # top-level categories.
    assert not any("Admin" in n for n in field_names)
    assert not any("Settings" in n for n in field_names)
    assert not any("Platform" in n for n in field_names)
    # But Games (user tier) and the fallback are still visible.
    assert any("Games" in n for n in field_names)
    assert any("All Commands" in n for n in field_names)


def test_categories_embed_includes_line_lists_games_children():
    """The Games category must show its children in the 'Includes:'
    line so users know what's behind the dropdown.
    """
    embed = build_categories_overview_embed(member_tier="user")
    games_field = next(f for f in embed.fields if "Games" in f.name)
    # Pin a sampling of the known children rather than the full set —
    # changes to game roster shouldn't break this test.
    assert "Blackjack" in games_field.value
    assert "Mining" in games_field.value


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_one_select_with_visible_hubs_plus_all_commands():
    view = HelpCategoryView(member_tier="administrator")
    select = _select(view)
    values = {opt.value for opt in select.options}
    # Committed hubs visible to administrator + ALL_COMMANDS sentinel.
    # Economy joined in S7; further hubs land in S8-S10.
    assert values == {
        "games",
        "economy",
        "admin",
        "settings",
        "diagnostic",
        ALL_COMMANDS_KEY,
    }


def test_user_tier_view_omits_admin_hubs():
    view = HelpCategoryView(member_tier="user")
    select = _select(view)
    values = {opt.value for opt in select.options}
    assert "games" in values
    assert ALL_COMMANDS_KEY in values
    assert "admin" not in values
    assert "settings" not in values
    assert "diagnostic" not in values


def test_view_has_no_individual_hub_child_options():
    """Hub children (Blackjack, RPS, Mining, etc.) must never appear at
    the top level — they're reachable only through their parent hub.
    """
    view = HelpCategoryView(member_tier="owner")
    select = _select(view)
    values = {opt.value for opt in select.options}
    for hub_child in (
        "blackjack",
        "rps_tournament",
        "deathmatch",
        "mining",
        "counting",
        "chain",
    ):
        assert hub_child not in values, (
            f"hub child {hub_child!r} leaked into HelpCategoryView top-level"
        )


def test_view_default_member_tier_is_user_when_unspecified():
    view = HelpCategoryView()
    # Default tier is "user" — admin hubs must not surface.
    assert view._member_tier == "user"  # type: ignore[attr-defined]
    select = _select(view)
    values = {opt.value for opt in select.options}
    assert "admin" not in values


# ---------------------------------------------------------------------------
# Routing — All Commands branch swaps to HelpPanelView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_selecting_all_commands_swaps_to_help_panel_view(monkeypatch):
    """Selecting "All Commands / Advanced" opens the legacy paginated
    view in place. Custom IDs from the new dropdown go away because
    Discord matches the next click against the new view's custom_ids.
    """
    interaction = _interaction()
    interaction.data = {"values": [ALL_COMMANDS_KEY]}

    vis_result = MagicMock()
    vis_result.visible_subsystems = set(["economy", "mining", "games"])
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

    view = HelpCategoryView(member_tier="owner")
    await view._on_select(interaction)

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], HelpPanelView)


# ---------------------------------------------------------------------------
# Routing — Hub category opens host cog's build_help_menu_view
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_selecting_hub_category_opens_host_cog_panel(monkeypatch):
    interaction = _interaction()
    interaction.data = {"values": ["games"]}

    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
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

    fake_panel_view = discord.ui.View()
    fake_panel_embed = discord.Embed(title="Games Hub")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(
        return_value=(fake_panel_embed, fake_panel_view),
    )

    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
        view = HelpCategoryView(member_tier="owner")
        await view._on_select(interaction)

    fake_cog.build_help_menu_view.assert_awaited_once()
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is fake_panel_embed
    assert kwargs["view"] is fake_panel_view

    # Back-to-Help must be attached to the hub panel so the user can
    # return to the category index.
    back_buttons = [
        c
        for c in fake_panel_view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "help:back"
    ]
    assert len(back_buttons) == 1


@pytest.mark.asyncio
async def test_selecting_unknown_hub_sends_ephemeral(monkeypatch):
    interaction = _interaction()
    interaction.data = {"values": ["not_a_real_hub"]}

    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
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

    view = HelpCategoryView(member_tier="owner")
    await view._on_select(interaction)

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_hub_cog_missing_send_ephemeral(monkeypatch):
    interaction = _interaction()
    interaction.data = {"values": ["games"]}

    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
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

    with patch("cogs.help_cog._cog_for_subsystem", return_value=None):
        view = HelpCategoryView(member_tier="owner")
        await view._on_select(interaction)

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_hub_build_help_menu_view_exception_sends_ephemeral(monkeypatch):
    interaction = _interaction()
    interaction.data = {"values": ["games"]}

    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
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

    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))

    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
        view = HelpCategoryView(member_tier="owner")
        await view._on_select(interaction)

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


# ---------------------------------------------------------------------------
# Persistent-view registration
# ---------------------------------------------------------------------------


def test_help_category_view_registered_as_help_subsystem():
    """``HelpCategoryView`` is the canonical Help view after S3, so it
    must claim the ``"help"`` subsystem key in the persistent-view
    registry.
    """
    from core.runtime.persistent_views import get_view_class

    assert get_view_class("help") is HelpCategoryView


# ---------------------------------------------------------------------------
# Custom IDs are stable and follow <subsystem>:<action>
# ---------------------------------------------------------------------------


def test_category_select_custom_id_is_stable():
    """Custom ID must remain ``help_categories:select`` so that any
    future persistent-view registrations or click handlers continue
    to resolve.
    """
    view = HelpCategoryView(member_tier="owner")
    select = _select(view)
    assert select.custom_id == "help_categories:select"
