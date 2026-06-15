"""Tests for views.server_management.hub — the PR14 Server Management hub view.

Pins the shape + behaviour contract:

* persistent-view registration (restoration works for free),
* static, namespaced, actionable button custom_ids,
* admin-floor ``interaction_check`` (authority, not ownership — works for the
  anchored prefix panel AND the ephemeral slash),
* manager routing into each cog's ``build_help_menu_view`` hook with
  Back-to-hub attached, plus graceful missing-cog / hook-failure handling,
* the Setup button delegating to the wizard entry,
* the Refresh button recomposing in place,
* no module-level ``cogs`` import (the ``views → cogs`` arch boundary).
"""

from __future__ import annotations

import ast
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime.persistent_views import get_view_class
from services.server_management_hub import HubStatus, ManagerBadge
from views.server_management import hub as hub_mod
from views.server_management.hub import (
    _ROUTED_MANAGERS,
    ServerManagementHubView,
    build_hub_embed,
    build_server_management_hub,
)

_BUTTON_IDS = {
    "server_management:moderation",
    "server_management:channels",
    "server_management:roles",
    "server_management:cleanup",
    "server_management:setup",
    "server_management:access_map",
    "server_management:help_preview",
    "server_management:help_editor",
    "server_management:refresh",
}


def _interaction(*, admin: bool = True, guild: bool = True) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.user.guild_permissions.administrator = admin
    interaction.guild = MagicMock() if guild else None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _button(view: ServerManagementHubView, custom_id: str) -> discord.ui.Button:
    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == custom_id
    )


def _status() -> HubStatus:
    return HubStatus(
        guild_id=1,
        badges=(
            ManagerBadge("moderation", "🛡️", "Moderation", "🟢", "ok"),
            ManagerBadge("setup", "🧩", "Setup", "🟡", "64% configured"),
        ),
        overall_glyph="🟡",
        overall_summary="1 warning",
    )


# ---------------------------------------------------------------------------
# Registration + shape
# ---------------------------------------------------------------------------


def test_view_is_registered_for_restoration():
    assert get_view_class("server_management") is ServerManagementHubView
    assert ServerManagementHubView.SUBSYSTEM == "server_management"


def test_view_subsystem_is_registered_first_class():
    """The hub is a first-class subsystem — its SUBSYSTEM must resolve in
    SUBSYSTEMS so the identity-contract validator finds no orphan view and
    restoration maps the anchor back to this class.
    """
    from utils.subsystem_registry import SUBSYSTEMS

    assert ServerManagementHubView.SUBSYSTEM in SUBSYSTEMS


def test_view_constructs_with_no_args_for_restoration():
    # restore_anchors calls view_cls() with no args — must not raise.
    view = ServerManagementHubView()
    assert view.timeout is None  # PersistentView


def test_view_has_expected_button_custom_ids():
    view = ServerManagementHubView()
    actual = {c.custom_id for c in view.children if isinstance(c, discord.ui.Button)}
    assert actual == _BUTTON_IDS


def test_buttons_are_actionable_no_placeholders():
    view = ServerManagementHubView()
    forbidden = ("coming soon", "todo", "wip", "placeholder", "tbd")
    for btn in view.children:
        if not isinstance(btn, discord.ui.Button):
            continue
        assert btn.disabled is False
        lower = (btn.label or "").lower()
        assert not any(tok in lower for tok in forbidden)


def test_component_count_under_discord_cap_with_back_to_help():
    view = ServerManagementHubView()
    view.add_item(
        discord.ui.Button(
            label="↩ Back to Help",
            style=discord.ButtonStyle.secondary,
            custom_id="help:back",
            row=4,
        ),
    )
    assert len(view.children) <= 25


def test_routed_managers_cover_four_specialised_cogs():
    assert set(_ROUTED_MANAGERS) == {"moderation", "channels", "roles", "cleanup"}
    assert _ROUTED_MANAGERS["moderation"][0] == "ModerationCog"
    assert _ROUTED_MANAGERS["cleanup"][0] == "Cleanup"


# ---------------------------------------------------------------------------
# Authority — admin floor
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_interaction_check_admits_admin():
    view = ServerManagementHubView()
    assert await view.interaction_check(_interaction(admin=True)) is True


