"""mining_workflow grid ops (PR 3) — move / mine_here / reseed_world.

Pins the workflow seam: every successful move marks fog-of-war discovery, a
blocked vertical move reports the light-gate hint, and ``mine_here`` folds the
seed-deterministic cell into the loot.  DB writes are mocked; the no-op
transaction mirrors test_mining_workflow_characterization.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from services import mining_workflow
from utils.mining import grid


@pytest.fixture(autouse=True)
def _null_txn_and_xp():
    """db.transaction() → no-op; game-XP awards → no-op (loot/move are the point)."""

    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="conn")

    with (
        patch("services.mining_workflow.db.transaction", _txn),
        patch(
            "services.mining_workflow.game_xp_service.award",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.mining_workflow.game_xp_service.emit_award_events",
            AsyncMock(),
        ),
    ):
        yield


# ---------------------------------------------------------------------------
# move — lateral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_move_lateral_updates_position_and_marks_both_cells():
    set_position = AsyncMock()
    mark_discovered = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_position=AsyncMock(return_value=(0, 0)),
        get_depth=AsyncMock(return_value=1),
        set_position=set_position,
        mark_discovered=mark_discovered,
    ):
        result = await mining_workflow.move(7, 99, grid.NORTH)

    assert result.moved is True
    assert (result.x, result.y, result.depth) == (0, 1, 1)
    set_position.assert_awaited_once()
    # Both the origin and the destination are revealed (look-back fog fix).
    assert mark_discovered.await_count == 2


@pytest.mark.asyncio
async def test_move_unknown_direction_does_not_move():
    set_position = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_position=AsyncMock(return_value=(2, 3)),
        get_depth=AsyncMock(return_value=0),
        set_position=set_position,
        mark_discovered=AsyncMock(),
    ):
        result = await mining_workflow.move(7, 99, "sideways")
    assert result.moved is False
    set_position.assert_not_awaited()


# ---------------------------------------------------------------------------
# move — vertical (depth band)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_move_down_blocked_without_light_reports_hint():
    # Empty gear + no skills ⇒ depth_access 0 ⇒ world.descend stays put.
    set_depth = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_position=AsyncMock(return_value=(0, 0)),
        get_depth=AsyncMock(return_value=0),
        get_equipment=AsyncMock(return_value={}),
        get_skills=AsyncMock(return_value={}),
        set_depth=set_depth,
        mark_discovered=AsyncMock(),
    ):
        result = await mining_workflow.move(7, 99, grid.DOWN)
    assert result.moved is False
    assert result.hint is not None
    set_depth.assert_not_awaited()


@pytest.mark.asyncio
async def test_move_down_with_light_descends_and_marks_cell():
    set_depth = AsyncMock()
    mark_discovered = AsyncMock()
    with (
        patch.multiple(
            "services.mining_workflow.db",
            get_position=AsyncMock(return_value=(1, 1)),
            get_depth=AsyncMock(return_value=0),
            get_equipment=AsyncMock(return_value={}),
            get_skills=AsyncMock(return_value={}),
            set_depth=set_depth,
            record_depth=AsyncMock(return_value=False),
            mark_discovered=mark_discovered,
        ),
        patch(
            "services.mining_workflow.world.descend",
            return_value=1,
        ),
    ):
        result = await mining_workflow.move(7, 99, grid.DOWN)
    assert result.moved is True
    assert result.depth == 1
    set_depth.assert_awaited_once_with("7", 99, 1, conn=ANY)
    mark_discovered.assert_awaited_once_with("7", 99, 1, 1, 1, conn=ANY)


@pytest.mark.asyncio
async def test_move_up_at_surface_does_not_move():
    set_depth = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_position=AsyncMock(return_value=(0, 0)),
        get_depth=AsyncMock(return_value=0),
        set_depth=set_depth,
        mark_discovered=AsyncMock(),
    ):
        result = await mining_workflow.move(7, 99, grid.UP)
    assert result.moved is False
    set_depth.assert_not_awaited()


# ---------------------------------------------------------------------------
# mine_here
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mine_here_grants_loot_and_marks_current_cell():
    update_mining_item = AsyncMock()
    mark_discovered = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_mining_inventory=AsyncMock(return_value={}),
        get_equipment=AsyncMock(return_value={}),
        get_depth=AsyncMock(return_value=0),
        get_position=AsyncMock(return_value=(0, 0)),
        get_world_seed=AsyncMock(return_value=123),
        update_mining_item=update_mining_item,
        mark_discovered=mark_discovered,
    ):
        result = await mining_workflow.mine_here(5, 42)

    assert isinstance(result, mining_workflow.MineResult)
    assert result.amount >= 1
    update_mining_item.assert_awaited_once()
    mark_discovered.assert_awaited_once_with("5", 42, 0, 0, 0, conn=ANY)


@pytest.mark.asyncio
async def test_mine_here_rich_cell_sets_a_cell_note():
    # Force a RICH cell so the flavour note is deterministic.
    rich = grid.Cell(0, 0, 0, grid.CellFeature.RICH, "gold", 2.0)
    with (
        patch.multiple(
            "services.mining_workflow.db",
            get_mining_inventory=AsyncMock(return_value={}),
            get_equipment=AsyncMock(return_value={}),
            get_depth=AsyncMock(return_value=0),
            get_position=AsyncMock(return_value=(0, 0)),
            get_world_seed=AsyncMock(return_value=123),
            update_mining_item=AsyncMock(),
            mark_discovered=AsyncMock(),
        ),
        patch("services.mining_workflow.grid.cell_at", return_value=rich),
    ):
        result = await mining_workflow.mine_here(5, 42)
    assert result.found == "gold"
    assert result.cell_note is not None


# ---------------------------------------------------------------------------
# reseed_world
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reseed_world_persists_and_returns_seed():
    set_world_seed = AsyncMock()
    with patch("services.mining_workflow.db.set_world_seed", set_world_seed):
        result = await mining_workflow.reseed_world(99, 2024)
    assert result == 2024
    set_world_seed.assert_awaited_once_with(99, 2024)
