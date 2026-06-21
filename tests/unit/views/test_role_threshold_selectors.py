"""Selector-driven time/XP threshold config (server-management PR6 + P0C).

The free-text role-name modal is replaced by a role picker → numeric modal, so a
persisted threshold always references a role that exists (capturing its id + name
snapshot).  Pins: the modals persist ``role_id`` + ``display_name``; the stale
helper flags a row whose role can no longer be resolved; and the Time panel's
**🧹 Clear Missing** button bulk-clears those stale rows through the audited seam.

**2026-06-21:** the hardcoded ``_DEFAULT_THRESHOLDS`` tier names + the
``_ensure_defaults`` seed routine were removed (owner directive — roles load
dynamically from the server now).  The old "Seed Defaults" button is gone; the
**Clear Missing** purge replaces it, and is covered here.

**P0C (2026-06-08):** every threshold write now routes through the audited
``services.role_automation.set_{time,xp}_threshold`` seam (write + audit emit,
and the XP path also invalidates the XP-threshold cache) instead of calling
``utils.db.roles.set_role_*`` directly — so these tests assert the *seam* call
(with its ``actor_id``), and the drift fence
``tests/unit/invariants/test_no_direct_role_threshold_writes.py`` keeps it that
way.  The ``role_id`` capture / staleness behaviour is unchanged.
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
async def test_clear_missing_button_clears_only_stale_rows():
    """The Time panel's "🧹 Clear Missing" button bulk-clears thresholds whose
    role no longer resolves — routing each removal through the audited clear
    seam with ``actor_id`` = the clicking user — and leaves resolvable rows
    untouched.  (Replaces the removed hardcoded-defaults "Seed Defaults" path.)
    """
    from views.roles.time_roles_panel import TimeRolesPanel

    rows = [
        {"role_id": 1, "role_name": "Ghost", "days_required": 7},
        {"role_id": 2, "role_name": "Veteran", "days_required": 30},
    ]

    def _resolve(_guild, *, name=None, role_id=None):
        # Only role_id=2 (Veteran) still resolves; Ghost (id=1) is stale.
        return SimpleNamespace(id=2, name="Veteran") if role_id == 2 else None

    ctx = MagicMock()
    ctx.guild.id = 99
    panel = TimeRolesPanel(ctx)
    panel.message = None  # _rerender no-ops without a bound message
    interaction = _interaction()
    with (
        patch(
            "views.roles.time_roles_panel.db.get_role_thresholds",
            new=AsyncMock(return_value=rows),
        ),
        patch(
            "views.roles.time_roles_panel.resources.resolve_role",
            side_effect=_resolve,
        ),
        patch(
            "views.roles.time_roles_panel.role_automation.clear_time_threshold",
            new_callable=AsyncMock,
        ) as seam,
        patch("views.roles.time_roles_panel.invalidate_xp_threshold_roles"),
        patch("views.roles.time_roles_panel.safe_defer", AsyncMock(return_value=True)),
    ):
        # The @discord.ui.button decorator leaves the coroutine on the class.
        await TimeRolesPanel.clear_missing_btn(panel, interaction, MagicMock())
    # Only the stale row is cleared — through the audited seam, actor = clicker.
    seam.assert_awaited_once_with(
        guild_id=99,
        role_name="Ghost",
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


def test_hardcoded_defaults_and_ensure_defaults_are_removed():
    """Regression guard for the owner directive: the hardcoded German/Minecraft
    tier names (``_DEFAULT_THRESHOLDS``) and the ``_ensure_defaults`` seed
    routine must NOT come back — roles load dynamically from the server now.
    """
    import views.roles._helpers as helpers

    assert not hasattr(helpers, "_DEFAULT_THRESHOLDS")
    assert not hasattr(helpers, "_ensure_defaults")


def test_role_presets_are_creation_only_and_drop_old_tier_names():
    """``ROLE_PRESETS`` exists (a few quick-create names) and never re-introduces
    the old hardcoded tier names.
    """
    from views.roles._helpers import ROLE_PRESETS

    names = {p.name for p in ROLE_PRESETS}
    assert names, "expected a few creation presets"
    # The old hardcoded tier names must not reappear as presets.
    assert not (names & {"Neu", "Normal", "Iron", "Gold", "Diamand", "Netherite", "Beacon"})


@pytest.mark.asyncio
async def test_role_create_panel_create_routes_pending_through_lifecycle():
    """The creation menu's ✅ Create stages the picked preset name/colour/hoist
    and creates the role through the audited RoleLifecycleService.
    """
    import discord

    from services.lifecycle import SUCCESS
    from views.roles.creation_panel import RoleCreatePanel

    ctx = MagicMock()
    ctx.guild.id = 99
    panel = RoleCreatePanel(ctx)
    panel.pending_name = "Moderator"
    panel.pending_color = discord.Color(0x3498DB)
    panel.pending_hoist = True

    interaction = _interaction()
    interaction.response.edit_message = AsyncMock()
    interaction.message = MagicMock()

    fake_result = SimpleNamespace(
        outcome=SUCCESS,
        steps=[SimpleNamespace(target_name="Moderator", target_id=999)],
        first_error=None,
    )
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=fake_result)
    with patch("views.roles.creation_panel.RoleLifecycleService", return_value=svc):
        await RoleCreatePanel.create_btn(panel, interaction, MagicMock())

    svc.apply.assert_awaited_once()
    req = svc.apply.await_args.args[1]
    assert req.operation == "create"
    assert req.name == "Moderator"
    assert req.hoist is True
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_role_create_panel_create_requires_a_name():
    """✅ Create with nothing staged tells the operator to pick/Custom first and
    never touches the lifecycle service.
    """
    from views.roles.creation_panel import RoleCreatePanel

    ctx = MagicMock()
    ctx.guild.id = 99
    panel = RoleCreatePanel(ctx)  # pending_name is None
    interaction = _interaction()
    with patch("views.roles.creation_panel.RoleLifecycleService") as svc:
        await RoleCreatePanel.create_btn(panel, interaction, MagicMock())
    svc.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
