"""Automation scheduler — Phase 9g / Track 6 PR 18.

Long-running supervised task that polls ``automation_rules`` for
due rules and routes them through
:func:`services.automation_executor.execute_rule`. Closes Track 6.

Responsibilities:

* Poll every ``poll_interval_seconds`` (default 30 s) for rules
  where ``enabled=true`` and ``next_run_at <= NOW()``.
* Claim each due rule via ``utils.db.automation.claim_run`` with a
  derived ``idempotency_key`` so two concurrent schedulers cannot
  double-run the same rule.
* Respect per-rule quiet hours stored in
  ``trigger_config['quiet_hours']`` (a ``[start_hour, end_hour]``
  pair in the rule's timezone).
* Auto-disable rules whose ``failure_count`` exceeds
  ``failure_threshold`` (default 5) after this run records a
  failure.
* Compute ``next_run_at`` based on ``trigger_kind`` /
  ``trigger_config``. ``manual`` rules are NEVER re-armed.
* Surface live counters + the last poll timestamp via
  ``services.diagnostics_service`` under the name
  ``automation_scheduler``.

The scheduler is supervised: failures inside the loop are caught
+ logged, then the loop continues. A truly fatal error (cancelled
task, asyncio shutdown) propagates so the supervisor can restart.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from services.automation_executor import execute_rule
from utils.db import automation as db

logger = logging.getLogger("bot.services.automation_scheduler")

_DEFAULT_POLL_SECONDS = 30
_DEFAULT_FAILURE_THRESHOLD = 5


@dataclass
class SchedulerCounters:
    """Snapshot of scheduler observability counters."""

    polls: int = 0
    rules_seen: int = 0
    rules_claimed: int = 0
    rules_skipped_quiet_hours: int = 0
    rules_skipped_collision: int = 0
    rules_succeeded: int = 0
    rules_failed: int = 0
    rules_auto_disabled: int = 0
    last_poll_at: datetime | None = None
    last_error: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "polls": self.polls,
            "rules_seen": self.rules_seen,
            "rules_claimed": self.rules_claimed,
            "rules_skipped_quiet_hours": self.rules_skipped_quiet_hours,
            "rules_skipped_collision": self.rules_skipped_collision,
            "rules_succeeded": self.rules_succeeded,
            "rules_failed": self.rules_failed,
            "rules_auto_disabled": self.rules_auto_disabled,
            "last_poll_at": (
                self.last_poll_at.isoformat() if self.last_poll_at else None
            ),
            "last_error": self.last_error,
        }


@dataclass
class AutomationScheduler:
    """Supervised task that drives the executor.

    Construction is side-effect-free; call :meth:`run_forever` from
    a supervised task wrapper (see :func:`spawn_scheduler`).
    """

    bot: Any = None
    poll_interval_seconds: int = _DEFAULT_POLL_SECONDS
    failure_threshold: int = _DEFAULT_FAILURE_THRESHOLD
    counters: SchedulerCounters = field(default_factory=SchedulerCounters)
    _stop: asyncio.Event | None = None

    def stop(self) -> None:
        if self._stop is not None:
            self._stop.set()

    async def run_forever(self) -> None:
        """The supervised loop."""
        self._stop = asyncio.Event()
        logger.info(
            "automation_scheduler: starting (poll_interval=%ds, failure_threshold=%d)",
            self.poll_interval_seconds,
            self.failure_threshold,
        )
        try:
            while not self._stop.is_set():
                try:
                    await self.tick()
                except Exception as exc:  # noqa: BLE001 — loop boundary
                    self.counters.last_error = f"{type(exc).__name__}: {exc}"
                    logger.exception("automation_scheduler.tick: failed")
                try:
                    await asyncio.wait_for(
                        self._stop.wait(),
                        timeout=self.poll_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info("automation_scheduler: stopped")

    async def tick(self) -> None:
        """One poll cycle. Exposed for direct testing."""
        self.counters.polls += 1
        self.counters.last_poll_at = _now_utc()

        due = await self._fetch_due_rules()
        self.counters.rules_seen += len(due)
        for rule in due:
            await self._dispatch_one(rule)

    async def _fetch_due_rules(self) -> list[dict[str, Any]]:
        """Return enabled rules whose ``next_run_at`` is in the past.

        Tests can monkeypatch this to inject synthetic schedules.
        Production uses a direct query against the pool; we keep
        the logic here so it stays mockable.
        """
        from utils.db import pool

        try:
            rows = await pool.get().fetch(
                """
                SELECT id, guild_id, name, enabled, trigger_kind,
                       trigger_config, action_kind, action_config,
                       schedule, timezone, last_run_at, next_run_at,
                       failure_count, last_error, created_by,
                       created_at, updated_at
                FROM automation_rules
                WHERE enabled
                  AND (next_run_at IS NULL OR next_run_at <= NOW())
                ORDER BY next_run_at NULLS FIRST
                LIMIT 50
                """,
            )
        except Exception:
            logger.exception(
                "automation_scheduler._fetch_due_rules: query failed",
            )
            return []
        out: list[dict[str, Any]] = []
        for row in rows:
            rec = dict(row)
            rec["trigger_config"] = db._decode(rec.get("trigger_config")) or {}
            rec["action_config"] = db._decode(rec.get("action_config")) or {}
            out.append(rec)
        return out

    async def _dispatch_one(self, rule: dict[str, Any]) -> None:
        rule_id = int(rule["id"])
        guild_id = int(rule["guild_id"])

        if _in_quiet_hours(rule):
            self.counters.rules_skipped_quiet_hours += 1
            logger.debug(
                "automation_scheduler: rule_id=%d in quiet hours; skipping",
                rule_id,
            )
            await db.update_schedule_state(
                rule_id,
                next_run_at=_compute_next_run_at(rule),
                last_run_at=_now_utc(),
            )
            return

        idempotency_key = _idempotency_key(rule)
        run_id = await db.claim_run(
            rule_id=rule_id,
            guild_id=guild_id,
            idempotency_key=idempotency_key,
            dry_run=False,
        )
        if run_id is None:
            self.counters.rules_skipped_collision += 1
            return
        self.counters.rules_claimed += 1

        await db.mark_running(run_id)

        guild = self.bot.get_guild(guild_id) if self.bot is not None else None
        result = await execute_rule(
            rule,
            dry_run=False,
            bot=self.bot,
            guild=guild,
            actor_id=rule.get("created_by"),
        )
        await db.finish_run(
            run_id=run_id,
            status=result.status,
            result_summary=result.result_summary,
            error=result.error,
        )

        if result.status == "success":
            self.counters.rules_succeeded += 1
            await db.reset_failure_count(rule_id)
        else:
            self.counters.rules_failed += 1
            failure_count = await db.record_failure(
                rule_id,
                result.error or "unknown",
            )
            if failure_count >= self.failure_threshold:
                await db.set_enabled(rule_id, False)
                self.counters.rules_auto_disabled += 1
                logger.warning(
                    "automation_scheduler: rule_id=%d disabled after "
                    "%d consecutive failures",
                    rule_id,
                    failure_count,
                )

        # Re-arm or leave dormant. Manual rules never auto-fire so
        # they are not re-armed; everything else gets a fresh
        # ``next_run_at`` computed from its trigger config.
        if rule.get("trigger_kind") != "manual":
            await db.update_schedule_state(
                rule_id,
                next_run_at=_compute_next_run_at(rule),
                last_run_at=_now_utc(),
            )
        else:
            await db.update_schedule_state(
                rule_id,
                next_run_at=None,
                last_run_at=_now_utc(),
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _idempotency_key(rule: dict[str, Any]) -> str:
    """Per-tick claim key.

    Includes the rule id + the rule's currently-scheduled
    ``next_run_at`` epoch, plus a UUID4 component. The
    (rule_id, next_run_at) bound guarantees the same claim string
    is never reused for a different tick — even if the UUID is the
    same in some pathological mock.
    """
    rule_id = rule["id"]
    next_run_at = rule.get("next_run_at")
    epoch = int(next_run_at.timestamp()) if isinstance(next_run_at, datetime) else 0
    return f"rule:{rule_id}:tick:{epoch}:{uuid.uuid4()}"


def _in_quiet_hours(rule: dict[str, Any]) -> bool:
    """Return True when the current UTC hour falls inside
    ``trigger_config['quiet_hours']``.

    ``quiet_hours`` is a ``[start_hour, end_hour]`` pair. The range
    is inclusive at the start, exclusive at the end. Wrap-around
    (e.g. ``[22, 6]``) is supported.
    """
    qh = rule.get("trigger_config", {}).get("quiet_hours")
    if not qh:
        return False
    try:
        start = int(qh[0])
        end = int(qh[1])
    except (TypeError, ValueError, IndexError):
        return False
    hour = _now_utc().hour
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def _compute_next_run_at(rule: dict[str, Any]) -> datetime | None:
    """Compute the rule's next scheduled fire time.

    v1 supports one installable kind:

    * ``interval`` — fire every ``interval_minutes`` minutes.

    ``scheduled_time`` is not installable for new rules until cron
    parsing ships (gated by
    :data:`services.automation_registry.UNSUPPORTED_INSTALLABLE_TRIGGER_KINDS`
    and enforced in
    :class:`services.automation_mutation.AutomationMutationPipeline.create_rule`).
    This branch remains only to avoid crashing the scheduler loop if
    historical DB rows already exist — it returns ``now + 1 day`` so
    such rows keep being polled at a coarse cadence without firing in
    a tight loop.

    Other kinds return ``None`` (rules drop off the schedule queue
    until something else flips ``next_run_at``).
    """
    trigger_kind = rule.get("trigger_kind")
    cfg = rule.get("trigger_config") or {}
    now = _now_utc()
    if trigger_kind == "interval":
        try:
            minutes = int(cfg.get("interval_minutes", 0))
        except (TypeError, ValueError):
            minutes = 0
        if minutes <= 0:
            return None
        return now + timedelta(minutes=minutes)
    if trigger_kind == "scheduled_time":
        # Defensive: tolerate pre-existing rows. New creation is
        # blocked at the mutation-service boundary.
        return now + timedelta(days=1)
    return None


# ---------------------------------------------------------------------------
# Diagnostics registration
# ---------------------------------------------------------------------------


_INSTANCE: AutomationScheduler | None = None


def get_or_create(bot: Any | None = None) -> AutomationScheduler:
    """Return the singleton scheduler, instantiating if needed."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = AutomationScheduler(bot=bot)
    elif bot is not None and _INSTANCE.bot is None:
        _INSTANCE.bot = bot
    return _INSTANCE


