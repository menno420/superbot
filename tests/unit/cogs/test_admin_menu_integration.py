"""Unit tests for the admin menu integration buttons (PR 2).

The admin menu (``!adminmenu`` / ``_AdminPanelView``) gains six
navigation buttons that route into existing cog hubs / panels:

- 🛠 Settings    → SettingsCog.build_help_menu_view
- 🛰 Platform    → views.diagnostic._PlatformHubView (PR 1)
- 🩺 Diagnostics → DiagnosticCog.build_help_menu_view
- 📝 Logging     → build_logging_status_embed (in-place)
- 🧹 Cleanup     → Cleanup.build_help_menu_view
- 📚 Help        → cogs.help_cog.HelpPanelView

These tests cover the view shape and the dispatch wiring.  The
``build_help_menu_view`` hooks are mocked so we exercise the admin
panel's routing logic without instantiating each downstream cog.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.admin_cog import (
    AdminCog,
    _AdminPanelView,
    attach_back_to_admin_button,
)
from cogs.logging_cog import build_logging_status_embed


def _ctx_shim(user_id: int = 1) -> MagicMock:
    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = user_id
    return ctx


def _admin_view(user_id: int = 1) -> _AdminPanelView:
    bot = MagicMock()
    bot.extensions = {"cogs.admin_cog": object()}
    cog = AdminCog(bot=bot)
    return _AdminPanelView(_ctx_shim(user_id), cog)


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_admin_view_has_eleven_components_across_four_rows():
    view = _admin_view()
    # 4 existing tool buttons + 6 navigation buttons + 1 overview = 11.
    assert len(view.children) == 11
    rows = sorted({c.row for c in view.children})
    assert rows == [0, 1, 2, 3]


def test_admin_view_row_zero_contains_four_existing_tool_buttons():
    view = _admin_view()
    row0 = [c for c in view.children if c.row == 0]
    labels = [b.label for b in row0]
    assert len(row0) == 4
    assert any("Server Stats" in (lbl or "") for lbl in labels)
    assert any("Cog List" in (lbl or "") for lbl in labels)
    assert any("Reload All" in (lbl or "") for lbl in labels)
    assert any("Log Level" in (lbl or "") for lbl in labels)


def test_admin_view_navigation_buttons_cover_all_six_destinations():
    view = _admin_view()
    nav_labels = [
        c.label
        for c in view.children
        if c.row in (1, 2) and isinstance(c, discord.ui.Button)
    ]
    assert len(nav_labels) == 6
    # Order-independent — verify each destination is reachable from
    # the panel.
    joined = " | ".join(lbl or "" for lbl in nav_labels)
    assert "Settings" in joined
    assert "Platform" in joined
    assert "Diagnostics" in joined
    assert "Logging" in joined
    assert "Cleanup" in joined
    assert "Help" in joined


def test_admin_view_overview_is_last_row():
    view = _admin_view()
    overview = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and "Overview" in (c.label or "")
    )
    assert overview.row == 3
    assert overview.style == discord.ButtonStyle.secondary


def test_admin_overview_description_mentions_both_tools_and_navigation():
    view = _admin_view()
    embed = view.build_embed()
    description = embed.description or ""
    assert "Tools" in description
    assert "Navigate" in description


# ---------------------------------------------------------------------------
# Logging button — direct dispatch to the extracted builder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logging_button_routes_through_logging_cog_hook():
    """S7d: Logging button opens LoggingPanelView via the standard
    cog hook (same pattern as Settings / Diagnostics / Cleanup)."""
    view = _admin_view()
    btn = _find_button(view, "Logging")
    interaction = MagicMock()
    interaction.user = view._author

    fake_cog = MagicMock()
    fake_embed = discord.Embed(title="📝 Logging panel")
    fake_view: discord.ui.View = discord.ui.View()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))
    interaction.client.get_cog.return_value = fake_cog

    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)
    interaction.client.get_cog.assert_called_with("LoggingCog")
    fake_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["embed"] is fake_embed
    # Back-to-admin button must be attached to the routed sub-view.
    back_btns = [
        c
        for c in fake_view.children
        if isinstance(c, discord.ui.Button) and "Back to Admin" in (c.label or "")
    ]
    assert len(back_btns) == 1


@pytest.mark.asyncio
async def test_logging_button_bails_when_defer_fails():
    view = _admin_view()
    btn = _find_button(view, "Logging")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.client.get_cog = MagicMock()
    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=False,
    ):
        await btn.callback(interaction)
    # Defer-failure short-circuits before the cog lookup.
    interaction.client.get_cog.assert_not_called()


# ---------------------------------------------------------------------------
# Platform button — opens _PlatformHubView from PR 1
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_button_opens_platform_hub_view():
    view = _admin_view()
    btn = _find_button(view, "Platform")
    interaction = MagicMock()
    interaction.user = view._author
    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)
    # _PlatformHubView is the swap target — verify by class name to
    # avoid coupling to the import path.
    edit.assert_awaited_once()
    swapped_view = edit.await_args.kwargs["view"]
    assert type(swapped_view).__name__ == "_PlatformHubView"


@pytest.mark.asyncio
async def test_platform_button_attaches_back_to_admin_button():
    view = _admin_view()
    btn = _find_button(view, "Platform")
    interaction = MagicMock()
    interaction.user = view._author
    captured: dict[str, discord.ui.View] = {}

    async def _capture_edit(interaction, **kwargs):
        captured["view"] = kwargs["view"]
        return True

    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch("cogs.admin_cog.safe_edit", new=_capture_edit):
        await btn.callback(interaction)
    sub_view = captured["view"]
    back_btns = [
        c
        for c in sub_view.children
        if isinstance(c, discord.ui.Button) and "Back to Admin" in (c.label or "")
    ]
    assert len(back_btns) == 1


# ---------------------------------------------------------------------------
# _open_via_help_hook — Settings / Diagnostics / Cleanup buttons share this
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_via_help_hook_invokes_target_cog_hook():
    view = _admin_view()
    interaction = MagicMock()
    interaction.user = view._author

    fake_cog = MagicMock()
    fake_embed = discord.Embed(title="Subsystem")
    fake_view: discord.ui.View = discord.ui.View()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))
    interaction.client.get_cog.return_value = fake_cog

    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await view._open_via_help_hook(interaction, cog_name="SettingsCog")
    interaction.client.get_cog.assert_called_with("SettingsCog")
    fake_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["embed"] is fake_embed
    # Back-to-admin button must be attached to the routed sub-view.
    back_btns = [
        c
        for c in fake_view.children
        if isinstance(c, discord.ui.Button) and "Back to Admin" in (c.label or "")
    ]
    assert len(back_btns) == 1


@pytest.mark.asyncio
async def test_open_via_help_hook_handles_missing_cog():
    view = _admin_view()
    interaction = MagicMock()
    interaction.user = view._author
    interaction.client.get_cog.return_value = None
    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await view._open_via_help_hook(interaction, cog_name="GhostCog")
    edit.assert_awaited_once()
    embed = edit.await_args.kwargs["embed"]
    assert "GhostCog unavailable" in (embed.title or "")
    # Stay on the admin view; do not swap.
    assert edit.await_args.kwargs["view"] is view


@pytest.mark.asyncio
async def test_open_via_help_hook_handles_hook_exception():
    view = _admin_view()
    interaction = MagicMock()
    interaction.user = view._author
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))
    interaction.client.get_cog.return_value = fake_cog
    with patch(
        "cogs.admin_cog.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await view._open_via_help_hook(interaction, cog_name="SettingsCog")
    embed = edit.await_args.kwargs["embed"]
    assert "SettingsCog unavailable" in (embed.title or "")
    assert "RuntimeError" in (embed.description or "")


# ---------------------------------------------------------------------------
# Help button — resolves governance and opens HelpPanelView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_button_opens_help_category_view():
    """S3: the admin Help button returns the user to the top of Help,
    which is now :class:`HelpCategoryView` (mother-hub categories).
    """
    view = _admin_view()
    btn = _find_button(view, "Help")
    interaction = MagicMock()
    interaction.user = view._author

    vis_result = MagicMock()
    vis_result.visible_subsystems = {"economy", "moderation"}
    vis_result.member_tier = "administrator"
    fake_view = discord.ui.View()
    fake_embed = discord.Embed(title="Help")

    with patch(
        "cogs.admin_cog.safe_defer",
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
        "cogs.help_cog.HelpCategoryView",
        return_value=fake_view,
    ) as view_cls, patch(
        "cogs.help_cog.build_categories_overview_embed",
        return_value=fake_embed,
    ), patch(
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)
    # HLP-2: the view receives the audience projection built from the
    # governance result, not a bare tier string.
    view_cls.assert_called_once()
    projection = view_cls.call_args.kwargs["projection"]
    assert projection.member_tier == "administrator"
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is fake_view


@pytest.mark.asyncio
async def test_help_button_falls_back_to_orange_embed_on_governance_failure():
    view = _admin_view()
    btn = _find_button(view, "Help")
    interaction = MagicMock()
    interaction.user = view._author
    with patch(
        "cogs.admin_cog.safe_defer",
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
        "cogs.admin_cog.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)
    embed = edit.await_args.kwargs["embed"]
    assert "Help unavailable" in (embed.title or "")
    assert edit.await_args.kwargs["view"] is view


# ---------------------------------------------------------------------------
# attach_back_to_admin_button helper
# ---------------------------------------------------------------------------


def test_attach_back_to_admin_button_adds_a_button():
    sub_view: discord.ui.View = discord.ui.View()
    author = MagicMock()
    author.id = 7
    attach_back_to_admin_button(sub_view, author)
    btns = [c for c in sub_view.children if isinstance(c, discord.ui.Button)]
    assert len(btns) == 1
    assert "Back to Admin" in (btns[0].label or "")
    assert btns[0].custom_id == "admin:back"
    assert btns[0].row == 4


def test_attach_back_to_admin_button_noop_when_view_full():
    sub_view: discord.ui.View = discord.ui.View()
    # Fill to 25 components.
    for i in range(25):
        sub_view.add_item(
            discord.ui.Button(label=f"x{i}", custom_id=f"x{i}", row=i // 5),
        )
    author = MagicMock()
    attach_back_to_admin_button(sub_view, author)
    # Still 25 — no overflow.
    assert len(sub_view.children) == 25


# ---------------------------------------------------------------------------
# build_logging_status_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_logging_status_embed_with_disabled_logging():
    guild = MagicMock()
    guild.id = 1234
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "services.server_logging.auto_create_enabled",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "services.server_logging.counters_snapshot",
        return_value={"counters": {"sent": 0, "failed": 0}},
    ):
        embed = await build_logging_status_embed(guild)
    field_names = [f.name for f in embed.fields]
    assert field_names == [
        "Enabled",
        "Auto-create channels",
        "Mod channel",
        "Cleanup channel",
        "Counters (process-local)",
    ]
    enabled_field = next(f for f in embed.fields if f.name == "Enabled")
    assert "off" in enabled_field.value


@pytest.mark.asyncio
async def test_build_logging_status_embed_with_no_guild():
    """DM invocation: build with guild=None must not crash."""
    with patch(
        "services.server_logging.counters_snapshot",
        return_value={"counters": {}},
    ):
        embed = await build_logging_status_embed(None)
    assert "Server logging" in (embed.title or "")
