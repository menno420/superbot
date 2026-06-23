"""Role-panel in-place navigation + the temproles panel surface (Ultracode U2).

Two behaviours pinned here:

1. The role-hub **Create** buttons (RoleHubView and ManagementPanel) navigate in
   place — they ``interaction.response.edit_message(...)`` the anchor to the
   creation panel instead of sending a fresh ephemeral (the ``edit_in_place``
   consistency finding these cleared). The opened RoleCreatePanel carries a Back
   button so the navigation is reversible.

2. The Time-Roles panel's **⏳ My Temp Roles** button surfaces the ``!temproles``
   listing (RoleGrantsCog) in the hub — the command-reachability fix — reading
   through ``role_grants_service.list_active_grants`` and navigating in place to a
   read-only listing view with a Back button.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _interaction(*, user_id: int = 7) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.user.guild_permissions = SimpleNamespace(
        manage_roles=True,
        administrator=True,
    )
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(author=SimpleNamespace(id=7), guild=MagicMock())


# ---------------------------------------------------------------------------
# Task A — Create buttons navigate in place (edit_message, not send_message)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_hub_create_navigates_in_place():
    """RoleHubView.create_btn edits the anchor to the creation panel in place."""
    from views.roles.main_panel import RoleHubView

    hub = RoleHubView(_ctx(), cog=MagicMock())
    hub.message = SimpleNamespace(id=555)
    interaction = _interaction()

    await RoleHubView.create_btn(hub, interaction, MagicMock())

    interaction.response.edit_message.assert_awaited_once()
    interaction.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_management_create_navigates_in_place():
    """ManagementPanel.create_btn edits the anchor in place, with a parent set."""
    from views.roles.creation_panel import RoleCreatePanel
    from views.roles.management_panel import ManagementPanel

    panel = ManagementPanel(_ctx())
    panel.message = SimpleNamespace(id=777)
    interaction = _interaction()

    await ManagementPanel.create_btn(panel, interaction, MagicMock())

    interaction.response.edit_message.assert_awaited_once()
    interaction.response.send_message.assert_not_awaited()
    # The opened view is a creation panel that knows its parent (for Back nav).
    opened = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(opened, RoleCreatePanel)
    assert opened.parent is panel


@pytest.mark.asyncio
async def test_creation_panel_has_back_button_when_parented():
    """RoleCreatePanel opened from a hub carries a Back button (reversible nav)."""
    import discord

    from views.roles.creation_panel import RoleCreatePanel

    parent = MagicMock()
    panel = RoleCreatePanel(_ctx(), parent=parent)

    backs = [
        c
        for c in panel.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "role:create:back"
    ]
    assert len(backs) == 1

    # A top-level (parentless) open has no Back button.
    assert not [
        c
        for c in RoleCreatePanel(_ctx()).children
        if isinstance(c, discord.ui.Button)
        and getattr(c, "custom_id", None) == "role:create:back"
    ]


# ---------------------------------------------------------------------------
# Task B — Time-Roles panel surfaces !temproles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_time_roles_temp_roles_btn_navigates_in_place():
    """The ⏳ My Temp Roles button edits the anchor to the listing in place."""
    from views.roles.time_roles_panel import TimeRolesPanel, _TempRolesView

    panel = TimeRolesPanel(_ctx())
    panel.message = SimpleNamespace(id=321)
    interaction = _interaction()

    with patch(
        "services.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[]),
    ):
        await TimeRolesPanel.temp_roles_btn(panel, interaction, MagicMock())

    interaction.response.edit_message.assert_awaited_once()
    interaction.response.send_message.assert_not_awaited()
    opened = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(opened, _TempRolesView)


@pytest.mark.asyncio
async def test_temp_roles_view_lists_active_grants():
    """The listing reads list_active_grants for the viewer and renders each role."""
    from views.roles.time_roles_panel import TimeRolesPanel, _TempRolesView

    panel = TimeRolesPanel(_ctx())
    view = _TempRolesView(panel)
    interaction = _interaction(user_id=7)
    expires = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)
    role = SimpleNamespace(id=42, mention="<@&42>")

    with patch(
        "services.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[(role, expires)]),
    ) as list_mock:
        embed = await view.build_embed(interaction)

    # Reads the viewer's own grants (the no-arg !temproles form).
    list_mock.assert_awaited_once_with(interaction.guild, 7)
    assert "<@&42>" in embed.description


@pytest.mark.asyncio
async def test_temp_roles_view_empty_state():
    """No grants → the friendly empty-state copy, still reading the service."""
    from views.roles.time_roles_panel import TimeRolesPanel, _TempRolesView

    panel = TimeRolesPanel(_ctx())
    view = _TempRolesView(panel)
    interaction = _interaction()

    with patch(
        "services.role_grants_service.list_active_grants",
        new=AsyncMock(return_value=[]),
    ):
        embed = await view.build_embed(interaction)

    assert "no active temp roles" in embed.description.lower()


@pytest.mark.asyncio
async def test_temp_roles_view_has_back_button():
    """The listing view has a Back button to the time-roles panel."""
    import discord

    from views.roles.time_roles_panel import TimeRolesPanel, _TempRolesView

    view = _TempRolesView(TimeRolesPanel(_ctx()))
    backs = [
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "role:temproles:back"
    ]
    assert len(backs) == 1
