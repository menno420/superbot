"""Background session garbage collector.

Runs every SESSION_GC_INTERVAL seconds (default: 5 minutes) and:
  1. Deletes runtime_sessions older than SESSION_TTL seconds (default: 2 hours).
     Cascade delete removes associated runtime_session_state rows.
  2. Calls :func:`core.runtime.navigation_stack.forget` for each deleted
     session id so the per-session lock dict cannot grow unbounded
     (PR N1).
  3. Deletes panel_anchors marked is_stale=TRUE.
  4. Prunes stale ``game_state`` rows older than ``GAME_STATE_TTL_HOURS``
     (PR G0).  If a stale row's payload carries a ``bet`` field, the
     coins are refunded via :func:`services.economy_service.refund`
     before the row is deleted, so a crash mid-game never silently
     swallows staked money.

The GC is started as an asyncio Task from bot1.py's main() after db.init().

Public surface:
    start(bot) → asyncio.Task  — call once at startup
"""

from __future__ import annotations

import asyncio
import logging
import time

from core.runtime import navigation_stack, scope_locks
from services import economy_service, game_state_service
from services import metrics as _metrics
from utils import db

logger = logging.getLogger("bot.runtime.gc")

SESSION_TTL: int = 7200  # 2 hours in seconds
SESSION_GC_INTERVAL: int = 300  # 5 minutes between GC sweeps


async def _run_gc_loop() -> None:
    """Infinite loop that performs GC sweeps on each interval."""
    while True:
        await asyncio.sleep(SESSION_GC_INTERVAL)
        try:
            cutoff = time.time() - SESSION_TTL
            expired_ids = await db.delete_expired_sessions(cutoff)
            # Drop in-process navigation_stack locks for the now-gone
            # sessions.  ``forget`` is a no-op when no lock exists, so
            # safe to call on every id unconditionally.
            for sid in expired_ids:
                navigation_stack.forget(sid)
            anchors_removed = await db.delete_stale_panel_anchors()
            game_state_removed, game_state_refunded = await _sweep_stale_game_state()
            # F-2 / S1.2: safety-net reclamation of scope_locks that
            # cogs missed forget()-ing on edge teardown paths.  Held
            # locks are never reclaimed.
            scope_locks_swept = scope_locks.sweep_idle()
            active_count = await db.count_active_sessions()
            _metrics.session_active_count.set(active_count)
            if (
                expired_ids
                or anchors_removed
                or game_state_removed
                or game_state_refunded
                or scope_locks_swept
            ):
                logger.info(
                    "GC sweep complete — %d session(s), %d anchor(s), "
                    "%d game_state row(s) removed (%d refund(s)), "
                    "%d scope_lock(s) idle-swept",
                    len(expired_ids),
                    anchors_removed,
                    game_state_removed,
                    game_state_refunded,
                    scope_locks_swept,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("GC sweep error: %s", exc, exc_info=True)


async def _sweep_stale_game_state() -> tuple[int, int]:
    """Refund staked coins on every stale game_state row, then delete it.

    Returns ``(rows_removed, refunds_issued)``.

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
        return 0, 0
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
    return rows_removed, refunds_issued


def start() -> asyncio.Task:
    """Create and return the background GC task.

    Must be called inside a running asyncio event loop (i.e., after bot startup).
    PR-02b: spawned through ``core.runtime.tasks.spawn`` so the canonical
    supervisor tracks the task, increments ``task_outcome_total`` on
    completion, and includes it in ``tasks.active()``.  The returned task
    is still the same ``asyncio.Task`` instance for callers that retain
    it; ``tasks.cancel_all()`` cancels it on shutdown.
    """
    from core.runtime import tasks as runtime_tasks

    task = runtime_tasks.spawn("session_gc:loop", _run_gc_loop())
    logger.info(
        "Session GC started — TTL=%ds, interval=%ds",
        SESSION_TTL,
        SESSION_GC_INTERVAL,
    )
    return task
