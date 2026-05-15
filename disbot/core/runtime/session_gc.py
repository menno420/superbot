"""Background session garbage collector.

Runs every SESSION_GC_INTERVAL seconds (default: 5 minutes) and:
  1. Deletes runtime_sessions older than SESSION_TTL seconds (default: 2 hours).
     Cascade delete removes associated runtime_session_state rows.
  2. Deletes panel_anchors marked is_stale=TRUE.

The GC is started as an asyncio Task from bot1.py's main() after db.init().

Public surface:
    start(bot) → asyncio.Task  — call once at startup
"""

from __future__ import annotations

import asyncio
import logging
import time

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
            sessions_removed = await db.delete_expired_sessions(cutoff)
            anchors_removed = await db.delete_stale_panel_anchors()
            active_count = await db.count_active_sessions()
            _metrics.session_active_count.set(active_count)
            if sessions_removed or anchors_removed:
                logger.info(
                    "GC sweep complete — %d session(s), %d anchor(s) removed",
                    sessions_removed,
                    anchors_removed,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("GC sweep error: %s", exc, exc_info=True)


def start() -> asyncio.Task:
    """Create and return the background GC task.

    Must be called inside a running asyncio event loop (i.e., after bot startup).
    The caller is responsible for cancelling the task on shutdown.
    """
    task = asyncio.create_task(_run_gc_loop(), name="session_gc")
    logger.info(
        "Session GC started — TTL=%ds, interval=%ds", SESSION_TTL, SESSION_GC_INTERVAL
    )
    return task
