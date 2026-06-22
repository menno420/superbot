"""mining_workflow grid op (PR 3) — the unified ``dig`` (move + mine) + reseed_world.

Owner model (post-#1281): every dig is locomotion — it moves you into the adjacent
cell AND mines that cell.  Pins: lateral digs move + mine the destination, a blocked
vertical dig reports the light-gate hint with no loot, a down-dig records the depth,
and a rich cell's featured ore carries through.  DB writes are mocked; the no-op
transaction mirrors test_mining_workflow_characterization.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from services import mining_workflow
from utils.mining import grid

# Reads every dig path needs up front (position, depth, gear, skills); loot paths
# additionally read inventory + the world seed.  Per-test overrides layer on top.
_BASE_READS = dict(
    get_position=lambda: AsyncMock(return_value=(0, 0)),
    get_depth=lambda: AsyncMock(return_value=0),
    get_equipment=lambda: AsyncMock(return_value={}),
    get_skills=lambda: AsyncMock(return_value={}),
    get_mining_inventory=lambda: AsyncMock(return_value={}),
    get_world_seed=lambda: AsyncMock(return_value=123),
    # Energy fuel: (0, 0) settles to a full bar (epoch-0 timestamp), so digs are
    # never energy-blocked in these move/loot tests; set_energy is a no-op write.
    get_energy=lambda: AsyncMock(return_value=(0, 0)),
    set_energy=lambda: AsyncMock(),
)


def _reads(**overrides: object) -> dict[str, object]:
    base = {name: factory() for name, factory in _BASE_READS.items()}
    base.update(overrides)
    return base


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
# dig — lateral (move + mine the destination)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dig_lateral_moves_into_cell_and_mines_it():
    set_position = AsyncMock()
    update_mining_item = AsyncMock()
    mark_discovered = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        **_reads(
            set_position=set_position,
            update_mining_item=update_mining_item,
            mark_discovered=mark_discovered,
        ),
    ):
        result = await mining_workflow.dig(7, 99, grid.NORTH)

    assert result.moved is True
    assert (result.x, result.y, result.depth) == (0, 1, 0)  # North = +y
    assert result.found is not None and result.amount >= 1
    set_position.assert_awaited_once_with("7", 99, 0, 1, conn=ANY)
    update_mining_item.assert_awaited_once()
    # Discovery is marked on the DESTINATION cell.
    mark_discovered.assert_awaited_once_with("7", 99, 0, 0, 1, conn=ANY)


@pytest.mark.asyncio
async def test_dig_unknown_direction_does_nothing():
    set_position = AsyncMock()
    update_mining_item = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        **_reads(
            get_position=AsyncMock(return_value=(2, 3)),
            set_position=set_position,
            update_mining_item=update_mining_item,
            mark_discovered=AsyncMock(),
        ),
    ):
        result = await mining_workflow.dig(7, 99, "sideways")

    assert result.moved is False
    assert result.found is None and result.amount == 0
    set_position.assert_not_awaited()
    update_mining_item.assert_not_awaited()


# ---------------------------------------------------------------------------
# dig — vertical (depth band)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dig_down_blocked_without_light_reports_hint_and_no_loot():
    # Empty gear + no skills ⇒ depth_access 0 ⇒ world.descend stays put.
    set_depth = AsyncMock()
    update_mining_item = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        **_reads(
            set_depth=set_depth,
            update_mining_item=update_mining_item,
            mark_discovered=AsyncMock(),
        ),
    ):
        result = await mining_workflow.dig(7, 99, grid.DOWN)

    assert result.moved is False
    assert result.hint is not None
    assert result.found is None
    set_depth.assert_not_awaited()
    update_mining_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_dig_down_with_light_descends_mines_and_records_depth():
    set_depth = AsyncMock()
    update_mining_item = AsyncMock()
    mark_discovered = AsyncMock()
    record_depth = AsyncMock(return_value=True)
    with (
        patch.multiple(
            "services.mining_workflow.db",
            **_reads(
                get_position=AsyncMock(return_value=(1, 1)),
                set_depth=set_depth,
                update_mining_item=update_mining_item,
                mark_discovered=mark_discovered,
                record_depth=record_depth,
            ),
        ),
        patch("services.mining_workflow.world.descend", return_value=1),
    ):
        result = await mining_workflow.dig(7, 99, grid.DOWN)

    assert result.moved is True
    assert result.depth == 1
    assert result.found is not None
    set_depth.assert_awaited_once_with("7", 99, 1, conn=ANY)
    # Mines + reveals the destination cell at the NEW depth.
    mark_discovered.assert_awaited_once_with("7", 99, 1, 1, 1, conn=ANY)
    update_mining_item.assert_awaited_once()
    record_depth.assert_awaited_once()


@pytest.mark.asyncio
async def test_dig_up_at_surface_does_nothing():
    set_depth = AsyncMock()
    update_mining_item = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        **_reads(
            set_depth=set_depth,
            update_mining_item=update_mining_item,
            mark_discovered=AsyncMock(),
        ),
    ):
        result = await mining_workflow.dig(7, 99, grid.UP)

    assert result.moved is False
    set_depth.assert_not_awaited()
    update_mining_item.assert_not_awaited()


# ---------------------------------------------------------------------------
# dig — cell content carries through
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dig_rich_cell_features_its_ore_and_sets_a_note():
    rich = grid.Cell(0, 1, 0, grid.CellFeature.RICH, "gold", 2.0)
    with (
        patch.multiple(
            "services.mining_workflow.db",
            **_reads(
                set_position=AsyncMock(),
                update_mining_item=AsyncMock(),
                mark_discovered=AsyncMock(),
            ),
        ),
        patch("services.mining_workflow.grid.cell_at", return_value=rich),
    ):
        result = await mining_workflow.dig(7, 99, grid.NORTH)

    assert result.found == "gold"  # the rich vein's featured ore
    assert result.cell_note is not None


# ---------------------------------------------------------------------------
# energy — the frequency brake (2026-06-22)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dig_blocked_when_out_of_energy():
    """0 energy as of a far-future timestamp ⇒ no regen ⇒ blocked, no writes."""
    set_position = AsyncMock()
    update_mining_item = AsyncMock()
    set_energy = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        **_reads(
            get_energy=AsyncMock(return_value=(0, 9_999_999_999)),
            set_position=set_position,
            update_mining_item=update_mining_item,
            set_energy=set_energy,
            mark_discovered=AsyncMock(),
        ),
    ):
        result = await mining_workflow.dig(7, 99, grid.NORTH)

    assert result.moved is False
    assert result.found is None and result.amount == 0
    assert result.hint is not None and "energy" in result.hint.lower()
    set_position.assert_not_awaited()
    update_mining_item.assert_not_awaited()
    set_energy.assert_not_awaited()


@pytest.mark.asyncio
async def test_dig_spends_energy_in_the_transaction():
    set_energy = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        **_reads(
            get_energy=AsyncMock(return_value=(10, 9_999_999_999)),  # 10, no regen
            set_position=AsyncMock(),
            update_mining_item=AsyncMock(),
            set_energy=set_energy,
            mark_discovered=AsyncMock(),
        ),
    ):
        result = await mining_workflow.dig(7, 99, grid.NORTH)

    assert result.moved is True
    # one dig debits one energy (10 → 9), persisted on the conn.
    set_energy.assert_awaited_once()
    assert set_energy.await_args.args[2] == 9


@pytest.mark.asyncio
async def test_use_ration_restores_energy_and_consumes_it():
    update_mining_item = AsyncMock()
    set_energy = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_mining_inventory=AsyncMock(return_value={"ration": 2}),
        get_energy=AsyncMock(return_value=(20, 9_999_999_999)),  # 20, no regen
        update_mining_item=update_mining_item,
        set_energy=set_energy,
    ):
        result = await mining_workflow.use_item(7, 99, "ration")

    assert result.ok is True
    update_mining_item.assert_awaited_once_with("7", 99, "ration", -1, conn=ANY)
    set_energy.assert_awaited_once()
    assert set_energy.await_args.args[2] == 45  # 20 + 25 ration restore


@pytest.mark.asyncio
async def test_use_food_at_full_energy_is_refused():
    update_mining_item = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_mining_inventory=AsyncMock(return_value={"energy drink": 1}),
        get_energy=AsyncMock(return_value=(60, 0)),  # already full
        update_mining_item=update_mining_item,
        set_energy=AsyncMock(),
    ):
        result = await mining_workflow.use_item(7, 99, "energy drink")

    assert result.ok is False
    update_mining_item.assert_not_awaited()  # the item is NOT wasted


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
