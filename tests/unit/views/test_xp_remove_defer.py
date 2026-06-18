"""Regression tests for XP-role removal interaction ACK safety.

Pre-fix the removal callback did the threshold write before
`interaction.response.send_message`. Under DB latency the 3-second
window expired and the admin saw "Interaction Failed". The fix wraps
the write in `safe_defer(ephemeral=True)` so the reply routes through
`safe_followup` once the write completes. (PR5 switched the write from
`set_role_xp_threshold` to the field-specific `clear_role_xp_threshold`;
Batch 3 (RS06) moved the clear behind the audited
`role_automation.clear_xp_threshold` seam; 2026-06-18 retired the bespoke
`_XpRemoveSelect` onto the shared `PaginatedSelectView` so the callback is
now `XpRolesPanel._remove_threshold`; the ACK ordering is unchanged.)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


async def test_xp_remove_select_defers_ephemeral_before_db_write():
    from views.roles.xp_roles_panel import XpRolesPanel

    panel = MagicMock()
    panel._rerender = AsyncMock()
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, *, ephemeral=False, **_kw):
        order.append(f"defer(ephemeral={ephemeral})")
        return True

    async def _clear(*_a, **_kw):
        order.append("clear_xp_threshold")
        return "mutation-id"

    async def _followup(*_a, **_kw):
        order.append("followup")
        return MagicMock()

    with (
        patch(
            "views.roles.xp_roles_panel.safe_defer",
            AsyncMock(side_effect=_defer),
        ) as defer,
        patch(
            "views.roles.xp_roles_panel.safe_followup",
            AsyncMock(side_effect=_followup),
        ),
        patch(
            "views.roles.xp_roles_panel.role_automation.clear_xp_threshold",
            AsyncMock(side_effect=_clear),
        ) as clear,
        patch("views.roles.xp_roles_panel.invalidate_xp_threshold_roles") as inval,
    ):
        await XpRolesPanel._remove_threshold(panel, interaction, ["Veteran"])

    assert order == [
        "defer(ephemeral=True)",
        "clear_xp_threshold",
        "followup",
    ], order
    assert clear.await_args.kwargs["guild_id"] == 99
    assert clear.await_args.kwargs["role_name"] == "Veteran"
    assert clear.await_args.kwargs["actor_id"] == 1
    defer.assert_awaited_once()
    inval.assert_called_once_with(99)
    panel._rerender.assert_awaited_once()
    interaction.response.send_message.assert_not_called()
