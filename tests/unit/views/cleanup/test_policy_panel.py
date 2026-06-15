"""Tests for the cleanup-policy operator panel view (server-management PR9).

The heavy logic lives in services.cleanup_diagnostics (tested separately); here
we pin the view wiring: embeds render, the admin re-check gates the builder and
the apply, the dry-run never writes, and confirm routes to the audited apply.
``discord.ui.Select.values`` falls back to ``self._values``, so we drive select
callbacks by setting that backing list.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.cleanup.policy_panel as panel
from governance.models import CleanupPolicy, PolicySource
from services.cleanup_diagnostics import (
    CleanupDiagnostics,
    CleanupPolicyPreview,
    CleanupScopeRow,
)
from services.governance_exceptions import GovernanceError

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _row(**kw):
    base = dict(
        scope_type="channel",
        scope_id=111,
        level_name="Light",
        delete_invalid_commands=True,
        delete_failed_commands=False,
        delete_after_seconds=10,
        policy_version=1,
        target_label="#general",
        is_stale=False,
        is_ineffective=False,
    )
    base.update(kw)
    return CleanupScopeRow(**base)


def _preview(will_change=True, warnings=()):
    return CleanupPolicyPreview(
        scope_type="channel",
        scope_id=111,
        target_label="#general",
        level="Strict",
        new_delete_message=True,
        new_delete_after_seconds=2,
        current=CleanupPolicy(
            delete_message=False,
            delete_after_seconds=0,
            send_feedback=True,
            resolved_from=PolicySource.FALLBACK_DEFAULT,
        ),
        will_change=will_change,
        warnings=tuple(warnings),
    )


def _interaction(admin: bool = True):
    it = MagicMock(spec=discord.Interaction)
    it.user = MagicMock()
    perms = MagicMock()
    perms.administrator = admin
    it.user.guild_permissions = perms
    it.guild = MagicMock()
    it.guild.id = 42
    it.response = MagicMock()
    it.response.send_message = AsyncMock()
    it.response.edit_message = AsyncMock()
    return it


def test_diagnostics_embed_empty():
    diag = CleanupDiagnostics(guild_id=42, rows=(), level_counts={})
    embed = panel.diagnostics_embed_from(diag)
    text = " ".join(f.value for f in embed.fields)
    assert "None" in text


def test_diagnostics_embed_lists_rows_and_flags():
    diag = CleanupDiagnostics(
        guild_id=42,
        rows=(
            _row(
                scope_type="guild",
                scope_id=0,
                target_label="Guild default",
                level_name="Standard",
                is_ineffective=True,
            ),
            _row(
                scope_type="channel",
                scope_id=999,
                target_label="channel 999 (deleted)",
                is_stale=True,
            ),
        ),
        level_counts={"Standard": 1, "Light": 1},
    )
    embed = panel.diagnostics_embed_from(diag)
    names = [f.name for f in embed.fields]
    assert any("Ineffective" in n for n in names)
    assert any("Stale" in n for n in names)


def test_preview_embed_change_shows_warnings():
    embed = panel.preview_embed_from(
        _preview(will_change=True, warnings=("watch out",))
    )
    assert any("watch out" in f.value for f in embed.fields)


def test_preview_embed_no_change_field():
    embed = panel.preview_embed_from(_preview(will_change=False))
    assert any("No change" in f.name for f in embed.fields)


# ---------------------------------------------------------------------------
# CleanupPolicyPanelView buttons
# ---------------------------------------------------------------------------


def _btn(view, custom_id):
    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == custom_id
    )


@pytest.mark.asyncio
async def test_build_button_requires_admin():
    view = panel.CleanupPolicyPanelView(MagicMock(), MagicMock())
    it = _interaction(admin=False)
    await _btn(view, "cleanup_policy:build").callback(it)
    it.response.send_message.assert_awaited_once()
    assert "Administrator" in it.response.send_message.call_args.args[0]


@pytest.mark.asyncio
async def test_build_button_admin_opens_scope_select():
    guild = MagicMock()
    view = panel.CleanupPolicyPanelView(MagicMock(), guild)
    it = _interaction(admin=True)
    await _btn(view, "cleanup_policy:build").callback(it)
    it.response.send_message.assert_awaited_once()
    sent_view = it.response.send_message.call_args.kwargs["view"]
    assert any(isinstance(c, panel._ScopeSelect) for c in sent_view.children)


@pytest.mark.asyncio
async def test_refresh_button_rerenders_diagnostics():
    guild = MagicMock()
    view = panel.CleanupPolicyPanelView(MagicMock(), guild)
    it = _interaction()
    fake_embed = discord.Embed(title="diag")
    with patch.object(
        panel,
        "build_cleanup_diagnostics_embed",
        AsyncMock(return_value=fake_embed),
    ):
        await _btn(view, "cleanup_policy:refresh").callback(it)
    it.response.edit_message.assert_awaited_once()
    assert it.response.edit_message.call_args.kwargs["embed"] is fake_embed
    assert it.response.edit_message.call_args.kwargs["view"] is view


# ---------------------------------------------------------------------------
# Builder selects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scope_select_guild_opens_level_select():
    sel = panel._ScopeSelect(MagicMock())
    sel._values = ["guild"]
    it = _interaction()
    await sel.callback(it)
    sent_view = it.response.send_message.call_args.kwargs["view"]
    assert any(isinstance(c, panel._LevelSelect) for c in sent_view.children)


@pytest.mark.asyncio
async def test_level_select_previews_without_writing():
    sel = panel._LevelSelect(MagicMock(), "channel", 111, "#general")
    sel._values = ["Strict"]
    it = _interaction()
    with (
        patch.object(
            panel, "preview_cleanup_change", AsyncMock(return_value=_preview())
        ),
        patch.object(panel, "apply_cleanup_change", AsyncMock()) as applier,
    ):
        await sel.callback(it)
    it.response.send_message.assert_awaited_once()
    assert isinstance(
        it.response.send_message.call_args.kwargs["view"],
        panel._ConfirmApplyView,
    )
    applier.assert_not_called()  # dry-run only


# ---------------------------------------------------------------------------
# Confirm + apply
# ---------------------------------------------------------------------------


def _confirm_btn(view, label):
    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == label
    )


@pytest.mark.asyncio
async def test_apply_button_requires_admin():
    view = panel._ConfirmApplyView(MagicMock(), MagicMock(), _preview())
    it = _interaction(admin=False)
    with patch.object(panel, "apply_cleanup_change", AsyncMock()) as applier:
        await _confirm_btn(view, "✅ Apply").callback(it)
    applier.assert_not_called()
    it.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_button_admin_calls_service():
    guild = MagicMock()
    view = panel._ConfirmApplyView(MagicMock(), guild, _preview())
    it = _interaction(admin=True)
    with patch.object(panel, "apply_cleanup_change", AsyncMock()) as applier:
        await _confirm_btn(view, "✅ Apply").callback(it)
    applier.assert_awaited_once()
    args = applier.await_args.args
    # (guild, member, scope_type, scope_id, level)
    assert args[0] is guild
    assert args[2] == "channel"
    assert args[3] == 111
    assert args[4] == "Strict"
    it.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_button_surfaces_governance_error():
    view = panel._ConfirmApplyView(MagicMock(), MagicMock(), _preview())
    it = _interaction(admin=True)
    with patch.object(
        panel,
        "apply_cleanup_change",
        AsyncMock(side_effect=GovernanceError("nope")),
    ):
        await _confirm_btn(view, "✅ Apply").callback(it)
    it.response.edit_message.assert_awaited_once()
    assert "nope" in it.response.edit_message.call_args.kwargs["content"]


@pytest.mark.asyncio
async def test_cancel_button_writes_nothing():
    view = panel._ConfirmApplyView(MagicMock(), MagicMock(), _preview())
    it = _interaction(admin=True)
    with patch.object(panel, "apply_cleanup_change", AsyncMock()) as applier:
        await _confirm_btn(view, "✖ Cancel").callback(it)
    applier.assert_not_called()
    it.response.edit_message.assert_awaited_once()
    assert "Cancelled" in it.response.edit_message.call_args.kwargs["content"]
