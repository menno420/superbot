"""Q-0054 — PvP duels tick each fighter's weapon + armor durability."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from cogs.deathmatch_cog import _tick_duel_gear_wear
from utils.mining.workshop import ACTION_DUEL, WEAR_PLAN, WearReport


def test_duel_wear_plan_covers_every_combat_set_slot():
    from utils import equipment

    slots = {slot for slot, _ in WEAR_PLAN[ACTION_DUEL]}
    assert slots == set(equipment.SET_SLOTS)
    # Never underground-gated — duels happen anywhere.
    assert all(not underground for _, underground in WEAR_PLAN[ACTION_DUEL])


@pytest.mark.asyncio
async def test_both_fighters_tick_once_and_notes_surface():
    p1 = SimpleNamespace(id=1, display_name="One", bot=False)
    p2 = SimpleNamespace(id=2, display_name="Two", bot=False)
    with (
        patch(
            "cogs.deathmatch_cog.db.get_equipment",
            new_callable=AsyncMock,
            return_value={"weapon": "sword"},
        ),
        patch(
            "cogs.deathmatch_cog.mining_workflow.wear_tick",
            new_callable=AsyncMock,
            return_value=WearReport(notes=("⚠️ worn",)),
        ) as tick,
    ):
        notes = await _tick_duel_gear_wear(99, p1, p2)
    assert tick.await_count == 2
    for call in tick.await_args_list:
        assert call.kwargs["action"] == ACTION_DUEL
        assert call.kwargs["depth"] == 0
    assert notes == ["One: ⚠️ worn", "Two: ⚠️ worn"]


@pytest.mark.asyncio
async def test_bot_fighters_are_skipped():
    human = SimpleNamespace(id=1, display_name="One", bot=False)
    robot = SimpleNamespace(id=2, display_name="Bot", bot=True)
    with (
        patch(
            "cogs.deathmatch_cog.db.get_equipment",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "cogs.deathmatch_cog.mining_workflow.wear_tick",
            new_callable=AsyncMock,
            return_value=WearReport(),
        ) as tick,
    ):
        notes = await _tick_duel_gear_wear(99, human, robot)
    assert tick.await_count == 1  # only the human
    assert notes == []
