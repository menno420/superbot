"""Runtime instance lock orchestration (boot identity + heartbeat).

Provides:

* :data:`BOOT_ID` — process-unique UUID generated at import time. Every
  log record carries this so multi-replica deploys are debuggable.
* :class:`BootIdFilter` — :mod:`logging` filter that injects ``boot_id``
  on every record. Install on the root handlers before any log call.
* :func:`install_boot_id_logging` — attach the filter to a handler set.
* :func:`acquire_lock_or_exit` — claim the runtime lock or exit cleanly.
* :func:`run_heartbeat_loop` — supervised refresh of the lock's
  ``heartbeat_at``; exits the process on persistent failure.
* :func:`release_lock_best_effort` — atexit / shutdown hook.

The lock model is documented in :mod:`utils.db.runtime_lock`. This
module is the only orchestrator allowed to talk to that primitive set
from the bot's entry point.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from utils.db import runtime_lock

logger = logging.getLogger("bot.services.runtime")

BOOT_ID: uuid.UUID = uuid.uuid4()

DEFAULT_HEARTBEAT_SECONDS: int = 30
_HEARTBEAT_FAILURE_LIMIT: int = 3


class BootIdFilter(logging.Filter):
    """Stamp ``boot_id`` on every log record.

    Attached to handlers (not loggers) so every record that reaches a
    handler carries the field even if the originating logger has its
    own propagate=False configuration.
    """

    def __init__(self, boot_id: uuid.UUID = BOOT_ID) -> None:
        super().__init__()
        self._boot_id_str = str(boot_id)

    def filter(self, record: logging.LogRecord) -> bool:
        # Always set — overrides any caller-supplied extra={"boot_id": ...}
        # so we have a single source of truth.
        record.boot_id = self._boot_id_str
        return True


def install_boot_id_logging(
    handlers: list[logging.Handler],
    *,
    boot_id: uuid.UUID = BOOT_ID,
) -> None:
    """Attach a :class:`BootIdFilter` to every handler.

    Idempotent: re-installing on a handler that already has the filter
    is a no-op.
    """
    for handler in handlers:
        already = any(isinstance(f, BootIdFilter) for f in handler.filters)
        if not already:
            handler.addFilter(BootIdFilter(boot_id))


async def acquire_lock_or_exit(
    *,
    boot_id: uuid.UUID = BOOT_ID,
    lock_name: str = runtime_lock.DEFAULT_LOCK_NAME,
    stale_after_seconds: int = runtime_lock.DEFAULT_STALE_AFTER_SECONDS,
) -> None:
    """Claim the runtime lock or exit the process cleanly.

    Exit code 0 (not 1) when the lock is held by a fresh peer — this is
    a normal multi-replica scenario, not a crash, so Railway should not
    restart the loser.

    Exit code 1 when the underlying DB call fails — we want Railway to
    restart and retry. The DB failure is logged before exit.
    """
    try:
        result = await runtime_lock.try_acquire(
            boot_id,
            lock_name=lock_name,
            stale_after_seconds=stale_after_seconds,
        )
    except Exception as exc:
        logger.critical(
            "runtime_lock.try_acquire failed: %s — exiting so Railway "
            "restarts this replica.",
            exc,
            exc_info=True,
        )
        raise SystemExit(1) from exc

    if result.acquired:
        logger.info(
            "Runtime lock acquired (lock_name=%s boot_id=%s).",
            lock_name,
            boot_id,
        )
        return

    holder = result.holder_boot_id
    heartbeat = result.holder_heartbeat_at
    logger.warning(
        "Runtime lock held by another live replica "
        "(lock_name=%s holder_boot_id=%s last_heartbeat=%s reason=%s). "
        "Exiting cleanly so Railway leaves this replica idle.",
        lock_name,
        holder,
        heartbeat,
        result.reason,
    )
    raise SystemExit(0)


async def run_heartbeat_loop(
    stop_event: asyncio.Event,
    *,
    boot_id: uuid.UUID = BOOT_ID,
    lock_name: str = runtime_lock.DEFAULT_LOCK_NAME,
    interval_seconds: int = DEFAULT_HEARTBEAT_SECONDS,
) -> None:
    """Refresh ``heartbeat_at`` every ``interval_seconds`` until stopped.

    Behavior:

    * On a single transient DB failure: log and try again next tick.
    * After :data:`_HEARTBEAT_FAILURE_LIMIT` consecutive failures: log
      CRITICAL and exit (``os._exit(1)``) — we do NOT want a process
      to keep running with a stale lock that another replica may have
      already reclaimed.
    * On a successful ``UPDATE 0`` (the row no longer matches our
      ``boot_id``): treat as fatal; another replica won. Exit
      immediately so we don't double-respond.
    """
    consecutive_failures = 0
    while not stop_event.is_set():
        try:
            owned = await runtime_lock.heartbeat(
                boot_id,
                lock_name=lock_name,
            )
        except Exception as exc:
            consecutive_failures += 1
            logger.warning(
                "runtime_lock.heartbeat failed (%d/%d): %s",
                consecutive_failures,
                _HEARTBEAT_FAILURE_LIMIT,
                exc,
            )
            if consecutive_failures >= _HEARTBEAT_FAILURE_LIMIT:
                logger.critical(
                    "runtime_lock.heartbeat: %d consecutive failures — "
                    "exiting so a healthy replica can take over.",
                    consecutive_failures,
                )
                os._exit(1)
        else:
            if not owned:
                logger.critical(
                    "Runtime lock no longer owned by this boot "
                    "(lock_name=%s boot_id=%s). Another replica has "
                    "taken over — exiting immediately.",
                    lock_name,
                    boot_id,
                )
                os._exit(1)
            consecutive_failures = 0
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            continue


async def release_lock_best_effort(
    *,
    boot_id: uuid.UUID = BOOT_ID,
    lock_name: str = runtime_lock.DEFAULT_LOCK_NAME,
) -> None:
    """Drop the ``bot_runtime_lock`` row owned by this boot.

    Best effort: any exception is logged and swallowed. Called from the
    shutdown path so a clean SIGTERM frees the lock immediately rather
    than waiting ``stale_after_seconds`` for the heartbeat to age out.
    """
    try:
        await runtime_lock.release(boot_id, lock_name=lock_name)
        logger.info(
            "Runtime lock released (lock_name=%s boot_id=%s).",
            lock_name,
            boot_id,
        )
    except Exception as exc:
        logger.warning(
            "runtime_lock.release skipped (lock_name=%s boot_id=%s): %s",
            lock_name,
            boot_id,
            exc,
        )


__all__ = [
    "BOOT_ID",
    "DEFAULT_HEARTBEAT_SECONDS",
    "BootIdFilter",
    "acquire_lock_or_exit",
    "install_boot_id_logging",
    "release_lock_best_effort",
    "run_heartbeat_loop",
]
