"""skill_service — available-point math, allocate guards, respec coin sink."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from services import skill_service as ss


def _patch_level(level: int):
    return patch.object(
        ss.game_xp_service,
        "level_info",
        AsyncMock(return_value=(level, 0, 100)),
    )


def _patch_skills(alloc: dict[str, int]):
    return patch.object(ss.db, "get_skills", AsyncMock(return_value=dict(alloc)))


@pytest.mark.asyncio
async def test_available_points_is_capped_level_minus_spent():
    # level 8, nothing spent → 8 available (under the soft cap).
    with _patch_level(8), _patch_skills({}):
        assert await ss.available_points(1, 2) == 8
    # level 30, 5 spent → min(30, 20) − 5 = 15 (the soft cap bites).
    with _patch_level(30), _patch_skills({"mining": 5}):
        assert await ss.available_points(1, 2) == 15
    # over-spent (cap lowered later) floors at 0, never negative.
    with _patch_level(1), _patch_skills({"mining": 5}):
        assert await ss.available_points(1, 2) == 0


@pytest.mark.asyncio
async def test_allocate_rejects_unknown_branch():
    with _patch_level(10), _patch_skills({}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.allocate(1, 2, "digging")
    assert not result.ok
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_allocate_rejects_nonpositive_amount():
    with _patch_level(10), _patch_skills({}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.allocate(1, 2, "mining", 0)
    assert not result.ok
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_allocate_rejects_over_per_branch_cap():
    # already at the per-branch cap.
    with _patch_level(40), _patch_skills({"mining": ss.skills.PER_BRANCH_CAP}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.allocate(1, 2, "mining", 1)
    assert not result.ok
    assert "caps at" in result.message
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_allocate_rejects_over_budget():
    # level 2 ⇒ 2 available; asking for 3.
    with _patch_level(2), _patch_skills({}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.allocate(1, 2, "mining", 3)
    assert not result.ok
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_allocate_persists_absolute_total_on_success():
    with _patch_level(10), _patch_skills({"mining": 2}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.allocate(1, 2, "mining", 3)
    assert result.ok
    # Absolute new total (2 + 3 = 5), not a delta.
    setp.assert_awaited_once_with(2, 1, "mining", 5)


def test_respec_cost_scales_with_level():
    assert ss.respec_cost(0) == ss.RESPEC_BASE_COST
    assert ss.respec_cost(10) == ss.RESPEC_BASE_COST + 10 * ss.RESPEC_COST_PER_LEVEL


@pytest.mark.asyncio
async def test_respec_with_nothing_allocated_is_a_noop():
    with _patch_level(5), _patch_skills({}):
        result = await ss.respec(1, 2)
    assert not result.ok


@asynccontextmanager
async def _fake_txn():
    yield object()  # the conn is never really used (debit/set are mocked)


@pytest.mark.asyncio
async def test_respec_debits_and_clears_every_branch():
    alloc = {"mining": 4, "combat": 3}
    with _patch_level(6), _patch_skills(alloc):
        with (
            patch.object(ss.db, "transaction", _fake_txn),
            patch.object(
                ss.economy_service,
                "debit_in_txn",
                AsyncMock(return_value=500),
            ) as debit,
            patch.object(
                ss.db,
                "set_skill_points",
                AsyncMock(),
            ) as setp,
            patch.object(ss.bus, "emit", AsyncMock()) as emit,
        ):
            result = await ss.respec(1, 2)
    assert result.ok
    assert result.new_balance == 500
    debit.assert_awaited_once()
    # cost = base + 6×per-level.
    assert debit.await_args.args[3] == ss.respec_cost(6)
    # every allocated branch cleared to 0.
    cleared = {call.args[2] for call in setp.await_args_list}
    assert cleared == {"mining", "combat"}
    assert all(call.args[3] == 0 for call in setp.await_args_list)
    emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_respec_insufficient_funds_does_not_clear():
    alloc = {"mining": 4}
    with _patch_level(6), _patch_skills(alloc):
        with (
            patch.object(ss.db, "transaction", _fake_txn),
            patch.object(
                ss.economy_service,
                "debit_in_txn",
                AsyncMock(
                    side_effect=ss.economy_service.InsufficientFundsError("broke")
                ),
            ),
            patch.object(
                ss.db,
                "get_coins",
                AsyncMock(return_value=10),
            ),
            patch.object(ss.db, "set_skill_points", AsyncMock()) as setp,
        ):
            result = await ss.respec(1, 2)
    assert not result.ok
    setp.assert_not_called()


# --- Slice E: single-branch respec ------------------------------------------


def test_respec_branch_cost_is_cheaper_than_full_and_scales():
    assert ss.respec_branch_cost(0) == ss.RESPEC_BRANCH_BASE_COST
    assert (
        ss.respec_branch_cost(10)
        == ss.RESPEC_BRANCH_BASE_COST + 10 * ss.RESPEC_BRANCH_COST_PER_LEVEL
    )
    # A single-branch respec must always cost less than the full one.
    for level in (0, 5, 20, 40):
        assert ss.respec_branch_cost(level) < ss.respec_cost(level)


@pytest.mark.asyncio
async def test_respec_branch_rejects_unknown_branch():
    with _patch_level(5), _patch_skills({"mining": 3}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.respec_branch(1, 2, "digging")
    assert not result.ok
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_respec_branch_with_no_points_in_branch_is_a_noop():
    with _patch_level(5), _patch_skills({"mining": 3}):
        with patch.object(ss.db, "set_skill_points", AsyncMock()) as setp:
            result = await ss.respec_branch(1, 2, "combat")
    assert not result.ok
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_respec_branch_debits_and_clears_only_that_branch():
    alloc = {"mining": 4, "combat": 3}
    with _patch_level(6), _patch_skills(alloc):
        with (
            patch.object(ss.db, "transaction", _fake_txn),
            patch.object(
                ss.economy_service,
                "debit_in_txn",
                AsyncMock(return_value=420),
            ) as debit,
            patch.object(
                ss.db,
                "set_skill_points",
                AsyncMock(),
            ) as setp,
            patch.object(ss.bus, "emit", AsyncMock()) as emit,
        ):
            result = await ss.respec_branch(1, 2, "mining")
    assert result.ok
    assert result.new_balance == 420
    assert debit.await_args.args[3] == ss.respec_branch_cost(6)
    # Only "mining" cleared (to 0) — "combat" stays untouched.
    setp.assert_awaited_once()
    assert setp.await_args.args[:4] == (2, 1, "mining", 0)
    emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_respec_branch_insufficient_funds_does_not_clear():
    with _patch_level(6), _patch_skills({"mining": 4}):
        with (
            patch.object(ss.db, "transaction", _fake_txn),
            patch.object(
                ss.economy_service,
                "debit_in_txn",
                AsyncMock(
                    side_effect=ss.economy_service.InsufficientFundsError("broke")
                ),
            ),
            patch.object(
                ss.db,
                "get_coins",
                AsyncMock(return_value=10),
            ),
            patch.object(ss.db, "set_skill_points", AsyncMock()) as setp,
        ):
            result = await ss.respec_branch(1, 2, "mining")
    assert not result.ok
    setp.assert_not_called()
