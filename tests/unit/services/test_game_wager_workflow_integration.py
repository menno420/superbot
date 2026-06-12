"""Real-Postgres integration for services.game_wager_workflow (P0-1).

The whole point of the wager workflow is *transactional* money movement:
escrow both PvP stakes (or a tournament fee) atomically with the recovery
row, settle/refund/payout atomically with the row deletion, and stay
idempotent under replay.  A mock-the-pool test cannot prove that — a
rollback only means something against a real transaction.  So this suite
drives the workflow against a live database (schema + migrations applied
by ``pool.init()``) and asserts the three guarantees the plan names:

1. **Failure injection** — a fault between compose steps leaves *no*
   partial money movement (balances and escrow rows both untouched).
2. **Terminal-state matrix** — win / tie / refund / tournament payout
   move exactly the right coins and leave no escrow rows.
3. **Idempotency** — a second settle / payout is a no-op (never
   double-pays), even after a crash-retry.

CI safety / isolation mirrors ``test_health_findings_integration``: the
module-local ``wager_db`` fixture skips when ``DATABASE_URL`` is unset
(CI) or Postgres is unreachable, and every row this suite writes lives in
a private guild-id band that it sweeps on entry + exit, so a booted bot's
own rows are never disturbed.  Count/balance assertions are absolute only
within that private band.
"""

from __future__ import annotations

import json
import os

import asyncpg
import pytest
import pytest_asyncio

from services import economy_service, game_wager_workflow
from utils import db
from utils.db import pool

# Private guild-id band — far from any real Discord snowflake the booted
# bot would use, so this suite never collides with live rows.
_GUILD_BASE = 990_000_000_000_000_000
_SUB = "test_wager_escrow"
_TSUB = "test_wager_tournament"


async def _sweep() -> None:
    await pool.execute(
        "DELETE FROM game_state WHERE guild_id >= $1",
        (_GUILD_BASE,),
    )
    await pool.execute(
        "DELETE FROM xp WHERE guild_id >= $1",
        (_GUILD_BASE,),
    )
    await pool.execute(
        "DELETE FROM economy_audit_log WHERE guild_id >= $1",
        (_GUILD_BASE,),
    )


@pytest_asyncio.fixture
async def wager_db():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL unset — real-Postgres integration test skipped (CI)")
    try:
        await pool.init()
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(
            f"Postgres unreachable ({type(exc).__name__}) — integration test skipped",
        )
    await _sweep()
    try:
        yield pool
    finally:
        await _sweep()
        await pool.close()


# Unique guild id per test so parallel rows never clash within the band.
_counter = 0


def _next_guild() -> int:
    global _counter
    _counter += 1
    return _GUILD_BASE + _counter


async def _set_balance(guild_id: int, user_id: int, coins: int) -> None:
    await db.add_coins(user_id, guild_id, coins)


async def _balance(guild_id: int, user_id: int) -> int:
    return await db.get_coins(user_id, guild_id)


async def _escrow_rows(guild_id: int, subsystem: str) -> list[dict]:
    rows = await pool.fetchall(
        "SELECT user_id, state FROM game_state WHERE guild_id=$1 AND subsystem=$2",
        (guild_id, subsystem),
    )
    for r in rows:
        if isinstance(r["state"], str):
            r["state"] = json.loads(r["state"])
    return rows


# ---------------------------------------------------------------------------
# PvP — escrow at accept
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_pvp_wager_escrows_both_stakes_atomically(wager_db):
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 100)

    res = await game_wager_workflow.open_pvp_wager(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        version=1,
        p1_id=p1,
        p2_id=p2,
        stake=40,
        reason="t:escrow",
    )
    assert res.escrowed and res.stake == 40
    assert await _balance(g, p1) == 60
    assert await _balance(g, p2) == 60
    rows = await _escrow_rows(g, _SUB)
    assert {r["user_id"] for r in rows} == {p1, p2}


@pytest.mark.asyncio
async def test_open_pvp_wager_insufficient_funds_rolls_back(wager_db):
    """If the second player cannot afford the stake, the first player's
    debit AND both escrow rows roll back — no partial escrow.
    """
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 10)  # cannot afford 40

    with pytest.raises(economy_service.InsufficientFundsError):
        await game_wager_workflow.open_pvp_wager(
            guild_id=g,
            channel_id=5,
            subsystem=_SUB,
            version=1,
            p1_id=p1,
            p2_id=p2,
            stake=40,
            reason="t:escrow",
        )
    # No money moved, no rows written.
    assert await _balance(g, p1) == 100
    assert await _balance(g, p2) == 10
    assert await _escrow_rows(g, _SUB) == []


