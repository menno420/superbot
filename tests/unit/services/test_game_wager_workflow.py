"""Unit (mock-the-pool) coverage for services.game_wager_workflow.

The faithful transactional guarantees live in
``test_game_wager_workflow_integration`` (real Postgres, skipped in CI).
This suite mocks the DB seam so CI — which runs no Postgres — still
exercises the orchestration: which primitives each op composes, the
idempotent no-op when the escrow rows are gone, and the pot-vs-free
payout branch.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from services import economy_service
from services import game_wager_workflow as wf


@pytest.fixture
def fake_db(monkeypatch):
    """Patch the workflow's DB seam: transaction, economy + game_state legs."""
    conn = object()

    @asynccontextmanager
    async def fake_txn():
        yield conn

    monkeypatch.setattr(wf.db, "transaction", fake_txn)
    monkeypatch.setattr(wf.db, "get_coins", AsyncMock(return_value=0))
    debit = AsyncMock(return_value=60)
    credit = AsyncMock(return_value=140)
    save = AsyncMock()
    clear = AsyncMock()
    monkeypatch.setattr(economy_service, "debit_in_txn", debit)
    monkeypatch.setattr(economy_service, "credit_in_txn", credit)
    monkeypatch.setattr(wf.game_state_service, "save", save)
    monkeypatch.setattr(wf.game_state_service, "clear", clear)
    monkeypatch.setattr(wf.bus, "emit", AsyncMock())
    return {
        "conn": conn,
        "debit": debit,
        "credit": credit,
        "save": save,
        "clear": clear,
    }


@pytest.mark.asyncio
async def test_open_pvp_wager_debits_both_and_writes_two_rows(fake_db):
    res = await wf.open_pvp_wager(
        guild_id=1,
        channel_id=2,
        subsystem="s",
        version=1,
        p1_id=10,
        p2_id=20,
        stake=40,
        reason="r",
    )
    assert res.escrowed and res.stake == 40
    assert fake_db["debit"].await_count == 2
    assert fake_db["save"].await_count == 2


@pytest.mark.asyncio
async def test_open_pvp_wager_free_is_noop(fake_db):
    res = await wf.open_pvp_wager(
        guild_id=1,
        channel_id=2,
        subsystem="s",
        version=1,
        p1_id=10,
        p2_id=20,
        stake=0,
        reason="r",
    )
    assert not res.escrowed
    fake_db["debit"].assert_not_called()
    fake_db["save"].assert_not_called()


@pytest.mark.asyncio
async def test_settle_pvp_credits_pot(fake_db, monkeypatch):
    monkeypatch.setattr(
        wf.game_state_service,
        "fetch_rows_for_update",
        AsyncMock(
            return_value=[
                {"user_id": 10, "channel_id": 2, "state": {"bet": 40}},
                {"user_id": 20, "channel_id": 2, "state": {"bet": 40}},
            ]
        ),
    )
    res = await wf.settle_pvp(
        guild_id=1,
        channel_id=2,
        subsystem="s",
        p1_id=10,
        p2_id=20,
        winner_id=10,
        reason="r",
    )
    assert res.paid and res.amount == 80
    fake_db["credit"].assert_awaited_once()
    assert fake_db["credit"].await_args.args[3] == 80  # pot
    assert fake_db["clear"].await_count == 2


@pytest.mark.asyncio
async def test_settle_pvp_idempotent_when_rows_gone(fake_db, monkeypatch):
    monkeypatch.setattr(
        wf.game_state_service,
        "fetch_rows_for_update",
        AsyncMock(return_value=[]),
    )
    res = await wf.settle_pvp(
        guild_id=1,
        channel_id=2,
        subsystem="s",
        p1_id=10,
        p2_id=20,
        winner_id=10,
        reason="r",
    )
    assert not res.paid and res.amount == 0
    fake_db["credit"].assert_not_called()
    fake_db["clear"].assert_not_called()


@pytest.mark.asyncio
async def test_refund_pvp_credits_each_own_stake(fake_db, monkeypatch):
    monkeypatch.setattr(
        wf.game_state_service,
        "fetch_rows_for_update",
        AsyncMock(
            return_value=[
                {"user_id": 10, "channel_id": 2, "state": {"bet": 40}},
                {"user_id": 20, "channel_id": 2, "state": {"bet": 25}},
            ]
        ),
    )
    res = await wf.refund_pvp(
        guild_id=1,
        channel_id=2,
        subsystem="s",
        p1_id=10,
        p2_id=20,
        reason="r",
    )
    assert res.paid and res.amount == 65
    assert fake_db["credit"].await_count == 2
    assert fake_db["clear"].await_count == 2


@pytest.mark.asyncio
async def test_enter_tournament_debits_and_saves(fake_db):
    bal = await wf.enter_tournament(
        guild_id=1,
        user_id=10,
        channel_id=0,
        subsystem="t",
        version=1,
        fee=30,
        reason="r",
        extra_state={"rounds": 5},
    )
    assert bal == 60
    fake_db["debit"].assert_awaited_once()
    saved_state = fake_db["save"].await_args.args[4]
    assert saved_state == {"bet": 30, "rounds": 5}


@pytest.mark.asyncio
async def test_enter_tournament_free_skips_debit(fake_db):
    bal = await wf.enter_tournament(
        guild_id=1,
        user_id=10,
        channel_id=0,
        subsystem="t",
        version=1,
        fee=0,
        reason="r",
    )
    assert bal == 0  # db.get_coins stub
    fake_db["debit"].assert_not_called()
    fake_db["save"].assert_not_called()


@pytest.mark.asyncio
async def test_payout_tournament_pot_path(fake_db, monkeypatch):
    monkeypatch.setattr(
        wf.game_state_service,
        "fetch_rows_for_update",
        AsyncMock(
            return_value=[
                {"user_id": 10, "channel_id": 0, "state": {"bet": 30}},
                {"user_id": 20, "channel_id": 0, "state": {"bet": 30}},
            ]
        ),
    )
    res = await wf.payout_tournament(
        guild_id=1,
        subsystem="t",
        winner_id=10,
        reason="win",
        free_reward=200,
        free_reason="free",
    )
    assert res.paid and res.amount == 60
    assert fake_db["credit"].await_args.args[3] == 60
    assert fake_db["clear"].await_count == 2


@pytest.mark.asyncio
async def test_payout_tournament_free_path(fake_db, monkeypatch):
    monkeypatch.setattr(
        wf.game_state_service,
        "fetch_rows_for_update",
        AsyncMock(return_value=[]),
    )
    res = await wf.payout_tournament(
        guild_id=1,
        subsystem="t",
        winner_id=10,
        reason="win",
        free_reward=200,
        free_reason="free",
    )
    assert res.paid and res.amount == 200
    assert fake_db["credit"].await_args.args[3] == 200
    fake_db["clear"].assert_not_called()


@pytest.mark.asyncio
async def test_payout_tournament_idempotent_no_rows_no_reward(fake_db, monkeypatch):
    monkeypatch.setattr(
        wf.game_state_service,
        "fetch_rows_for_update",
        AsyncMock(return_value=[]),
    )
    res = await wf.payout_tournament(
        guild_id=1,
        subsystem="t",
        winner_id=10,
        reason="win",
    )
    assert not res.paid
    fake_db["credit"].assert_not_called()