@pytest.mark.asyncio
async def test_interaction_check_denies_non_admin_with_ephemeral():
    view = ServerManagementHubView()
    interaction = _interaction(admin=False)
    assert await view.interaction_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# Manager routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_manager_routes_and_attaches_back_button():
    view = ServerManagementHubView()
    interaction = _interaction()
    child_view = discord.ui.View()
    child_embed = discord.Embed(title="Mod")
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(child_embed, child_view))
    interaction.client.get_cog.return_value = fake_cog

    await view._open_manager(interaction, "moderation")

    interaction.client.get_cog.assert_called_once_with("ModerationCog")
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is child_embed
    assert kwargs["view"] is child_view
    back = [
        c
        for c in child_view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "server_management:back"
    ]
    assert len(back) == 1


@pytest.mark.asyncio
async def test_open_manager_resolves_each_routed_cog_name():
    for key, (cog_name, _label) in _ROUTED_MANAGERS.items():
        view = ServerManagementHubView()
        interaction = _interaction()
        fake_cog = MagicMock()
        fake_cog.build_help_menu_view = AsyncMock(
            return_value=(discord.Embed(), discord.ui.View()),
        )
        interaction.client.get_cog.return_value = fake_cog
        await view._open_manager(interaction, key)
        interaction.client.get_cog.assert_called_once_with(cog_name)


@pytest.mark.asyncio
async def test_open_manager_missing_cog_sends_ephemeral():
    view = ServerManagementHubView()
    interaction = _interaction()
    interaction.client.get_cog.return_value = None

    await view._open_manager(interaction, "moderation")

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_open_manager_hook_failure_sends_ephemeral_not_crash():
    view = ServerManagementHubView()
    interaction = _interaction()
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))
    interaction.client.get_cog.return_value = fake_cog

    await view._open_manager(interaction, "roles")

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_manager_buttons_delegate_to_open_manager():
    expected = {
        "server_management:moderation": "moderation",
        "server_management:channels": "channels",
        "server_management:roles": "roles",
        "server_management:cleanup": "cleanup",
    }
    for custom_id, key in expected.items():
        view = ServerManagementHubView()
        interaction = _interaction()
        with patch.object(
            ServerManagementHubView,
            "_open_manager",
            new=AsyncMock(),
        ) as mock_open:
            await _button(view, custom_id).callback(interaction)
        mock_open.assert_awaited_once_with(interaction, key)


@pytest.mark.asyncio
async def test_setup_button_opens_wizard_entry():
    view = ServerManagementHubView()
    interaction = _interaction()
    with patch(
        "cogs.setup._wizard_entry.open_wizard_from_slash",
        new=AsyncMock(),
    ) as mock_open:
        await _button(view, "server_management:setup").callback(interaction)
    mock_open.assert_awaited_once_with(interaction)


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_recomposes_in_place():
    view = ServerManagementHubView()
    interaction = _interaction()
    with (
        patch.object(
            hub_mod,
            "collect_hub_status",
            new=AsyncMock(return_value=_status()),
        ),
        patch.object(hub_mod, "safe_defer", new=AsyncMock(return_value=True)),
        patch.object(hub_mod, "safe_edit", new=AsyncMock()) as mock_edit,
    ):
        await _button(view, "server_management:refresh").callback(interaction)
    mock_edit.assert_awaited_once()
    _args, kwargs = mock_edit.call_args
    assert kwargs["view"] is view


@pytest.mark.asyncio
async def test_refresh_outside_guild_sends_ephemeral():
    view = ServerManagementHubView()
    interaction = _interaction(guild=False)
    await _button(view, "server_management:refresh").callback(interaction)
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_server_management_hub_returns_embed_and_view():
    with patch.object(
        hub_mod,
        "collect_hub_status",
        new=AsyncMock(return_value=_status()),
    ):
        embed, view = await build_server_management_hub(MagicMock())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, ServerManagementHubView)


def test_build_hub_embed_renders_badges_and_overall():
    embed = build_hub_embed(_status())
    assert embed.title is not None and "Server Management" in embed.title
    text = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "Moderation" in text
    assert "Setup" in text
    assert "configuration health" in text.lower()


# ---------------------------------------------------------------------------
# Arch boundary — no module-level cogs import
# ---------------------------------------------------------------------------


def test_no_module_level_cogs_import():
    """The hub view must reach cogs only via lazy (function-body) imports or
    ``interaction.client.get_cog`` — never a module-level ``views → cogs`` edge.
    """
    src = inspect.getsource(hub_mod)
    tree = ast.parse(src)
    for node in tree.body:  # module-level statements only
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("cogs"):
            pytest.fail(f"module-level cogs import: from {node.module}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(
                    "cogs",
                ), f"module-level cogs import: {alias.name}"