@pytest.mark.asyncio
async def test_open_pvp_wager_fault_between_legs_leaves_nothing(wager_db, monkeypatch):
    """A fault injected after the first debit rolls the whole escrow back."""
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 100)

    real_save = game_wager_workflow.game_state_service.save
    calls = {"n": 0}

    async def boom_on_second_save(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("injected fault mid-escrow")
        return await real_save(*args, **kwargs)

    monkeypatch.setattr(
        game_wager_workflow.game_state_service,
        "save",
        boom_on_second_save,
    )
    with pytest.raises(RuntimeError, match="injected fault"):
        await game_wager_workflow.open_pvp_wager(
            guild_id=g,
            channel_id=5,
            subsystem=_SUB,
            version=1,
            p1_id=p1,
            p2_id=p2,
            stake=40,
            reason="t:escrow",
        )
    # Both debits rolled back with the failed row write.
    assert await _balance(g, p1) == 100
    assert await _balance(g, p2) == 100
    assert await _escrow_rows(g, _SUB) == []


# ---------------------------------------------------------------------------
# PvP — settle / refund (terminal matrix + idempotency)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settle_pvp_pays_pot_to_winner_and_is_idempotent(wager_db):
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 100)
    await game_wager_workflow.open_pvp_wager(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        version=1,
        p1_id=p1,
        p2_id=p2,
        stake=40,
        reason="t:escrow",
    )
    res = await game_wager_workflow.settle_pvp(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        p1_id=p1,
        p2_id=p2,
        winner_id=p1,
        reason="t:win",
    )
    assert res.paid and res.amount == 80
    assert await _balance(g, p1) == 140  # 60 + 80 pot
    assert await _balance(g, p2) == 60  # stayed escrowed-out
    assert await _escrow_rows(g, _SUB) == []

    # Idempotent replay: no rows left → no-op, no double pay.
    again = await game_wager_workflow.settle_pvp(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        p1_id=p1,
        p2_id=p2,
        winner_id=p1,
        reason="t:win",
    )
    assert not again.paid and again.amount == 0
    assert await _balance(g, p1) == 140


@pytest.mark.asyncio
async def test_refund_pvp_returns_each_own_stake_and_is_idempotent(wager_db):
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 100)
    await game_wager_workflow.open_pvp_wager(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        version=1,
        p1_id=p1,
        p2_id=p2,
        stake=40,
        reason="t:escrow",
    )
    res = await game_wager_workflow.refund_pvp(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        p1_id=p1,
        p2_id=p2,
        reason="t:refund",
    )
    assert res.paid and res.amount == 80
    assert await _balance(g, p1) == 100  # made whole
    assert await _balance(g, p2) == 100
    assert await _escrow_rows(g, _SUB) == []

    again = await game_wager_workflow.refund_pvp(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        p1_id=p1,
        p2_id=p2,
        reason="t:refund",
    )
    assert not again.paid
    assert await _balance(g, p1) == 100


@pytest.mark.asyncio
async def test_settle_pvp_fault_does_not_mint_or_strand(wager_db, monkeypatch):
    """A fault during settle leaves the pot escrowed (rows intact, winner
    not credited) — the opposite of the pre-P0-1 mint window.
    """
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 100)
    await game_wager_workflow.open_pvp_wager(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        version=1,
        p1_id=p1,
        p2_id=p2,
        stake=40,
        reason="t:escrow",
    )

    async def boom(*args, **kwargs):
        raise RuntimeError("injected fault during clear")

    monkeypatch.setattr(game_wager_workflow.game_state_service, "clear", boom)
    with pytest.raises(RuntimeError, match="injected fault"):
        await game_wager_workflow.settle_pvp(
            guild_id=g,
            channel_id=5,
            subsystem=_SUB,
            p1_id=p1,
            p2_id=p2,
            winner_id=p1,
            reason="t:win",
        )
    # Winner credit rolled back with the failed row delete; pot still escrowed.
    assert await _balance(g, p1) == 60
    rows = await _escrow_rows(g, _SUB)
    assert {r["user_id"] for r in rows} == {p1, p2}


