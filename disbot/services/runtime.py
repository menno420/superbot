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
import time
import uuid

from utils.db import runtime_lock

logger = logging.getLogger("bot.services.runtime")

BOOT_ID: uuid.UUID = uuid.uuid4()

DEFAULT_HEARTBEAT_SECONDS: int = 30
_HEARTBEAT_FAILURE_LIMIT: int = 3

# LP-4: rolling-deploy handoff. When another fresh replica still holds
# the runtime lock at boot, poll for up to ``DEFAULT_BOOT_WAIT_SECONDS``
# rather than exit-zeroing immediately. 150 s comfortably covers a
# graceful old-replica drain (heartbeat 30 s + drain budget 5 s + DB
# close) plus margin for slow networks. Operators override per
# environment via the env knobs below; Railway's default healthcheck
# window must be at least the wait budget or new replicas will be
# rotated out as unhealthy before they can claim the lock.
DEFAULT_BOOT_WAIT_SECONDS: float = 150.0
DEFAULT_BOOT_POLL_SECONDS: float = 5.0


def _env_float(name: str, default: float) -> float:
    """Read a positive float from an env var, falling back on parse error."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning(
            "Invalid %s=%r; using default %.1fs.",
            name,
            raw,
            default,
        )
        return default
    if value < 0:
        logger.warning(
            "%s=%.1f is negative; using default %.1fs.",
            name,
            value,
            default,
        )
        return default
    return value


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
    boot_wait_seconds: float | None = None,
    boot_poll_seconds: float | None = None,
) -> None:
    """Claim the runtime lock or exit the process cleanly.

    LP-4: when another fresh replica holds the lock at boot, poll up
    to ``boot_wait_seconds`` (env ``RUNTIME_LOCK_BOOT_WAIT_SECONDS``,
    default 150 s) for it to release, rather than exit-zeroing on the
    first attempt. This smooths rolling-deploy handoffs where the new
    replica boots before the old one has finished draining. On
    timeout we still exit 0 so the orchestration platform leaves this
    replica idle.

    Exit code 0 when the lock is held by a fresh peer after the wait
    budget elapses — normal multi-replica handoff, not a crash.

    Exit code 1 when the underlying DB call fails — we want the
    orchestration platform to restart and retry. The DB failure is
    logged before exit.
    """
    if boot_wait_seconds is None:
        boot_wait_seconds = _env_float(
            "RUNTIME_LOCK_BOOT_WAIT_SECONDS",
            DEFAULT_BOOT_WAIT_SECONDS,
        )
    if boot_poll_seconds is None:
        boot_poll_seconds = _env_float(
            "RUNTIME_LOCK_BOOT_POLL_SECONDS",
            DEFAULT_BOOT_POLL_SECONDS,
        )
    # Sanity: poll must be > 0 and strictly less than wait so the loop
    # makes progress. If misconfigured, fall back to safe values.
    if boot_wait_seconds > 0 and (
        boot_poll_seconds <= 0 or boot_poll_seconds >= boot_wait_seconds
    ):
        logger.warning(
            "RUNTIME_LOCK_BOOT_POLL_SECONDS=%.1f vs "
            "RUNTIME_LOCK_BOOT_WAIT_SECONDS=%.1f — using min(1s, wait) "
            "for poll.",
            boot_poll_seconds,
            boot_wait_seconds,
        )
        boot_poll_seconds = min(1.0, boot_wait_seconds)

    started_at = time.monotonic()
    deadline = started_at + boot_wait_seconds
    attempts = 0
    while True:
        attempts += 1
        try:
            result = await runtime_lock.try_acquire(
                boot_id,
                lock_name=lock_name,
                stale_after_seconds=stale_after_seconds,
            )
        except Exception as exc:
            logger.critical(
                "runtime_lock.try_acquire failed: %s — exiting so the "
                "orchestration platform restarts this replica.",
                exc,
                exc_info=True,
            )
            raise SystemExit(1) from exc

        elapsed = time.monotonic() - started_at
        if result.acquired:
            logger.info(
                "Runtime lock acquired (lock_name=%s boot_id=%s "
                "attempts=%d wait=%.1fs).",
                lock_name,
                boot_id,
                attempts,
                elapsed,
            )
            _record_handoff_outcome(
                "acquired_after_wait" if attempts > 1 else "acquired_immediate",
                elapsed,
            )
            return

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.warning(
                "Runtime lock held by another live replica after "
                "%.1fs of waiting (lock_name=%s holder_boot_id=%s "
                "last_heartbeat=%s reason=%s attempts=%d). Exiting "
                "cleanly so the orchestration platform leaves this "
                "replica idle.",
                elapsed,
                lock_name,
                result.holder_boot_id,
                result.holder_heartbeat_at,
                result.reason,
                attempts,
            )
            _record_handoff_outcome("timeout", elapsed)
            raise SystemExit(0)

        sleep_for = min(boot_poll_seconds, remaining)
        logger.info(
            "Runtime lock held by peer (holder=%s heartbeat=%s "
            "reason=%s attempt=%d); retrying in %.1fs "
            "(remaining=%.1fs of %.1fs budget).",
            result.holder_boot_id,
            result.holder_heartbeat_at,
            result.reason,
            attempts,
            sleep_for,
            remaining,
            boot_wait_seconds,
        )
        await asyncio.sleep(sleep_for)


def _record_handoff_outcome(outcome: str, elapsed_seconds: float) -> None:
    """Update boot-handoff metrics, swallowing import errors so the
    runtime path never depends on prometheus_client being installed.
    """
    try:
        from services import metrics as _metrics

        _metrics.runtime_lock_boot_handoff_total.labels(outcome=outcome).inc()
        _metrics.runtime_lock_boot_wait_seconds.observe(elapsed_seconds)
    except Exception:
        logger.debug("Boot-handoff metric not recorded (metrics unavailable).")


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
    from services import metrics as _metrics

    consecutive_failures = 0
    while not stop_event.is_set():
        try:
            owned = await runtime_lock.heartbeat(
                boot_id,
                lock_name=lock_name,
            )
        except Exception as exc:
            consecutive_failures += 1
            _metrics.runtime_lock_heartbeat_total.labels(outcome="error").inc()
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
                _metrics.runtime_lock_heartbeat_total.labels(outcome="lost").inc()
                logger.critical(
                    "Runtime lock no longer owned by this boot "
                    "(lock_name=%s boot_id=%s). Another replica has "
                    "taken over — exiting immediately.",
                    lock_name,
                    boot_id,
                )
                os._exit(1)
            _metrics.runtime_lock_heartbeat_total.labels(outcome="ok").inc()
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


def diagnostics_snapshot() -> dict[str, str]:
    """LP-6: sync snapshot of the runtime-lock state for the
    :mod:`services.diagnostics_service` registry.

    Exposes only what is already known in-process — boot identity and
    lock name. DB-backed introspection (live holder, heartbeat age)
    requires an async query and is intentionally out of scope here; a
    future provider may surface it via a cached value updated by the
    heartbeat loop.
    """
    return {
        "boot_id": str(BOOT_ID),
        "lock_name": runtime_lock.DEFAULT_LOCK_NAME,
    }


# Self-register at import time (see lifecycle.py for the pattern).
try:
    from services import diagnostics_service as _diagnostics_service

    _diagnostics_service.register("runtime_lock", diagnostics_snapshot)
except Exception:  # noqa: BLE001 — diagnostics is observability only
    pass


__all__ = [
    "BOOT_ID",
    "DEFAULT_HEARTBEAT_SECONDS",
    "BootIdFilter",
    "acquire_lock_or_exit",
    "diagnostics_snapshot",
    "install_boot_id_logging",
    "release_lock_best_effort",
    "run_heartbeat_loop",
]
