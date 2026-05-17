"""Managed background-task helper.

Wraps ``asyncio.create_task`` to provide lifecycle guarantees that bare
``create_task`` does not:

- A strong reference is held inside this module until the task completes.
  ``asyncio.create_task`` otherwise lets the task be garbage-collected
  mid-flight (PEP 8.5 trap) when callers don't keep the return value.
- Unhandled exceptions are logged with full traceback at ERROR — without
  this, a failed background task is invisible unless ``loop.set_exception_handler``
  is configured.
- The ``task_outcome_total{name, outcome}`` Prometheus counter is
  incremented on every completion (``ok`` / ``error`` / ``cancelled``).
- ``cancel_all()`` is provided for cooperative shutdown — callers no longer
  need to track tasks themselves to cancel them.

This module addresses CRIT-1 (unmanaged tasks) from the platform-hardening
plan.  Cog and runtime code that previously did

    asyncio.create_task(self._save_guild(guild_id))

should migrate to

    from core.runtime import tasks
    tasks.spawn(f"save_guild:{guild_id}", self._save_guild(guild_id))

Task names should follow ``<subsystem>:<short-purpose>[:<id>]`` so the
metric labels stay readable.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from services import metrics

logger = logging.getLogger("bot.runtime.tasks")

# Strong references held until tasks complete.  Module-level set so callers
# may discard the return value of spawn() without risking GC.
_TASKS: set[asyncio.Task[Any]] = set()


def spawn(name: str, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
    """Spawn a managed background task and return the ``asyncio.Task``.

    The task is held in a module-level set until it completes; callers do
    not need to retain the return value to keep it alive.

    Args:
        name: Identifier used for logging and the ``task_outcome_total``
            metric label.  Convention: ``<subsystem>:<short-purpose>``.
        coro: The coroutine to run.

    Returns:
        The created ``asyncio.Task``.  Callers may await or cancel it,
        but discarding the return value is safe.
    """
    task = asyncio.create_task(coro, name=name)
    _TASKS.add(task)
    task.add_done_callback(_on_done)
    return task


def _on_done(task: asyncio.Task[Any]) -> None:
    """Done-callback: drop strong ref, log exceptions, increment metric."""
    _TASKS.discard(task)
    name = task.get_name()
    if task.cancelled():
        metrics.task_outcome_total.labels(name=name, outcome="cancelled").inc()
        return
    exc = task.exception()
    if exc is not None:
        metrics.task_outcome_total.labels(name=name, outcome="error").inc()
        logger.error("Managed task %r failed", name, exc_info=exc)
        return
    metrics.task_outcome_total.labels(name=name, outcome="ok").inc()


def active() -> set[asyncio.Task[Any]]:
    """Return a snapshot of currently-running spawned tasks."""
    return {t for t in _TASKS if not t.done()}


def count() -> int:
    """Return the number of currently-running spawned tasks."""
    return len(active())


def cancel_all() -> None:
    """Cancel every still-running spawned task.

    Intended for cooperative shutdown (called from the bot's main()
    ``finally`` clause).  Already-completed tasks are ignored.
    """
    for t in list(_TASKS):
        if not t.done():
            t.cancel()


def cancel_by_prefix(prefix: str) -> int:
    """Cancel every still-running spawned task whose name starts with *prefix*.

    Intended for cog ``cog_unload`` hooks so a cog reload doesn't leak
    its in-flight background work.  Convention: name tasks as
    ``"<subsystem>:<purpose>[:<id>]"`` and pass ``"<subsystem>:"`` as
    the prefix.

    Returns the number of tasks that were cancelled (already-done
    tasks are skipped).
    """
    cancelled = 0
    for t in list(_TASKS):
        if t.done():
            continue
        if t.get_name().startswith(prefix):
            t.cancel()
            cancelled += 1
    return cancelled


# ---------------------------------------------------------------------------
# Diagnostics registration — Phase S1.3
# ---------------------------------------------------------------------------

from services import diagnostics_service as _diag  # noqa: E402


def _diagnostics_snapshot() -> dict[str, object]:
    """Snapshot of managed-task state for ``!platform tasks``."""
    running = active()
    return {
        "active_count": len(running),
        "names": sorted(t.get_name() for t in running),
    }


_diag.register("tasks", _diagnostics_snapshot)