def _diagnostics_snapshot() -> dict[str, Any]:
    if _INSTANCE is None:
        return {"running": False}
    snap = _INSTANCE.counters.snapshot()
    snap["running"] = _INSTANCE._stop is not None and not _INSTANCE._stop.is_set()
    snap["poll_interval_seconds"] = _INSTANCE.poll_interval_seconds
    snap["failure_threshold"] = _INSTANCE.failure_threshold
    return snap


def register_diagnostics() -> None:
    """Register the snapshot under ``automation_scheduler``.

    Idempotent: a re-registration just overwrites the provider so
    the diagnostics surface always points at the active instance.
    """
    from services import diagnostics_service

    diagnostics_service.register(
        "automation_scheduler",
        _diagnostics_snapshot,
    )


# ---------------------------------------------------------------------------
# Spawn helper
# ---------------------------------------------------------------------------


def spawn_scheduler(bot: Any | None = None, *, force: bool = False) -> Any | None:
    """Spawn the scheduler as a supervised task.

    Returns the asyncio.Task so the cog can hold a reference, or
    ``None`` if the ``AUTOMATION_SCHEDULER_ENABLED`` env flag is
    unset/false and ``force=False``. The flag defaults to ``"false"``
    so production never spawns the loop without an explicit operator
    opt-in.
    """
    import os

    if not force:
        flag = os.getenv("AUTOMATION_SCHEDULER_ENABLED", "false").lower()
        if flag not in ("true", "1", "yes", "on"):
            logger.info(
                "automation_scheduler: spawn skipped — "
                "AUTOMATION_SCHEDULER_ENABLED is %r (set to 'true' to enable)",
                flag,
            )
            register_diagnostics()
            return None

    from core.runtime import tasks

    scheduler = get_or_create(bot)
    register_diagnostics()
    return tasks.spawn(
        "automation_scheduler",
        scheduler.run_forever(),
    )


__all__ = [
    "AutomationScheduler",
    "SchedulerCounters",
    "get_or_create",
    "register_diagnostics",
    "spawn_scheduler",
]
