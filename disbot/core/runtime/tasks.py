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
from collections.abc import Callable, Coroutine
from typing import Any

from services import metrics

logger = logging.getLogger("bot.runtime.tasks")

# Strong references held until tasks complete.  Module-level set so callers
# may discard the return value of spawn() without risking GC.
_TASKS: set[asyncio.Task[Any]] = set()

# Per-task on_error hooks (PR-02a).  Populated by ``spawn`` when an
# ``on_error`` argument is supplied and consumed (popped) by
# ``_on_done`` once the task completes.  Keyed by task identity rather
# than by name because two short-lived tasks may transiently share a
# name across the metric label.
OnErrorHook = Callable[[asyncio.Task[Any], BaseException], None]
_ON_ERROR_HOOKS: dict[asyncio.Task[Any], OnErrorHook] = {}


def spawn(
    name: str,
    coro: Coroutine[Any, Any, Any],
    *,
    on_error: OnErrorHook | None = None,
) -> asyncio.Task[Any]:
    """Spawn a managed background task and return the ``asyncio.Task``.

    The task is held in a module-level set until it completes; callers do
    not need to retain the return value to keep it alive.

    Args:
        name: Identifier used for logging and the ``task_outcome_total``
            metric label.  Convention: ``<subsystem>:<short-purpose>``.
        coro: The coroutine to run.
        on_error: Optional sync callback invoked from the done-callback
            when the task raises a non-``CancelledError`` exception.
            Receives ``(task, exception)``.  Used by ``bot1.py``'s
            supervised-task wrapper (PR-02a) to surface CRITICAL logs
            plus webhook alerts without bot1 maintaining its own
            done-callback.  The hook must not raise; any exception it
            raises is logged and swallowed.

    Returns:
        The created ``asyncio.Task``.  Callers may await or cancel it,
        but discarding the return value is safe.
    """
    task = asyncio.create_task(coro, name=name)
    _TASKS.add(task)
    if on_error is not None:
        _ON_ERROR_HOOKS[task] = on_error
    task.add_done_callback(_on_done)
    return task


def _on_done(task: asyncio.Task[Any]) -> None:
    """Done-callback: drop strong ref, log exceptions, increment metric."""
    _TASKS.discard(task)
    on_error = _ON_ERROR_HOOKS.pop(task, None)
    name = task.get_name()
    if task.cancelled():
        metrics.task_outcome_total.labels(name=name, outcome="cancelled").inc()
        return
    exc = task.exception()
    if exc is not None:
        metrics.task_outcome_total.labels(name=name, outcome="error").inc()
        logger.error("Managed task %r failed", name, exc_info=exc)
        if on_error is not None:
            try:
                on_error(task, exc)
            except Exception:  # noqa: BLE001 — hook isolation
                logger.exception(
                    "on_error hook for managed task %r raised",
                    name,
                )
        return
    metrics.task_outcome_total.labels(name=name, outcome="ok").inc()


def active() -> set[asyncio.Task[Any]]:
    """Return a snapshot of currently-running spawned tasks."""
    return {t for t in _TASKS if not t.done()}


def count() -> int:
    """Return the number of currently-running spawned tasks."""
    return len(active())


def cancel_all() -> set[asyncio.Task[Any]]:
    """Cancel every still-running spawned task; return the cancelled snapshot.

    Captures the snapshot of still-running tasks **before** issuing the
    cancellation requests so the caller has a stable set to await on.
    Returning the snapshot avoids the fragile "cancel, then re-snapshot"
    pattern: a second call to ``active()`` after cancellation would
    technically race against any done-callbacks (none of which run
    between the two sync calls today, but the pattern breaks the
    moment a contributor inserts an ``await`` between them).

    Already-completed tasks are excluded from the returned set so a
    caller doing ``asyncio.wait(returned)`` does not block on tasks
    that finished before shutdown started.

    Intended for cooperative shutdown (called from the bot's main()
    ``finally`` clause).  Returning the snapshot also makes the
    "what did I just cancel?" question testable without inspecting
    module-private state.
    """
    cancelled: set[asyncio.Task[Any]] = set()
    for t in list(_TASKS):
        if t.done():
            continue
        t.cancel()
        cancelled.add(t)
    return cancelled


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
