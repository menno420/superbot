"""Game wager workflow — the audited money boundary for wagered games (P0-1).

Every two-party (PvP) or paid-entry (tournament) coin movement in the
games stack composes the atomic ``economy_service`` primitives
(``debit_in_txn`` / ``credit_in_txn``) **inside one** ``db.transaction()``
here, exactly like ``services.mining_workflow`` does for mining.  Before
this service the wager flows debited and credited in two separate
top-level calls, so a crash between them could:

* **mint coins** — the winner was credited the pot, then a failure
  skipped the loser's debit (RPS / blackjack PvP settle); or
* **lose an entry fee** — the fee was debited at registration, then a
  crash skipped the checkpoint row that recovery refunds from
  (RPS / blackjack tournament entry).

The cure is D1 **escrow-at-accept** for PvP plus **debit-with-the-row**
for tournament entry:

* ``open_pvp_wager`` debits *both* players' stakes the moment a
  challenge is accepted and writes one ``*_escrow`` checkpoint row per
  player in the same transaction.  The pot now physically lives outside
  both wallets — the loser *cannot* be short at settle, so the
  overdraft-debit (and its mint window) is gone.
* ``settle_pvp`` / ``refund_pvp`` pay the escrowed pot out (to the
  winner, or back to each player on a tie/abort) and delete the escrow
  rows in one transaction.  Both are **idempotent**: they ``FOR UPDATE``
  the escrow rows, and a replay that finds them already gone is a no-op
  — a crash-retry or a double settle can never double-pay.
* ``enter_tournament`` debits the fee and writes the recovery row in one
  transaction (closing the lost-fee window).
* ``payout_tournament`` pays the winner and deletes the entry rows
  together, idempotent by the same row-consumption guard.

Escrow / entry rows carry the ``bet`` key, so the existing
``services.game_state_cleanup`` GC sweep and the per-cog cog_load
recovery loops already refund any row a crash strands — this service
adds atomicity, not a new recovery surface.

EventBus emission happens **after** the transaction commits, never
inside it (the ``economy_service.transfer`` precedent).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_state_service
from utils import db

logger = logging.getLogger("bot.game_wager_workflow")

# Payload key under which each escrow / entry row records the staked
# amount.  Shared with services.game_state_cleanup (the GC refund
# convention) and the per-cog recovery loops — keep it ``bet``.
STAKE_KEY = "bet"


@dataclass(frozen=True)
class EscrowResult:
    """The outcome of opening a PvP wager."""

    #: True when both stakes were escrowed this call (False = free game,
    #: stake <= 0, so nothing moved).
    escrowed: bool
    #: The per-player stake that left each wallet (0 when not escrowed).
    stake: int


@dataclass(frozen=True)
class SettleResult:
    """The outcome of a settle / refund / payout."""

    #: True when money moved this call.  False means the wager was
    #: already settled (idempotent replay) or there was nothing staked.
    paid: bool
    #: Total coins paid out this call.
    amount: int
    #: New balance of the credited winner, when a single winner was paid.
    new_winner_balance: int | None = None


# ---------------------------------------------------------------------------
# PvP — escrow at accept, settle / refund at resolve
# ---------------------------------------------------------------------------


async def open_pvp_wager(
    *,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    version: int,
    p1_id: int,
    p2_id: int,
    stake: int,
    reason: str,
) -> EscrowResult:
    """Escrow both players' stakes when a PvP challenge is accepted.

    Debits *stake* from each player and writes one escrow checkpoint row
    per player — all in ONE transaction.  Raises
    :class:`economy_service.InsufficientFundsError` (rolling back both
    legs) if either player cannot afford the stake, so the caller can
    abort the match before any hand is dealt.

    A *stake* of 0 (free PvP) escrows nothing and returns
    ``escrowed=False``.
    """
    if stake <= 0:
        return EscrowResult(escrowed=False, stake=0)
    async with db.transaction() as conn:
        bal1 = await economy_service.debit_in_txn(
            conn,
            guild_id,
            p1_id,
            stake,
            reason=reason,
            actor_id=p1_id,
        )
        bal2 = await economy_service.debit_in_txn(
            conn,
            guild_id,
            p2_id,
            stake,
            reason=reason,
            actor_id=p2_id,
        )
        await game_state_service.save(
            guild_id,
            p1_id,
            channel_id,
            subsystem,
            {STAKE_KEY: stake, "peer": p2_id},
            version=version,
            conn=conn,
        )
        await game_state_service.save(
            guild_id,
            p2_id,
            channel_id,
            subsystem,
            {STAKE_KEY: stake, "peer": p1_id},
            version=version,
            conn=conn,
        )
    await _emit_balance(guild_id, p1_id, -stake, bal1, reason)
    await _emit_balance(guild_id, p2_id, -stake, bal2, reason)
    return EscrowResult(escrowed=True, stake=stake)


async def settle_pvp(
    *,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    p1_id: int,
    p2_id: int,
    winner_id: int,
    reason: str,
) -> SettleResult:
    """Pay the escrowed pot to *winner_id* and release the escrow rows.

    Idempotent: locks both escrow rows ``FOR UPDATE`` and pays out the
    summed stakes only if they are still present.  A second call (crash
    retry / double resolve) finds the rows gone and returns
    ``paid=False`` without moving money.
    """
    async with db.transaction() as conn:
        rows = await game_state_service.fetch_rows_for_update(
            guild_id,
            subsystem,
            conn=conn,
            channel_id=channel_id,
            user_ids=[p1_id, p2_id],
        )
        pot = _sum_stakes(rows)
        if pot <= 0:
            return SettleResult(paid=False, amount=0)
        new_balance = await economy_service.credit_in_txn(
            conn,
            guild_id,
            winner_id,
            pot,
            reason=reason,
            actor_id=winner_id,
        )
        await _delete_escrow_rows(conn, guild_id, channel_id, subsystem, rows)
    await _emit_balance(guild_id, winner_id, pot, new_balance, reason)
    return SettleResult(paid=True, amount=pot, new_winner_balance=new_balance)


async def refund_pvp(
    *,
    guild_id: int,
    channel_id: int,
    subsystem: str,
    p1_id: int,
    p2_id: int,
    reason: str,
) -> SettleResult:
    """Return each player's own stake and release the escrow rows.

    Used on a tie / both-forfeit / post-accept abort.  Idempotent by the
    same ``FOR UPDATE`` row-consumption guard as :func:`settle_pvp`.
    """
    emits: list[tuple[int, int, int]] = []
    async with db.transaction() as conn:
        rows = await game_state_service.fetch_rows_for_update(
            guild_id,
            subsystem,
            conn=conn,
            channel_id=channel_id,
            user_ids=[p1_id, p2_id],
        )
        if _sum_stakes(rows) <= 0:
            return SettleResult(paid=False, amount=0)
        total = 0
        for row in rows:
            stake = _row_stake(row)
            if stake <= 0:
                continue
            uid = row["user_id"]
            new_balance = await economy_service.credit_in_txn(
                conn,
                guild_id,
                uid,
                stake,
                reason=reason,
                actor_id=uid,
            )
            total += stake
            emits.append((uid, stake, new_balance))
        await _delete_escrow_rows(conn, guild_id, channel_id, subsystem, rows)
    for uid, stake, new_balance in emits:
        await _emit_balance(guild_id, uid, stake, new_balance, reason)
    return SettleResult(paid=total > 0, amount=total)


# ---------------------------------------------------------------------------
# Tournament — debit-with-the-row at entry, settle the pot at payout
# ---------------------------------------------------------------------------


async def enter_tournament(
    *,
    guild_id: int,
    user_id: int,
    channel_id: int,
    subsystem: str,
    version: int,
    fee: int,
    reason: str,
    extra_state: dict | None = None,
) -> int:
    """Debit the entry *fee* and write the recovery row in one transaction.

    Returns the player's new balance.  Raises
    :class:`economy_service.InsufficientFundsError` (rolling back the
    row) when the player cannot afford the fee — the caller drops them
    from the tournament.  A *fee* of 0 is a free entry: no debit, no row,
    returns the current balance.
    """
    if fee <= 0:
        return await db.get_coins(user_id, guild_id)
    state = {STAKE_KEY: fee}
    if extra_state:
        state.update(extra_state)
    async with db.transaction() as conn:
        new_balance = await economy_service.debit_in_txn(
            conn,
            guild_id,
            user_id,
            fee,
            reason=reason,
            actor_id=user_id,
        )
        await game_state_service.save(
            guild_id,
            user_id,
            channel_id,
            subsystem,
            state,
            version=version,
            conn=conn,
        )
    await _emit_balance(guild_id, user_id, -fee, new_balance, reason)
    return new_balance


async def payout_tournament(
    *,
    guild_id: int,
    subsystem: str,
    winner_id: int | None,
    reason: str,
    free_reward: int = 0,
    free_reason: str | None = None,
) -> SettleResult:
    """Pay the tournament winner and release every entry row, atomically.

    The pot is the sum of the escrowed entry fees (the *truth*, not a
    recomputed ``fee × players``), so a player who dropped out after
    paying is never short-changed.  Crediting the winner and deleting
    the entry rows happen in one transaction; a replay finds no rows and
    is a no-op, so recovery can never double-pay an already-settled
    tournament.

    *free_reward* covers the no-entry-fee case (a fixed consolation
    reward).  Free tournaments stake nothing and leave no rows, so this
    leg is not row-guarded — it is single-call by construction (no
    recovery path pays rewards) and carries no money-at-risk.
    """
    async with db.transaction() as conn:
        rows = await game_state_service.fetch_rows_for_update(
            guild_id,
            subsystem,
            conn=conn,
        )
        pot = _sum_stakes(rows)
        if rows:
            # Paid tournament: release the escrowed entry rows and pay
            # the winner the summed pot (row deletion is the idempotency
            # guard — a replay finds no rows).
            await _delete_escrow_rows(conn, guild_id, None, subsystem, rows)
            if winner_id is None or pot <= 0:
                return SettleResult(paid=False, amount=0)
            paid_reason, amount = reason, pot
        elif winner_id is not None and free_reward > 0:
            # Free tournament: fixed consolation reward, no escrow to
            # consume (single-call by construction — see docstring).
            paid_reason, amount = free_reason or reason, free_reward
        else:
            return SettleResult(paid=False, amount=0)
        new_balance = await economy_service.credit_in_txn(
            conn,
            guild_id,
            winner_id,
            amount,
            reason=paid_reason,
            actor_id=winner_id,
        )
    await _emit_balance(guild_id, winner_id, amount, new_balance, paid_reason)
    return SettleResult(paid=True, amount=amount, new_winner_balance=new_balance)


# ---------------------------------------------------------------------------
# Recovery — refund stranded escrow / entry rows promptly (cog_load,
# on_guild_remove).  The 24 h game_state GC already refunds these via the
# ``bet`` convention; this just does it sooner so a crash mid-wager does
# not leave coins escrowed for up to a day.
# ---------------------------------------------------------------------------


async def recover_escrow(
    subsystem: str,
    *,
    reason: str,
    guild_id: int | None = None,
) -> int:
    """Refund every stranded ``bet`` row for *subsystem*, then clear it.

    Each escrow/entry row carries a single-player ``bet``, so the refund
    is single-sided and the clear-after makes a re-run a no-op.  Refund
    failures are logged but the row is still cleared (the GC convention —
    never loop forever on a permanently-failing refund).  Returns the
    number of rows refunded.  *guild_id* scopes ``on_guild_remove``;
    omit it for a cog_load sweep.
    """
    try:
        rows = await game_state_service.list_active_for_subsystem(
            subsystem,
            guild_id=guild_id,
        )
    except Exception as exc:
        logger.warning("%s escrow recovery skipped: %s", subsystem, exc)
        return 0
    refunded = 0
    for row in rows:
        state = row.get("state") or {}
        bet = state.get(STAKE_KEY)
        if isinstance(bet, int) and bet > 0:
            try:
                await economy_service.refund(
                    guild_id=row["guild_id"],
                    user_id=row["user_id"],
                    amount=bet,
                    reason=reason,
                )
                refunded += 1
            except Exception as exc:
                logger.warning(
                    "%s escrow refund failed for user=%s: %s",
                    subsystem,
                    row.get("user_id"),
                    exc,
                )
        try:
            await game_state_service.clear_by_id(row["id"])
        except Exception as exc:
            logger.warning(
                "%s escrow clear failed for id=%s: %s",
                subsystem,
                row.get("id"),
                exc,
            )
    if refunded:
        logger.info(
            "%s escrow recovery: refunded %d stranded stake(s)",
            subsystem,
            refunded,
        )
    return refunded


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _row_stake(row: dict) -> int:
    state = row.get("state") or {}
    stake = state.get(STAKE_KEY)
    return stake if isinstance(stake, int) and stake > 0 else 0


def _sum_stakes(rows: list[dict]) -> int:
    return sum(_row_stake(r) for r in rows)


async def _delete_escrow_rows(
    conn,
    guild_id: int,
    channel_id: int | None,
    subsystem: str,
    rows: list[dict],
) -> None:
    """Delete every locked escrow/entry row inside the settle transaction."""
    for row in rows:
        await game_state_service.clear(
            guild_id,
            row["user_id"],
            channel_id if channel_id is not None else row["channel_id"],
            subsystem,
            conn=conn,
        )


async def _emit_balance(
    guild_id: int,
    user_id: int | None,
    delta: int,
    new_balance: int | None,
    reason: str,
) -> None:
    """EVT_BALANCE_CHANGED, after the owning transaction committed."""
    if user_id is None or new_balance is None:
        return
    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=delta,
        new_balance=new_balance,
        reason=reason,
    )


__all__ = [
    "EscrowResult",
    "SettleResult",
    "open_pvp_wager",
    "settle_pvp",
    "refund_pvp",
    "enter_tournament",
    "payout_tournament",
    "recover_escrow",
]
