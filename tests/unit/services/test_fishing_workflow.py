"""fishing_workflow — transaction membership + post-commit emission.

The Q-0071 contract under test (the mining/shop precedent): all three legs of a
cast (catch-log write + audited coin credit + game-XP award) run on the SAME
workflow-owned connection, and nothing is emitted until the transaction context
has exited (= committed).
"""

from __future__ import annotations

import random
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow as wf
from services import game_xp_service
from utils.fishing.fish import FishSpecies
from utils.fishing.rewards import Catch


def _txn(sentinel_conn, events):
    @asynccontextmanager
    async def _ctx():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    return _ctx


_CATCH = Catch(
    species=FishSpecies("trout", "🐠", "uncommon", 8, 16, 0.5, 2.0),
    weight=1.4,
    value=12,
)


@pytest.mark.asyncio
async def test_all_legs_run_on_one_conn_and_emit_after_commit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    async def _record(user_id, guild_id, species, weight, value, *, conn=None):
        events.append("record")
        assert conn is sentinel_conn
        assert (species, weight, value) == ("trout", 1.4, 12)

    async def _credit(conn, guild_id, user_id, amount, *, reason, actor_id=None):
        events.append("credit")
        assert conn is sentinel_conn
        assert amount == 12
        assert reason == wf.FISH_REASON
        return 112

    award = game_xp_service.GameXpAward(
        guild_id=1,
        user_id=99,
        game=game_xp_service.GAME_FISHING,
        action="fish",
        amount=3,
        game_total=3,
        shared_total=3,
        level=1,
        leveled_up=False,
    )

    async def _award(guild_id, user_id, *, game, action, conn=None, depth=0):
        events.append("award")
        assert conn is sentinel_conn
        assert game == game_xp_service.GAME_FISHING
        return award

    async def _emit(event, **payload):
        events.append(f"emit:{event}")

    with (
        patch.object(wf, "roll_catch", lambda *a, **k: _CATCH),
        patch.object(wf.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(wf.db, "record_catch", AsyncMock(side_effect=_record)),
        patch.object(
            wf.economy_service,
            "credit_in_txn",
            AsyncMock(side_effect=_credit),
        ),
        patch.object(wf.game_xp_service, "award", AsyncMock(side_effect=_award)),
        patch.object(
            wf.game_xp_service,
            "emit_award_events",
            AsyncMock(),
        ) as emit_xp,
        patch.object(wf.bus, "emit", AsyncMock(side_effect=_emit)),
    ):
        result = await wf.fish(99, 1)

    # Every write happens inside the transaction; the balance event only after.
    assert events.index("txn_exit") < events.index("emit:economy.balance_changed")
    for leg in ("record", "credit", "award"):
        assert events.index(leg) < events.index("txn_exit")
    emit_xp.assert_awaited_once_with(award)

    assert result.coins == 12
    assert result.new_balance == 112
    assert result.catch is _CATCH
    assert result.xp_note is None


@pytest.mark.asyncio
async def test_level_up_surfaces_the_xp_note():
    sentinel_conn = MagicMock(name="conn")

    award = game_xp_service.GameXpAward(
        guild_id=1,
        user_id=99,
        game=game_xp_service.GAME_FISHING,
        action="fish",
        amount=3,
        game_total=300,
        shared_total=300,
        level=4,
        leveled_up=True,
    )

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(wf, "roll_catch", lambda *a, **k: _CATCH),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_catch", AsyncMock()),
        patch.object(
            wf.economy_service,
            "credit_in_txn",
            AsyncMock(return_value=50),
        ),
        patch.object(wf.game_xp_service, "award", AsyncMock(return_value=award)),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
        patch.object(wf.bus, "emit", AsyncMock()),
    ):
        result = await wf.fish(99, 1)

    assert result.xp_note == award.note


@pytest.mark.asyncio
async def test_roll_value_drives_both_the_log_and_the_credit():
    """A different rolled value flows to both the catch-log row and the credit."""
    sentinel_conn = MagicMock(name="conn")
    big = Catch(species=_CATCH.species, weight=2.0, value=40)
    credited: list[int] = []

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    async def _credit(conn, guild_id, user_id, amount, *, reason, actor_id=None):
        credited.append(amount)
        return 1000

    with (
        patch.object(wf, "roll_catch", lambda *a, **k: big),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_catch", AsyncMock()) as record,
        patch.object(
            wf.economy_service,
            "credit_in_txn",
            AsyncMock(side_effect=_credit),
        ),
        patch.object(wf.game_xp_service, "award", AsyncMock(return_value=None)),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()) as emit_xp,
        patch.object(wf.bus, "emit", AsyncMock()),
    ):
        result = await wf.fish(99, 1)

    record.assert_awaited_once()
    assert record.await_args.args[4] == 40  # value passed to record_catch
    assert credited == [40]
    assert result.coins == 40
    # No award (0-XP capped) → no XP event emitted.
    emit_xp.assert_not_awaited()
