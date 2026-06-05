"""Stale game-state cleanup provider (RC-7).

Owns the ADR-002 refund-on-abandon semantics that used to live inline in
``core.runtime.session_gc._sweep_stale_game_state``.  Registered with
``core.runtime.cleanup_registry`` (via :func:`install`, called once from
``bot1`` at startup) so the GC scheduler can reclaim stale ``game_state`` rows
— and refund any staked coins — without ``session_gc`` importing the economy or
game-state services.

Layer: ``services`` — may import ``core`` and sibling services.
"""

from __future__ import annotations

import logging

from core.runtime.cleanup_registry import CleanupResult, register
from services import economy_service, game_state_service

# Logged under the GC logger so operator log filters / alerts on the existing
# "game_state GC refund" lines keep working unchanged — RC-7 preserves the
# observable refund behaviour, only its ownership moves.
logger = logging.getLogger("bot.runtime.gc")

PROVIDER_NAME = "game_state"


async def sweep_stale_game_state() -> CleanupResult:
    """Refund staked coins on every stale game_state row, then delete it.

    Returns ``CleanupResult(removed, refunded)``.

    A stale row is one older than ``game_state_service.GAME_STATE_TTL_HOURS``
    (24 h by default).  In production this is rare: the cog should call
    ``clear`` on natural game completion, so only crashes / forced
    cog_unloads leave rows behind.

    The refund convention is opt-in: only rows whose payload contains
    a positive integer ``bet`` field trigger a refund.  This lets a
    cog adopt persistence without immediately wiring refund semantics,
    while keeping the door open for future cogs that DO carry stakes.
    Refund failures are logged but never prevent the row deletion —
    otherwise a permanently-failing refund would loop forever.
    """
    try:
        stale = await game_state_service.list_stale()
    except Exception as exc:
        logger.error("game_state stale-list failed: %s", exc, exc_info=True)
        return CleanupResult()
    rows_removed = 0
    refunds_issued = 0
    for row in stale:
        state = row.get("state")
        bet = state.get("bet") if isinstance(state, dict) else None
        if isinstance(bet, int) and bet > 0:
            try:
                await economy_service.refund(
                    guild_id=row["guild_id"],
                    user_id=row["user_id"],
                    amount=bet,
                    reason=f"game_state:gc:{row['subsystem']}",
                )
                refunds_issued += 1
            except Exception as exc:
                logger.warning(
                    "game_state GC refund failed for id=%s subsystem=%r: %s",
                    row["id"],
                    row["subsystem"],
                    exc,
                )
        try:
            await game_state_service.clear_by_id(row["id"])
            rows_removed += 1
        except Exception as exc:
            logger.warning(
                "game_state GC delete failed for id=%s: %s",
                row["id"],
                exc,
            )
    return CleanupResult(removed=rows_removed, refunded=refunds_issued)


def install() -> None:
    """Register this provider with the cleanup registry.

    Called once from ``bot1`` startup, before ``session_gc.start()``.  Idempotent
    (re-install overwrites the same name).
    """
    register(PROVIDER_NAME, sweep_stale_game_state)
