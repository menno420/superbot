"""BTD6 ingestion supervisor — drives scheduled refresh cycles.

Disabled by default (BTD6_INGESTION_ENABLED=false).  Set the env var
to 'true' to enable.  Designed to be started from BTD6Cog.cog_load()
and stopped from cog_unload().

Lifecycle guarantees (INV-K via core.runtime.tasks):
- start_supervisor() is idempotent: no-op if already running.
- stop_supervisor() signals the loop to exit and waits for the
  current cycle to finish (up to STOP_TIMEOUT_S).
- cog_unload() calls stop_supervisor() before cancel_by_prefix() so
  in-progress ingestion run rows are finalized before tasks are
  force-cancelled.

On startup, stale 'running' rows from a previous crash are recovered
to status='interrupted', error_code='supervisor_restart'.
"""

from __future__ import annotations

import asyncio
import logging
import os

from core.runtime import tasks
from services import btd6_ingestion_service
from utils.db import btd6_sources as btd6_sources_db

logger = logging.getLogger("bot.services.btd6_ingestion_supervisor")

_BTD6_INGESTION_ENABLED: bool = (
    os.getenv("BTD6_INGESTION_ENABLED", "false").lower() == "true"
)
_STARTUP_DELAY_S: int = int(os.getenv("BTD6_INGESTION_STARTUP_DELAY_S", "60"))
_DEFAULT_INTERVAL_S: int = int(os.getenv("BTD6_INGESTION_DEFAULT_INTERVAL_S", "3600"))
_STOP_TIMEOUT_S: int = 30

_SOURCE_INTERVALS: dict[str, int] = {
    # Live rotations — refresh frequently so the bot sees the current
    # race / boss / odyssey / event within ~one cycle.
    "nk_btd6_events": 1800,
    "nk_btd6_races": 1800,
    "nk_btd6_bosses": 1800,
    "nk_btd6_odyssey": 1800,
    # CT runs as a dependency parent: the supervisor calls
    # refresh_with_dependencies(nk_btd6_ct), which expands into the
    # per-tile child fetch automatically.
    "nk_btd6_ct": 1800,
    # Map directory is comparatively static; long backoff decay so a
    # single failure doesn't pin it offline for the rest of the day.
    "nk_btd6_maps": 86400,
}

_BACKOFF_BASE_S: int = 30
_BACKOFF_CAP_S: int = 3600

# ---------------------------------------------------------------------------
# Module-level state machine
# ---------------------------------------------------------------------------

_supervisor_task: asyncio.Task[None] | None = None
_stop_event: asyncio.Event = asyncio.Event()
_backoff: dict[str, int] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def start_supervisor() -> None:
    """Spawn the ingestion loop.  No-op if disabled or already running."""
    global _supervisor_task
    if not _BTD6_INGESTION_ENABLED:
        return
    if _supervisor_task is not None and not _supervisor_task.done():
        return
    try:
        recovered = await btd6_sources_db.mark_stale_runs_interrupted()
        if recovered:
            logger.warning(
                "recovered %d stale ingestion run(s) to interrupted",
                recovered,
            )
    except Exception:
        logger.warning(
            "failed to recover stale ingestion runs on startup",
            exc_info=True,
        )
    _stop_event.clear()
    _supervisor_task = tasks.spawn(
        "btd6_ingestion:supervisor",
        _run_loop(),
        on_error=_on_supervisor_error,
    )
    logger.info("BTD6 ingestion supervisor started")


async def stop_supervisor() -> None:
    """Signal the loop to exit and wait for it to complete."""
    global _supervisor_task
    _stop_event.set()
    task = _supervisor_task
    if task is None or task.done():
        return
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=_STOP_TIMEOUT_S)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logger.warning(
            "supervisor did not finish within %ds; continuing",
            _STOP_TIMEOUT_S,
        )
    logger.info("BTD6 ingestion supervisor stopped")


def _on_supervisor_error(task: asyncio.Task[None], exc: Exception) -> None:
    logger.critical("BTD6 ingestion supervisor crashed: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# Internal loop
# ---------------------------------------------------------------------------


async def _run_loop() -> None:
    logger.info("BTD6 ingestion loop waiting %ds before first cycle", _STARTUP_DELAY_S)
    try:
        await asyncio.sleep(_STARTUP_DELAY_S)
    except asyncio.CancelledError:
        return

    while not _stop_event.is_set():
        for source_key, interval_s in _SOURCE_INTERVALS.items():
            if _stop_event.is_set():
                break
            backoff = _backoff.get(source_key, 0)
            if backoff > 0:
                _backoff[source_key] = max(0, backoff - interval_s)
                continue
            try:
                child_task = tasks.spawn(
                    f"btd6_ingestion:refresh:{source_key}",
                    btd6_ingestion_service.refresh_with_dependencies(
                        source_key,
                        reason="scheduled",
                    ),
                )
                results = await child_task
                failed = [
                    r for r in results if r.status in ("fetch_error", "parse_error")
                ]
                if failed:
                    new_backoff = min(
                        _backoff.get(source_key, _BACKOFF_BASE_S) * 2,
                        _BACKOFF_CAP_S,
                    )
                    _backoff[source_key] = new_backoff
                    logger.warning(
                        "source %s failed (%s); backing off %ds",
                        source_key,
                        failed[0].error_code,
                        new_backoff,
                    )
                else:
                    _backoff.pop(source_key, None)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.error(
                    "unexpected error refreshing %s",
                    source_key,
                    exc_info=True,
                )

        if _stop_event.is_set():
            break
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=_DEFAULT_INTERVAL_S)
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            return


__all__ = ["start_supervisor", "stop_supervisor"]
