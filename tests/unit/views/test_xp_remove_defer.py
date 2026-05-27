"""Regression tests for XP-role removal interaction ACK safety.

Pre-fix `_XpRemoveSelect.callback` did `db.set_role_xp_threshold`
(write) before `interaction.response.send_message`. Under DB latency
the 3-second window expired and the admin saw "Interaction Failed".
The fix wraps the write in `safe_defer(ephemeral=True)` so the reply
routes through `safe_followup` once the write completes.
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
    from views.roles.xp_roles_panel import _XpRemoveSelect

    select = MagicMock()
    select.values = ["Veteran"]
    select.parent = MagicMock()
    select.parent._refresh = AsyncMock()
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, *, ephemeral=False, **_kw):
        order.append(f"defer(ephemeral={ephemeral})")
        return True

    async def _set(*_a, **_kw):
        order.append("set_role_xp_threshold")

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
        patch("views.roles.xp_roles_panel.db") as mock_db,
        patch("views.roles.xp_roles_panel.invalidate_xp_threshold_roles") as inval,
    ):
        mock_db.set_role_xp_threshold = AsyncMock(side_effect=_set)
        await _XpRemoveSelect.callback(select, interaction)

    assert order == [
        "defer(ephemeral=True)",
        "set_role_xp_threshold",
        "followup",
    ], order
    defer.assert_awaited_once()
    inval.assert_called_once_with(99)
    select.parent._refresh.assert_awaited_once()
    interaction.response.send_message.assert_not_called()
