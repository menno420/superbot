"""game_xp_service — award table, soft cap, shared-level derivation, events."""

from __future__ import annotations

from unittest.mock import ANY, AsyncMock, patch

import pytest

from core.events_catalogue import KNOWN_EVENTS
from services import game_xp_service as gx
from utils import db


def test_events_are_catalogued():
    assert gx.EVT_GAME_XP_AWARDED in KNOWN_EVENTS
    assert gx.EVT_GAME_LEVEL_UP in KNOWN_EVENTS


def test_award_table_v1():
    assert gx.xp_for_action("mine") == 3
    assert gx.xp_for_action("mine", depth=3) == 6  # depth-scaled
    assert gx.xp_for_action("harvest") == 2
    assert gx.xp_for_action("harvest", depth=3) == 2  # NOT depth-scaled
    assert gx.xp_for_action("explore", depth=2) == 6
    assert gx.xp_for_action("depth_record") == 25
    assert gx.xp_for_action("craft") == 8
    assert gx.xp_for_action("quick_craft") == 8
    assert gx.xp_for_action("repair") == 3
    # Money moves never award XP — selling/buying can't farm the track.
    assert gx.xp_for_action("sell") == 0
    assert gx.xp_for_action("buy") == 0


@pytest.mark.asyncio
async def test_zero_xp_action_returns_none_without_writes():
    with patch.object(gx.db, "add_game_xp", AsyncMock()) as add:
        result = await gx.award(1, 2, game="mining", action="sell")
    assert result is None
    add.assert_not_called()


def _db_patches(*, day_xp=0, day_matches=True, total_before=0, game_total=10):
    import datetime

    today = datetime.datetime.now(datetime.timezone.utc).date()
    row = {
        "xp": 0,
        "day": today if day_matches else None,
        "day_xp": day_xp,
    }
    return (
        patch.object(
            gx.db,
            "get_game_xp_row",
            AsyncMock(return_value=row),
        ),
        patch.object(
            gx.db,
            "get_total_xp",
            AsyncMock(return_value=total_before),
        ),
        patch.object(
            gx.db,
            "add_game_xp",
            AsyncMock(return_value=game_total),
        ),
    )


@pytest.mark.asyncio
async def test_award_full_rate_under_the_daily_cap():
    p_row, p_total, p_add = _db_patches(day_xp=0)
    with p_row, p_total, p_add as add:
        result = await gx.award(99, 1, game="mining", action="mine", depth=2)
    assert result is not None
    assert result.amount == 5  # 3 + depth 2, full rate
    assert add.await_args.args[3] == 5


@pytest.mark.asyncio
async def test_award_capped_rate_past_the_daily_cap_floors_at_one():
    p_row, p_total, p_add = _db_patches(day_xp=gx.DAILY_SOFT_CAP)
    with p_row, p_total, p_add:
        big = await gx.award(99, 1, game="mining", action="depth_record")
        small = await gx.award(99, 1, game="crafting", action="repair")
    assert big is not None and big.amount == int(25 * gx.CAPPED_RATE)  # 6
    assert small is not None and small.amount == 1  # floor 1, never zero


@pytest.mark.asyncio
async def test_day_rollover_resets_the_cap():
    p_row, p_total, p_add = _db_patches(
        day_xp=gx.DAILY_SOFT_CAP * 2,
        day_matches=False,  # yesterday's counter
    )
    with p_row, p_total, p_add:
        result = await gx.award(99, 1, game="mining", action="mine")
    assert result is not None
    assert result.amount == 3  # full rate again


@pytest.mark.asyncio
async def test_shared_level_derivation_matches_level_progress():
    # Level 0 needs 100 XP; start at 98, award 3 → crosses into level 1.
    p_row, p_total, p_add = _db_patches(total_before=98)
    with p_row, p_total, p_add:
        result = await gx.award(99, 1, game="mining", action="mine")
    assert result is not None
    assert result.shared_total == 101
    expected_level, _, _ = db.level_progress(101)
    assert result.level == expected_level == 1
    assert result.leveled_up is True
    assert "Level 1" in result.note


@pytest.mark.asyncio
async def test_award_passes_the_workflow_conn_through():
    sentinel = object()
    p_row, p_total, p_add = _db_patches()
    with p_row as row, p_total as total, p_add as add:
        await gx.award(99, 1, game="mining", action="mine", conn=sentinel)
    assert row.await_args.kwargs["conn"] is sentinel
    assert total.await_args.kwargs["conn"] is sentinel
    assert add.await_args.kwargs["conn"] is sentinel


@pytest.mark.asyncio
async def test_emit_award_events_emits_both_on_level_up():
    award = gx.GameXpAward(
        guild_id=99,
        user_id=1,
        game="mining",
        action="mine",
        amount=3,
        game_total=3,
        shared_total=101,
        level=1,
        leveled_up=True,
    )
    with patch.object(gx.bus, "emit", AsyncMock()) as emit:
        await gx.emit_award_events(award)
    events = [c.args[0] for c in emit.await_args_list]
    assert events == [gx.EVT_GAME_XP_AWARDED, gx.EVT_GAME_LEVEL_UP]


@pytest.mark.asyncio
async def test_emit_award_events_skips_level_up_when_not_crossed():
    award = gx.GameXpAward(
        guild_id=99,
        user_id=1,
        game="mining",
        action="mine",
        amount=3,
        game_total=3,
        shared_total=3,
        level=0,
        leveled_up=False,
    )
    with patch.object(gx.bus, "emit", AsyncMock()) as emit:
        await gx.emit_award_events(award)
    emit.assert_awaited_once_with(
        gx.EVT_GAME_XP_AWARDED,
        guild_id=99,
        user_id=1,
        game="mining",
        action="mine",
        amount=3,
        total=ANY,
    )
