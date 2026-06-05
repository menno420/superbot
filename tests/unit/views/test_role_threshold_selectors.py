"""Selector-driven time/XP threshold config (server-management PR6).

The free-text role-name modal is replaced by a role picker → numeric modal, so a
persisted threshold always references a role that exists (capturing its id + name
snapshot).  Pins: the modals persist ``role_id`` + ``display_name``; the stale
helper flags a row whose role can no longer be resolved; and ``_ensure_defaults``
seeds only defaults whose role actually exists (no phantom-name rows).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_time_days_modal_persists_role_id_and_name():
    from views.roles.time_roles_panel import TimeDaysModal

    parent = MagicMock()
    parent._rerender = AsyncMock()
    modal = TimeDaysModal(parent, SimpleNamespace(id=100, name="Veteran"))
    modal.days = MagicMock(value="30")
    interaction = _interaction()
    with (
        patch("views.roles.time_roles_panel.db") as db,
        patch("views.roles.time_roles_panel.invalidate_xp_threshold_roles"),
        patch("views.roles.time_roles_panel.safe_defer", AsyncMock(return_value=True)),
    ):
        db.set_role_threshold = AsyncMock()
        await modal.on_submit(interaction)
    db.set_role_threshold.assert_awaited_once_with(
        99, "Veteran", 30, role_id=100, display_name="Veteran"
    )
    parent._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_time_days_modal_rejects_negative():
    from views.roles.time_roles_panel import TimeDaysModal

    modal = TimeDaysModal(MagicMock(), SimpleNamespace(id=1, name="X"))
    modal.days = MagicMock(value="-3")
    interaction = _interaction()
    with patch("views.roles.time_roles_panel.db") as db:
        db.set_role_threshold = AsyncMock()
        await modal.on_submit(interaction)
    db.set_role_threshold.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_level_modal_persists_role_id_and_name():
    from views.roles.xp_roles_panel import XpLevelModal

    parent = MagicMock()
    parent._rerender = AsyncMock()
    modal = XpLevelModal(parent, SimpleNamespace(id=200, name="Pro"))
    modal.level = MagicMock(value="5")
    modal.auto_assign = MagicMock(value="yes")
    interaction = _interaction()
    with (
        patch("views.roles.xp_roles_panel.db") as db,
        patch("views.roles.xp_roles_panel.invalidate_xp_threshold_roles"),
        patch("views.roles.xp_roles_panel.safe_defer", AsyncMock(return_value=True)),
    ):
        db.set_role_xp_threshold = AsyncMock()
        await modal.on_submit(interaction)
    db.set_role_xp_threshold.assert_awaited_once_with(
        99, "Pro", 5, True, role_id=200, display_name="Pro"
    )


def test_row_is_stale_by_role_id():
    from views.roles.time_roles_panel import _row_is_stale

    guild = MagicMock()
    with patch("views.roles.time_roles_panel.resources") as res:
        res.resolve_role.return_value = object()  # id resolves → fresh
        assert _row_is_stale(guild, {"role_id": 100, "role_name": "X"}) is False
        res.resolve_role.return_value = None  # id no longer resolves → stale
        assert _row_is_stale(guild, {"role_id": 100, "role_name": "X"}) is True


def test_row_is_stale_legacy_name_fallback():
    from views.roles.time_roles_panel import _row_is_stale

    guild = MagicMock()
    with patch("views.roles.time_roles_panel.resources") as res:
        res.resolve_role.return_value = None
        assert _row_is_stale(guild, {"role_id": None, "role_name": "Ghost"}) is True
        assert res.resolve_role.call_args.kwargs.get("name") == "Ghost"


@pytest.mark.asyncio
async def test_ensure_defaults_seeds_only_existing_roles():
    from views.roles._helpers import _DEFAULT_THRESHOLDS, _ensure_defaults

    existing_name = _DEFAULT_THRESHOLDS[0][0]

    def _resolve(_guild, *, name=None, role_id=None):
        if name == existing_name:
            return SimpleNamespace(id=500, name=name)
        return None

    guild = MagicMock()
    guild.id = 7
    with (
        patch("utils.db.get_role_thresholds", new=AsyncMock(return_value=[])),
        patch("utils.db.set_role_threshold", new=AsyncMock()) as setter,
        patch("core.runtime.resources.resolve_role", side_effect=_resolve),
    ):
        await _ensure_defaults(guild)
    # Only the one default whose role exists is seeded — with its captured id —
    # and the phantom-named defaults are skipped (no nonexistent-role rows).
    setter.assert_awaited_once()
    assert setter.await_args.args[0] == 7
    assert setter.await_args.kwargs == {"role_id": 500, "display_name": existing_name}


@pytest.mark.asyncio
async def test_ensure_defaults_noop_when_thresholds_exist():
    from views.roles._helpers import _ensure_defaults

    guild = MagicMock()
    guild.id = 7
    with (
        patch(
            "utils.db.get_role_thresholds",
            new=AsyncMock(return_value=[{"role_name": "X", "days_required": 1}]),
        ),
        patch("utils.db.set_role_threshold", new=AsyncMock()) as setter,
    ):
        await _ensure_defaults(guild)
    setter.assert_not_awaited()
