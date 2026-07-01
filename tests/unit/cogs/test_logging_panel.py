"""Unit tests for the S7d LoggingPanelView and LoggingCog wiring.

Covers:

- LoggingPanelView shape (6 buttons across 5 rows: Status, Set Mod,
  Set Cleanup, Create Mod, Create Cleanup, Test, Overview).
- Status / Overview buttons re-render the panel embed in place.
- Set buttons open LogChannelSelectView as ephemeral followups.
- Create buttons open LogChannelProvisionView with a preview embed.
- Test button calls services.server_logging.log_event with the same
  args as `!logging test`.
- LoggingCog.build_help_menu_view returns the panel view + embed.
- LoggingCog.cog_load registers the schema (idempotent).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.logging.panel import LoggingPanelView
from cogs.logging.provision_view import LogChannelProvisionView
from cogs.logging.select_view import LogChannelSelectView
from cogs.logging_cog import LoggingCog
from core.runtime import subsystem_schema as schema_mod


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for s in saved.values():
        schema_mod.register(s)


def _author(id_: int = 1) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    return member


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_panel_view_has_its_actions_plus_durable_nav():
    """Eight panel actions PLUS the universal durable nav.

    The eight actions (Refresh, Set Mod/Cleanup, Create Mod/Cleanup, Test,
    Routes, Overview) are joined by the auto-attached 📚 Help + ↩ Moderation
    controls: logging declares ``SUBSYSTEM`` with ``parent_hub="moderation"``,
    and the ``↩ Overview`` self-refresh no longer opts the panel out of
    standard nav (the stranding-fix — previously it did, leaving the panel
    dependent on a fragile externally-attached back).
    """
    view = LoggingPanelView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    labels = [b.label or "" for b in buttons]
    for expected in (
        "Refresh Status",
        "Set Mod Channel",
        "Set Cleanup Channel",
        "Create Mod Channel",
        "Create Cleanup Channel",
        "Test",
        "Routes",
        "Overview",
    ):
        assert any(expected in lbl for lbl in labels), f"missing action: {expected}"
    nav_ids = {b.custom_id for b in buttons if b.custom_id}
    assert "nav:help" in nav_ids, "expected the universal 📚 Help back button"
    assert "nav:hub:moderation" in nav_ids, "expected the ↩ Moderation hub back"
    assert len(buttons) == 10  # 8 actions + Help + hub-back
    rows = sorted({b.row for b in buttons})
    assert rows == [0, 1, 2, 3, 4]


def test_panel_view_button_labels_match_directive():
    view = LoggingPanelView(_author())
    labels = " | ".join(
        b.label or "" for b in view.children if isinstance(b, discord.ui.Button)
    )
    assert "Refresh Status" in labels
    assert "Set Mod Channel" in labels
    assert "Set Cleanup Channel" in labels
    assert "Create Mod Channel" in labels
    assert "Create Cleanup Channel" in labels
    assert "Test" in labels
    assert "Overview" in labels


# ---------------------------------------------------------------------------
# Status / Overview buttons — re-render panel embed in place
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_status_button_re_renders_panel_embed_in_place():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Refresh Status")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()

    fake_embed = discord.Embed(title="📝 Server logging — status")

    with (
        patch(
            "cogs.logging.panel.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "cogs.logging.panel.build_panel_embed",
            new_callable=AsyncMock,
            return_value=fake_embed,
        ),
        patch(
            "cogs.logging.panel.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is view
    assert edit.await_args.kwargs["embed"] is fake_embed


@pytest.mark.asyncio
async def test_overview_button_renders_panel_embed():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Overview")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()

    with (
        patch(
            "cogs.logging.panel.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "cogs.logging.panel.build_panel_embed",
            new_callable=AsyncMock,
            return_value=discord.Embed(title="overview"),
        ),
        patch(
            "cogs.logging.panel.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as edit,
    ):
        await btn.callback(interaction)
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is view


# ---------------------------------------------------------------------------
# Set buttons → ephemeral LogChannelSelectView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_mod_button_opens_log_channel_select_view():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Set Mod Channel")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()

    await btn.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    opened = kwargs["view"]
    assert isinstance(opened, LogChannelSelectView)
    assert opened.kind == "mod"


@pytest.mark.asyncio
async def test_set_cleanup_button_opens_log_channel_select_view():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Set Cleanup Channel")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()

    await btn.callback(interaction)

    opened = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(opened, LogChannelSelectView)
    assert opened.kind == "cleanup"


@pytest.mark.asyncio
async def test_set_button_rejects_dm_invocation():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Set Mod Channel")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = None
    interaction.response.send_message = AsyncMock()

    await btn.callback(interaction)

    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg


# ---------------------------------------------------------------------------
# Create buttons → LogChannelProvisionView with preview embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_mod_button_opens_provision_view_with_preview():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Create Mod Channel")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()

    fake_embed = discord.Embed(title="preview")
    with patch(
        "cogs.logging.provision_view.build_preview_embed",
        new_callable=AsyncMock,
        return_value=(fake_embed, True),
    ):
        await btn.callback(interaction)

    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True
    assert sent.kwargs["embed"] is fake_embed
    opened = sent.kwargs["view"]
    assert isinstance(opened, LogChannelProvisionView)
    assert opened.kind == "mod"


@pytest.mark.asyncio
async def test_create_cleanup_button_disables_confirm_when_preview_blocks():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Create Cleanup Channel")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()

    with patch(
        "cogs.logging.provision_view.build_preview_embed",
        new_callable=AsyncMock,
        return_value=(discord.Embed(title="blocked"), False),
    ):
        await btn.callback(interaction)
    opened = interaction.response.send_message.await_args.kwargs["view"]
    confirm = next(
        b
        for b in opened.children
        if isinstance(b, discord.ui.Button) and "Confirm" in (b.label or "")
    )
    assert confirm.disabled is True


# ---------------------------------------------------------------------------
# Test button → server_logging.log_event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_button_calls_log_event_with_warn_action():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Test")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.user.id = 42
    interaction.guild = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()

    with (
        patch(
            "cogs.logging.panel.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "services.server_logging.log_event",
            new_callable=AsyncMock,
            return_value=True,
        ) as log_event,
    ):
        await btn.callback(interaction)
    log_event.assert_awaited_once()
    kwargs = log_event.await_args.kwargs
    assert kwargs["action"] == "warn"
    assert kwargs["actor_id"] == 42
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_test_button_rejects_dm_invocation():
    view = LoggingPanelView(_author())
    btn = _find_button(view, "Test")
    interaction = MagicMock()
    interaction.user = view._author
    interaction.guild = None
    interaction.response.send_message = AsyncMock()

    await btn.callback(interaction)

    msg = interaction.response.send_message.await_args.args[0]
    assert "guild context" in msg


# ---------------------------------------------------------------------------
# LoggingCog hook + schema registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cog_load_registers_logging_schema():
    cog = LoggingCog(bot=MagicMock())
    assert "logging" not in schema_mod.registered_subsystems()
    await cog.cog_load()
    assert "logging" in schema_mod.registered_subsystems()


@pytest.mark.asyncio
async def test_build_help_menu_view_returns_logging_panel():
    cog = LoggingCog(bot=MagicMock())
    interaction = MagicMock()
    interaction.user = _author()
    interaction.guild = MagicMock()

    with patch(
        "cogs.logging.panel.build_panel_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="panel"),
    ):
        embed, view = await cog.build_help_menu_view(interaction)
    assert isinstance(view, LoggingPanelView)
    assert embed.title == "panel"
