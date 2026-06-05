"""Background session garbage collector.

Runs every SESSION_GC_INTERVAL seconds (default: 5 minutes) and:
  1. Deletes runtime_sessions older than SESSION_TTL seconds (default: 2 hours).
     Cascade delete removes associated runtime_session_state rows.
  2. Calls :func:`core.runtime.navigation_stack.forget` for each deleted
     session id so the per-session lock dict cannot grow unbounded
     (PR N1).
  3. Deletes panel_anchors marked is_stale=TRUE.
  4. Invokes every registered feature cleanup provider via
     :func:`core.runtime.cleanup_registry.run_all` (RC-7).  Feature services
     own *what* stale state to reclaim and its economic semantics — e.g. the
     ``game_state`` provider (``services.game_state_cleanup``) refunds staked
     coins on abandoned rows before deleting them (ADR-002).  ``session_gc``
     only schedules the sweep; it no longer knows any feature's domain rules,
     so it no longer imports the economy or game-state services.

The GC is started as an asyncio Task from bot1.py's main() after db.init().
Feature providers are registered (e.g. ``game_state_cleanup.install()``) by
bot1 before ``start()`` is called.

Public surface:
    start(bot) → asyncio.Task  — call once at startup
"""

from __future__ import annotations

import asyncio
import logging
import time

from core.runtime import cleanup_registry, navigation_stack, scope_locks
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
            # RC-7: feature services own stale-state cleanup + refund semantics;
            # the GC just runs every registered provider and aggregates counts.
            feature_cleanup = await cleanup_registry.run_all()
            # F-2 / S1.2: safety-net reclamation of scope_locks that
            # cogs missed forget()-ing on edge teardown paths.  Held
            # locks are never reclaimed.
            scope_locks_swept = scope_locks.sweep_idle()
            active_count = await db.count_active_sessions()
            _metrics.session_active_count.set(active_count)
            if (
                expired_ids
                or anchors_removed
                or feature_cleanup.removed
                or feature_cleanup.refunded
                or scope_locks_swept
            ):
                logger.info(
                    "GC sweep complete — %d session(s), %d anchor(s), "
                    "%d stale feature-state row(s) removed (%d refund(s)), "
                    "%d scope_lock(s) idle-swept",
                    len(expired_ids),
                    anchors_removed,
                    feature_cleanup.removed,
                    feature_cleanup.refunded,
                    scope_locks_swept,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("GC sweep error: %s", exc, exc_info=True)


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
