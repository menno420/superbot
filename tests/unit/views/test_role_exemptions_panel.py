"""Tests for the role-automation exemptions settings panel."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from views.roles.exemptions_panel import RoleExemptionsPanel


def _ctx(guild_roles: list | None = None) -> SimpleNamespace:
    guild = MagicMock()
    guild.id = 1
    roles = {r.id: r for r in (guild_roles or [])}
    guild.get_role.side_effect = lambda rid: roles.get(rid)
    return SimpleNamespace(author=MagicMock(id=99), guild=guild, bot=MagicMock())


@pytest.mark.asyncio
async def test_build_embed_lists_exemptions_and_stacking_state():
    role = SimpleNamespace(id=10, name="Admin", mention="@Admin")
    panel = RoleExemptionsPanel(_ctx([role]))
    rows = [{"role_id": 10, "exempt_xp": True, "exempt_time": False}]
    with (
        patch("utils.db.get_role_exemptions", new=AsyncMock(return_value=rows)),
        patch(
            "services.settings_resolution.resolve_value",
            new=AsyncMock(side_effect=[False, True]),  # time=single, xp=stack
        ),
    ):
        embed = await panel.build_embed()

    fields = {f.name: f.value for f in embed.fields}
    assert "XP" in fields["Current exemptions"]
    assert "single" in fields["Tier stacking"].lower()
    assert "stack" in fields["Tier stacking"].lower()


@pytest.mark.asyncio
async def test_apply_writes_each_selected_role_through_service():
    panel = RoleExemptionsPanel(_ctx())
    panel.selected_role_ids = [10, 20]
    interaction = MagicMock()
    interaction.user.id = 99
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()

    with (
        patch("utils.db.get_role_exemptions", new=AsyncMock(return_value=[])),
        patch(
            "services.settings_resolution.resolve_value",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "services.role_exemption_service.set_exemption",
            new=AsyncMock(),
        ) as set_mock,
    ):
        await panel._apply(interaction, field="xp", value=True)

    assert set_mock.await_count == 2
    for call in set_mock.await_args_list:
        assert call.kwargs["exempt_xp"] is True
        assert call.kwargs["exempt_time"] is False  # untouched (no prior row)
        assert call.kwargs["actor_id"] == 99
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_without_selection_warns_and_does_not_write():
    panel = RoleExemptionsPanel(_ctx())
    panel.selected_role_ids = []
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    with patch(
        "services.role_exemption_service.set_exemption",
        new=AsyncMock(),
    ) as set_mock:
        await panel._apply(interaction, field="time", value=True)

    set_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()
