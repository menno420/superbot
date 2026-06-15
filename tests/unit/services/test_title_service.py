"""title_service — context build, earned-gating, equip/unequip boundary."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import title_service as ts
from utils.mining import skills


def _patch_state(*, alloc=None, max_depth=0, level=0):
    """Patch the three progression reads build_context aggregates."""
    return (
        patch.object(ts.db, "get_skills", AsyncMock(return_value=dict(alloc or {}))),
        patch.object(ts.db, "get_max_depth", AsyncMock(return_value=max_depth)),
        patch.object(
            ts.game_xp_service,
            "level_info",
            AsyncMock(return_value=(level, 0, 100)),
        ),
    )


@pytest.mark.asyncio
async def test_build_context_aggregates_progression():
    ps, pd, pl = _patch_state(alloc={"mining": 10}, max_depth=2, level=12)
    with ps, pd, pl:
        ctx = await ts.build_context(7, 42)
    assert ctx.skills == {"mining": 10}
    assert ctx.max_depth == 2
    assert ctx.level == 12


@pytest.mark.asyncio
async def test_earned_reflects_state():
    cap = skills.PER_BRANCH_CAP
    ps, pd, pl = _patch_state(alloc={"crafting": cap}, max_depth=1, level=10)
    with ps, pd, pl:
        earned_ids = {t.id for t in await ts.earned(7, 42)}
    assert {"master_smith", "spelunker", "veteran"} <= earned_ids


@pytest.mark.asyncio
async def test_equip_rejects_unknown_title():
    ps, pd, pl = _patch_state()
    with ps, pd, pl, patch.object(ts.db, "set_equipped_title", AsyncMock()) as setp:
        result = await ts.equip(7, 42, "emperor")
    assert not result.ok
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_equip_rejects_unearned_title():
    # crafting only at 1 point — master_smith not earned.
    ps, pd, pl = _patch_state(alloc={"crafting": 1})
    with ps, pd, pl, patch.object(ts.db, "set_equipped_title", AsyncMock()) as setp:
        result = await ts.equip(7, 42, "master_smith")
    assert not result.ok
    assert "haven't earned" in result.message
    setp.assert_not_called()


@pytest.mark.asyncio
async def test_equip_persists_an_earned_title():
    cap = skills.PER_BRANCH_CAP
    ps, pd, pl = _patch_state(alloc={"crafting": cap})
    with ps, pd, pl, patch.object(ts.db, "set_equipped_title", AsyncMock()) as setp:
        result = await ts.equip(7, 42, "MASTER_SMITH")  # case-insensitive
    assert result.ok
    setp.assert_awaited_once_with("42", 7, "master_smith")


@pytest.mark.asyncio
async def test_unequip_clears_the_choice():
    with patch.object(ts.db, "set_equipped_title", AsyncMock()) as setp:
        result = await ts.unequip(7, 42)
    assert result.ok
    setp.assert_awaited_once_with("42", 7, None)


@pytest.mark.asyncio
async def test_equipped_title_hidden_when_no_longer_earned():
    # stored choice is master_smith, but crafting was respecced to 0 → un-earned.
    ps, pd, pl = _patch_state(alloc={})
    with ps, pd, pl, patch.object(
        ts.db,
        "get_equipped_title",
        AsyncMock(return_value="master_smith"),
    ):
        assert await ts.equipped_title(7, 42) is None


@pytest.mark.asyncio
async def test_equipped_title_shown_when_still_earned():
    cap = skills.PER_BRANCH_CAP
    ps, pd, pl = _patch_state(alloc={"crafting": cap})
    with ps, pd, pl, patch.object(
        ts.db,
        "get_equipped_title",
        AsyncMock(return_value="master_smith"),
    ):
        title = await ts.equipped_title(7, 42)
    assert title is not None and title.id == "master_smith"


@pytest.mark.asyncio
async def test_equipped_title_none_when_unset():
    with patch.object(ts.db, "get_equipped_title", AsyncMock(return_value=None)):
        assert await ts.equipped_title(7, 42) is None
