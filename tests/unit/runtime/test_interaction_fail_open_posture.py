"""RC-3 / ADR-004 — per-surface interaction fail-open vs fail-closed (wave PR4).

Default posture is fail-open (today's behavior).  Owner/mutating surfaces opt in
to fail-closed:
  * `PersistentView.FAIL_CLOSED_ON_MISSING_ANCHOR` (the anchor-ownership path), and
  * `interaction_router._FAIL_CLOSED_PREFIXES` (the governance-gate-throw path).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from core.runtime import interaction_router, persistent_views


def _fake_interaction(
    custom_id, *, guild_id=1, channel_id=2, user_id=10, ephemeral=False
):
    inter = MagicMock()
    inter.custom_id = custom_id
    inter.data = {"custom_id": custom_id}
    inter.guild_id = guild_id
    inter.channel_id = channel_id
    inter.user = MagicMock()
    inter.user.id = user_id
    inter.user.roles = []
    inter.channel = MagicMock(spec=discord.TextChannel)
    inter.channel.id = channel_id
    inter.channel.category_id = None
    inter.message = MagicMock()
    inter.message.id = 555
    # Explicit flags so the ephemeral short-circuit (private-message ownership) is
    # tested deterministically — a bare MagicMock would make .flags.ephemeral truthy.
    inter.message.flags = MagicMock(ephemeral=ephemeral)
    resp = MagicMock()
    resp.is_done.return_value = False
    resp.send_message = AsyncMock()
    inter.response = resp
    return inter


# ---- persistent_views: missing-anchor posture -----------------------------


class _OwnerPanel(persistent_views.PersistentView):
    SUBSYSTEM = "test_owner"
    FAIL_CLOSED_ON_MISSING_ANCHOR = True


class _PublicPanel(persistent_views.PersistentView):
    SUBSYSTEM = "test_public"
    # FAIL_CLOSED_ON_MISSING_ANCHOR defaults to False (today's behavior)


@pytest.mark.asyncio
async def test_missing_anchor_fail_closed_for_owner_panel(monkeypatch):
    from core.runtime import message_anchor_manager

    monkeypatch.setattr(
        message_anchor_manager,
        "get_by_message_id",
        AsyncMock(return_value=None),
    )
    inter = _fake_interaction("test_owner:x")
    assert await _OwnerPanel().interaction_check(inter) is False
    inter.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_anchor_fail_open_for_public_panel(monkeypatch):
    from core.runtime import message_anchor_manager

    monkeypatch.setattr(
        message_anchor_manager,
        "get_by_message_id",
        AsyncMock(return_value=None),
    )
    inter = _fake_interaction("test_public:x")
    assert await _PublicPanel().interaction_check(inter) is True
    inter.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_ephemeral_message_allowed_for_fail_closed_panel(monkeypatch):
    """An ephemeral message is private to its opener — ownership is implicit, so a
    fail-closed panel surfaced through an ephemeral help/nav path (e.g. /help →
    Roles, which renders RoleHubPanelView) must NOT deny its own opener.

    Regression for "This panel can no longer be verified — please re-open it."
    """
    from core.runtime import message_anchor_manager

    spy = AsyncMock(return_value=None)
    monkeypatch.setattr(message_anchor_manager, "get_by_message_id", spy)
    inter = _fake_interaction("test_owner:x", ephemeral=True)
    assert await _OwnerPanel().interaction_check(inter) is True
    inter.response.send_message.assert_not_awaited()
    spy.assert_not_awaited()  # ephemeral short-circuits before the anchor lookup


@pytest.mark.asyncio
async def test_anchor_owner_mismatch_still_denied(monkeypatch):
    """The existing ownership check is unchanged by the new flag."""
    from core.runtime import message_anchor_manager

    monkeypatch.setattr(
        message_anchor_manager,
        "get_by_message_id",
        AsyncMock(return_value={"user_id": 999}),
    )
    inter = _fake_interaction("test_public:x", user_id=10)
    assert await _PublicPanel().interaction_check(inter) is False


def test_role_hub_panel_opts_into_fail_closed():
    from cogs.role_cog import RoleHubPanelView

    assert RoleHubPanelView.FAIL_CLOSED_ON_MISSING_ANCHOR is True


def test_default_persistent_view_is_fail_open():
    assert persistent_views.PersistentView.FAIL_CLOSED_ON_MISSING_ANCHOR is False


# ---- interaction_router: governance-gate-throw posture --------------------


@pytest.fixture
def _restore_handlers():
    saved = dict(interaction_router._handlers)
    yield
    interaction_router._handlers.clear()
    interaction_router._handlers.update(saved)


@pytest.mark.asyncio
async def test_router_fail_closed_on_governance_throw(monkeypatch, _restore_handlers):
    import governance

    monkeypatch.setattr(
        governance,
        "get_visible_subsystems",
        AsyncMock(side_effect=RuntimeError("governance down")),
    )
    handler = AsyncMock()
    interaction_router.register("moderation", handler)  # a fail-closed prefix

    await interaction_router.dispatch(_fake_interaction("moderation:warn"))

    handler.assert_not_awaited()  # denied before the handler


@pytest.mark.asyncio
async def test_router_fail_open_on_governance_throw_public(
    monkeypatch,
    _restore_handlers,
):
    import governance
    from core.runtime import session_manager

    monkeypatch.setattr(
        governance,
        "get_visible_subsystems",
        AsyncMock(side_effect=RuntimeError("governance down")),
    )
    monkeypatch.setattr(
        session_manager,
        "get_or_create",
        AsyncMock(return_value=None),
    )
    handler = AsyncMock()
    interaction_router.register("economy", handler)  # NOT a fail-closed prefix

    await interaction_router.dispatch(_fake_interaction("economy:daily"))

    handler.assert_awaited_once()  # allowed (fail-open) despite governance throw


def test_fail_closed_prefix_set_covers_admin_surfaces():
    s = interaction_router._FAIL_CLOSED_PREFIXES
    for p in ("settings", "setup", "provisioning", "admin", "moderation", "role"):
        assert p in s
    assert "economy" not in s  # public/game surfaces stay fail-open
