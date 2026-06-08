"""Selector-driven time/XP threshold config (server-management PR6 + P0C).

The free-text role-name modal is replaced by a role picker → numeric modal, so a
persisted threshold always references a role that exists (capturing its id + name
snapshot).  Pins: the modals persist ``role_id`` + ``display_name``; the stale
helper flags a row whose role can no longer be resolved; and ``_ensure_defaults``
seeds only defaults whose role actually exists (no phantom-name rows).

**P0C (2026-06-08):** every threshold write now routes through the audited
``services.role_automation.set_{time,xp}_threshold`` seam (write + audit emit,
and the XP path also invalidates the XP-threshold cache) instead of calling
``utils.db.roles.set_role_*`` directly — so these tests assert the *seam* call
(with its ``actor_id``), and the drift fence
``tests/unit/invariants/test_no_direct_role_threshold_writes.py`` keeps it that
way.  The ``role_id`` capture / staleness / seed-existing-only behaviour is
unchanged.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user.id = 7
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_time_days_modal_routes_time_through_seam():
    from views.roles.time_roles_panel import TimeDaysModal

    parent = MagicMock()
    parent._rerender = AsyncMock()
    modal = TimeDaysModal(parent, SimpleNamespace(id=100, name="Veteran"))
    modal.days = MagicMock(value="30")
    interaction = _interaction()
    with (
        patch("views.roles.time_roles_panel.role_automation") as ra,
        patch("views.roles.time_roles_panel.invalidate_xp_threshold_roles"),
        patch("views.roles.time_roles_panel.safe_defer", AsyncMock(return_value=True)),
    ):
        ra.set_time_threshold = AsyncMock()
        await modal.on_submit(interaction)
    # Audited seam, id-first, with the acting user captured.
    ra.set_time_threshold.assert_awaited_once_with(
        guild_id=99,
        role_id=100,
        role_name="Veteran",
        days=30,
        actor_id=7,
    )
    parent._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_time_days_modal_rejects_negative():
    from views.roles.time_roles_panel import TimeDaysModal

    modal = TimeDaysModal(MagicMock(), SimpleNamespace(id=1, name="X"))
    modal.days = MagicMock(value="-3")
    interaction = _interaction()
    with patch("views.roles.time_roles_panel.role_automation") as ra:
        ra.set_time_threshold = AsyncMock()
        await modal.on_submit(interaction)
    ra.set_time_threshold.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_defaults_button_routes_through_seam():
    """The Time panel's "Seed Defaults" button seeds only defaults whose role
    exists, routing each write through the audited seam with ``actor_id`` = the
    clicking user.
    """
    from views.roles._helpers import _DEFAULT_THRESHOLDS
    from views.roles.time_roles_panel import TimeRolesPanel

    first_name, first_days = _DEFAULT_THRESHOLDS[0]

    def _resolve(_guild, *, name=None, role_id=None):
        return SimpleNamespace(id=808, name=first_name) if name == first_name else None

    ctx = MagicMock()
    ctx.guild.id = 99
    panel = TimeRolesPanel(ctx)
    panel.message = None  # _rerender no-ops without a bound message
    interaction = _interaction()
    with (
        patch(
            "views.roles.time_roles_panel.resources.resolve_role",
            side_effect=_resolve,
        ),
        patch(
            "views.roles.time_roles_panel.role_automation.set_time_threshold",
            new_callable=AsyncMock,
        ) as seam,
        patch("views.roles.time_roles_panel.safe_defer", AsyncMock(return_value=True)),
    ):
        # The @discord.ui.button decorator shadows the instance attr with a
        # Button; the original coroutine stays on the class.
        await TimeRolesPanel.reset_btn(panel, interaction, MagicMock())
    # Only the one existing default is seeded — through the seam, id-first.
    seam.assert_awaited_once_with(
        guild_id=99,
        role_id=808,
        role_name=first_name,
        days=first_days,
        actor_id=7,
    )


@pytest.mark.asyncio
async def test_xp_level_modal_routes_xp_through_seam():
    from views.roles.xp_roles_panel import XpLevelModal

    parent = MagicMock()
    parent._rerender = AsyncMock()
    modal = XpLevelModal(parent, SimpleNamespace(id=200, name="Pro"))
    modal.level = MagicMock(value="5")
    modal.auto_assign = MagicMock(value="yes")
    interaction = _interaction()
    with (
        patch("views.roles.xp_roles_panel.role_automation") as ra,
        patch("views.roles.xp_roles_panel.invalidate_xp_threshold_roles"),
        patch("views.roles.xp_roles_panel.safe_defer", AsyncMock(return_value=True)),
    ):
        ra.set_xp_threshold = AsyncMock()
        await modal.on_submit(interaction)
    ra.set_xp_threshold.assert_awaited_once_with(
        guild_id=99,
        role_id=200,
        role_name="Pro",
        level=5,
        actor_id=7,
        auto_assign=True,
    )


@pytest.mark.asyncio
async def test_role_automation_modal_routes_xp_through_seam_with_created_id():
    """After ``!createrole``, the offered XP-automation modal routes through the
    seam id-first — the created role's id is threaded in (closing the old
    name-only write that would orphan the tier on a later rename).
    """
    from views.roles.creation_panel import RoleAutomationModal

    parent_view = MagicMock()
    parent_view.children = []
    modal = RoleAutomationModal(MagicMock(), "Pro", parent_view, role_id=321)
    modal.level_threshold = MagicMock(value="5")
    modal.auto_assign_enabled = MagicMock(value="yes")
    interaction = _interaction()
    interaction.response.edit_message = AsyncMock()
    with (
        patch("views.roles.creation_panel.role_automation") as ra,
        patch("views.roles.creation_panel.invalidate_xp_threshold_roles"),
    ):
        ra.set_xp_threshold = AsyncMock()
        await modal.on_submit(interaction)
    ra.set_xp_threshold.assert_awaited_once_with(
        guild_id=99,
        role_id=321,
        role_name="Pro",
        level=5,
        actor_id=7,
        auto_assign=True,
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

    existing_name, existing_days = _DEFAULT_THRESHOLDS[0]

    def _resolve(_guild, *, name=None, role_id=None):
        if name == existing_name:
            return SimpleNamespace(id=500, name=name)
        return None

    guild = MagicMock()
    guild.id = 7
    with (
        patch("utils.db.get_role_thresholds", new=AsyncMock(return_value=[])),
        patch(
            "services.role_automation.set_time_threshold",
            new=AsyncMock(),
        ) as seam,
        patch("core.runtime.resources.resolve_role", side_effect=_resolve),
    ):
        await _ensure_defaults(guild)
    # Only the one default whose role exists is seeded — with its captured id,
    # through the audited seam, system-actored (no human behind a boot seed).
    seam.assert_awaited_once_with(
        guild_id=7,
        role_id=500,
        role_name=existing_name,
        days=existing_days,
        actor_id=None,
        actor_type="system",
    )


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
        patch(
            "services.role_automation.set_time_threshold",
            new=AsyncMock(),
        ) as seam,
    ):
        await _ensure_defaults(guild)
    seam.assert_not_awaited()