# ---------------------------------------------------------------------------
# Tournament — entry + payout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enter_tournament_debits_and_writes_row_atomically(wager_db):
    g, u = _next_guild(), 1
    await _set_balance(g, u, 100)
    bal = await game_wager_workflow.enter_tournament(
        guild_id=g,
        user_id=u,
        channel_id=0,
        subsystem=_TSUB,
        version=1,
        fee=30,
        reason="t:entry",
        extra_state={"rounds": 5},
    )
    assert bal == 70
    rows = await _escrow_rows(g, _TSUB)
    assert len(rows) == 1
    assert rows[0]["state"]["bet"] == 30
    assert rows[0]["state"]["rounds"] == 5


@pytest.mark.asyncio
async def test_enter_tournament_insufficient_rolls_back(wager_db):
    g, u = _next_guild(), 1
    await _set_balance(g, u, 10)
    with pytest.raises(economy_service.InsufficientFundsError):
        await game_wager_workflow.enter_tournament(
            guild_id=g,
            user_id=u,
            channel_id=0,
            subsystem=_TSUB,
            version=1,
            fee=30,
            reason="t:entry",
        )
    assert await _balance(g, u) == 10
    assert await _escrow_rows(g, _TSUB) == []


@pytest.mark.asyncio
async def test_payout_tournament_pays_pot_and_is_idempotent(wager_db):
    g, w, loser = _next_guild(), 1, 2
    await _set_balance(g, w, 100)
    await _set_balance(g, loser, 100)
    await game_wager_workflow.enter_tournament(
        guild_id=g,
        user_id=w,
        channel_id=0,
        subsystem=_TSUB,
        version=1,
        fee=30,
        reason="t:entry",
    )
    await game_wager_workflow.enter_tournament(
        guild_id=g,
        user_id=loser,
        channel_id=0,
        subsystem=_TSUB,
        version=1,
        fee=30,
        reason="t:entry",
    )
    res = await game_wager_workflow.payout_tournament(
        guild_id=g,
        subsystem=_TSUB,
        winner_id=w,
        reason="t:win",
    )
    assert res.paid and res.amount == 60  # pot = sum of the two entries
    assert await _balance(g, w) == 130  # 70 + 60
    assert await _escrow_rows(g, _TSUB) == []

    # Replay: rows consumed → no-op, no double pay.
    again = await game_wager_workflow.payout_tournament(
        guild_id=g,
        subsystem=_TSUB,
        winner_id=w,
        reason="t:win",
    )
    assert not again.paid
    assert await _balance(g, w) == 130


@pytest.mark.asyncio
async def test_payout_tournament_free_reward_when_no_entries(wager_db):
    g, w = _next_guild(), 1
    await _set_balance(g, w, 100)
    res = await game_wager_workflow.payout_tournament(
        guild_id=g,
        subsystem=_TSUB,
        winner_id=w,
        reason="t:win",
        free_reward=200,
        free_reason="t:free",
    )
    assert res.paid and res.amount == 200
    assert await _balance(g, w) == 300


@pytest.mark.asyncio
async def test_payout_tournament_no_winner_is_noop(wager_db):
    g = _next_guild()
    res = await game_wager_workflow.payout_tournament(
        guild_id=g,
        subsystem=_TSUB,
        winner_id=None,
        reason="t:win",
        free_reward=200,
        free_reason="t:free",
    )
    assert not res.paid


@pytest.mark.asyncio
async def test_free_pvp_wager_moves_no_money(wager_db):
    g, p1, p2 = _next_guild(), 1, 2
    await _set_balance(g, p1, 100)
    await _set_balance(g, p2, 100)
    res = await game_wager_workflow.open_pvp_wager(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        version=1,
        p1_id=p1,
        p2_id=p2,
        stake=0,
        reason="t:escrow",
    )
    assert not res.escrowed
    assert await _escrow_rows(g, _SUB) == []
    settle = await game_wager_workflow.settle_pvp(
        guild_id=g,
        channel_id=5,
        subsystem=_SUB,
        p1_id=p1,
        p2_id=p2,
        winner_id=p1,
        reason="t:win",
    )
    assert not settle.paid
    assert await _balance(g, p1) == 100
