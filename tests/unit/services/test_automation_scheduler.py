"""Phase 9g / Track 6 PR 18 — automation scheduler tests.

Pins:

* ``tick`` polls for due rules, claims via ``claim_run``, runs the
  executor, finishes the run with the result, and arms the next
  fire time.
* Quiet hours: a rule inside its ``quiet_hours`` window is
  skipped + re-armed, never executed.
* Idempotency collisions: ``claim_run`` returning None bumps the
  collision counter; the executor is not invoked.
* Auto-disable: a rule whose ``failure_count`` reaches the
  threshold gets ``set_enabled(False)``.
* Manual rules are not auto-rearmed.
* Diagnostics snapshot exposes counters + running state.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.automation_scheduler import (
    AutomationScheduler,
    SchedulerCounters,
    _compute_next_run_at,
    _idempotency_key,
    _in_quiet_hours,
    register_diagnostics,
)


def _rule(
    *,
    rule_id=7,
    guild_id=1,
    trigger_kind="interval",
    trigger_config=None,
    action_kind="notify_owner",
    action_config=None,
    next_run_at=None,
    enabled=True,
    failure_count=0,
):
    if trigger_config is None:
        trigger_config = {"interval_minutes": 5}
    if action_config is None:
        action_config = {"template": "hi"}
    return {
        "id": rule_id,
        "guild_id": guild_id,
        "name": "x",
        "enabled": enabled,
        "trigger_kind": trigger_kind,
        "trigger_config": trigger_config,
        "action_kind": action_kind,
        "action_config": action_config,
        "schedule": None,
        "timezone": "UTC",
        "last_run_at": None,
        "next_run_at": next_run_at,
        "failure_count": failure_count,
        "last_error": None,
        "created_by": 99,
        "created_at": None,
        "updated_at": None,
    }


@pytest.fixture
def _mock_db():
    with (
        patch(
            "services.automation_scheduler.db.claim_run",
            new_callable=AsyncMock,
        ) as claim_run,
        patch(
            "services.automation_scheduler.db.mark_running",
            new_callable=AsyncMock,
        ) as mark_running,
        patch(
            "services.automation_scheduler.db.finish_run",
            new_callable=AsyncMock,
        ) as finish_run,
        patch(
            "services.automation_scheduler.db.set_enabled",
            new_callable=AsyncMock,
        ) as set_enabled,
        patch(
            "services.automation_scheduler.db.record_failure",
            new_callable=AsyncMock,
        ) as record_failure,
        patch(
            "services.automation_scheduler.db.reset_failure_count",
            new_callable=AsyncMock,
        ) as reset_failure,
        patch(
            "services.automation_scheduler.db.update_schedule_state",
            new_callable=AsyncMock,
        ) as update_state,
        patch(
            "services.automation_scheduler.execute_rule",
            new_callable=AsyncMock,
        ) as execute,
    ):
        yield {
            "claim_run": claim_run,
            "mark_running": mark_running,
            "finish_run": finish_run,
            "set_enabled": set_enabled,
            "record_failure": record_failure,
            "reset_failure_count": reset_failure,
            "update_schedule_state": update_state,
            "execute_rule": execute,
        }


def _success_result():
    return MagicMock(
        status="success",
        result_summary={"sent": 1},
        error=None,
    )


def _failure_result(error="boom"):
    return MagicMock(
        status="failure",
        result_summary={},
        error=error,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_quiet_hours_simple_window():
    rule = _rule(trigger_config={"quiet_hours": [0, 23]})
    # Currently-UTC hour is in [0, 23) for almost the entire day.
    # Use a fixed hour via patching.
    with patch(
        "services.automation_scheduler._now_utc",
        return_value=datetime(2026, 5, 20, 10, 0, tzinfo=timezone.utc),
    ):
        assert _in_quiet_hours(rule) is True


def test_quiet_hours_wraparound_overnight():
    rule = _rule(trigger_config={"quiet_hours": [22, 6]})
    with patch(
        "services.automation_scheduler._now_utc",
        return_value=datetime(2026, 5, 20, 23, 0, tzinfo=timezone.utc),
    ):
        assert _in_quiet_hours(rule) is True
    with patch(
        "services.automation_scheduler._now_utc",
        return_value=datetime(2026, 5, 20, 3, 0, tzinfo=timezone.utc),
    ):
        assert _in_quiet_hours(rule) is True
    with patch(
        "services.automation_scheduler._now_utc",
        return_value=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
    ):
        assert _in_quiet_hours(rule) is False


def test_quiet_hours_absent_returns_false():
    assert _in_quiet_hours(_rule()) is False


def test_idempotency_key_includes_rule_and_next_run_epoch():
    when = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
    rule = _rule(next_run_at=when)
    key = _idempotency_key(rule)
    assert key.startswith(f"rule:7:tick:{int(when.timestamp())}:")


def test_compute_next_run_at_for_interval():
    rule = _rule(trigger_kind="interval", trigger_config={"interval_minutes": 30})
    when = _compute_next_run_at(rule)
    assert when is not None
    delta = when - datetime.now(timezone.utc)
    assert timedelta(minutes=29) < delta < timedelta(minutes=31)


def test_compute_next_run_at_for_manual_returns_none():
    rule = _rule(trigger_kind="manual")
    assert _compute_next_run_at(rule) is None


# ---------------------------------------------------------------------------
# tick — happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tick_dispatches_due_rule_success(_mock_db):
    scheduler = AutomationScheduler()
    rule = _rule()
    with patch.object(
        scheduler, "_fetch_due_rules", new=AsyncMock(return_value=[rule])
    ):
        _mock_db["claim_run"].return_value = 42
        _mock_db["execute_rule"].return_value = _success_result()
        await scheduler.tick()

    _mock_db["claim_run"].assert_awaited_once()
    _mock_db["mark_running"].assert_awaited_once_with(42)
    _mock_db["execute_rule"].assert_awaited_once()
    _mock_db["finish_run"].assert_awaited_once()
    _mock_db["reset_failure_count"].assert_awaited_once_with(7)
    # Re-armed via update_schedule_state.
    _mock_db["update_schedule_state"].assert_awaited()
    assert scheduler.counters.rules_claimed == 1
    assert scheduler.counters.rules_succeeded == 1


@pytest.mark.asyncio
async def test_tick_records_failure_and_increments_counter(_mock_db):
    scheduler = AutomationScheduler()
    rule = _rule()
    with patch.object(
        scheduler, "_fetch_due_rules", new=AsyncMock(return_value=[rule])
    ):
        _mock_db["claim_run"].return_value = 42
        _mock_db["execute_rule"].return_value = _failure_result()
        _mock_db["record_failure"].return_value = 1
        await scheduler.tick()

    _mock_db["record_failure"].assert_awaited_once_with(7, "boom")
    _mock_db["set_enabled"].assert_not_awaited()
    assert scheduler.counters.rules_failed == 1


@pytest.mark.asyncio
async def test_tick_auto_disables_after_threshold(_mock_db):
    scheduler = AutomationScheduler(failure_threshold=3)
    rule = _rule(failure_count=2)
    with patch.object(
        scheduler, "_fetch_due_rules", new=AsyncMock(return_value=[rule])
    ):
        _mock_db["claim_run"].return_value = 42
        _mock_db["execute_rule"].return_value = _failure_result()
        _mock_db["record_failure"].return_value = 3  # crosses threshold
        await scheduler.tick()

    _mock_db["set_enabled"].assert_awaited_once_with(7, False)
    assert scheduler.counters.rules_auto_disabled == 1


@pytest.mark.asyncio
async def test_tick_skips_quiet_hours_without_running_executor(_mock_db):
    scheduler = AutomationScheduler()
    rule = _rule(trigger_config={"interval_minutes": 5, "quiet_hours": [0, 23]})
    with (
        patch.object(scheduler, "_fetch_due_rules", new=AsyncMock(return_value=[rule])),
        patch(
            "services.automation_scheduler._now_utc",
            return_value=datetime(2026, 5, 20, 10, 0, tzinfo=timezone.utc),
        ),
    ):
        await scheduler.tick()

    _mock_db["execute_rule"].assert_not_awaited()
    _mock_db["claim_run"].assert_not_awaited()
    _mock_db["update_schedule_state"].assert_awaited()
    assert scheduler.counters.rules_skipped_quiet_hours == 1


@pytest.mark.asyncio
async def test_tick_skips_idempotency_collision_without_executing(_mock_db):
    scheduler = AutomationScheduler()
    rule = _rule()
    with patch.object(
        scheduler, "_fetch_due_rules", new=AsyncMock(return_value=[rule])
    ):
        _mock_db["claim_run"].return_value = None  # another scheduler beat us
        await scheduler.tick()

    _mock_db["execute_rule"].assert_not_awaited()
    _mock_db["mark_running"].assert_not_awaited()
    assert scheduler.counters.rules_skipped_collision == 1


@pytest.mark.asyncio
async def test_tick_manual_rule_does_not_rearm_next_run_at(_mock_db):
    scheduler = AutomationScheduler()
    rule = _rule(trigger_kind="manual", trigger_config={})
    with patch.object(
        scheduler, "_fetch_due_rules", new=AsyncMock(return_value=[rule])
    ):
        _mock_db["claim_run"].return_value = 42
        _mock_db["execute_rule"].return_value = _success_result()
        await scheduler.tick()

    call = _mock_db["update_schedule_state"].await_args
    assert call.kwargs["next_run_at"] is None


# ---------------------------------------------------------------------------
# Counters + diagnostics
# ---------------------------------------------------------------------------


def test_counters_snapshot_serialises_datetimes():
    counters = SchedulerCounters(
        polls=3,
        last_poll_at=datetime(2026, 5, 20, 10, 0, tzinfo=timezone.utc),
    )
    snap = counters.snapshot()
    assert snap["polls"] == 3
    assert isinstance(snap["last_poll_at"], str)


def test_register_diagnostics_calls_diagnostics_service():
    from services import automation_scheduler as mod

    mod._INSTANCE = AutomationScheduler()  # fresh
    with patch(
        "services.diagnostics_service.register",
    ) as reg_mock:
        register_diagnostics()
    reg_mock.assert_called_once()
    args = reg_mock.call_args.args
    assert args[0] == "automation_scheduler"


# ---------------------------------------------------------------------------
# spawn_scheduler env-flag gate
# ---------------------------------------------------------------------------


def test_spawn_scheduler_skips_when_env_flag_disabled(monkeypatch):
    """AUTOMATION_SCHEDULER_ENABLED defaults to false → spawn returns None
    and never enters the supervised tasks layer."""
    from services import automation_scheduler as mod

    monkeypatch.delenv("AUTOMATION_SCHEDULER_ENABLED", raising=False)
    with patch("core.runtime.tasks.spawn") as spawn_mock:
        result = mod.spawn_scheduler(bot=None)
    assert result is None
    spawn_mock.assert_not_called()


def test_spawn_scheduler_skips_when_env_flag_explicitly_false(monkeypatch):
    from services import automation_scheduler as mod

    monkeypatch.setenv("AUTOMATION_SCHEDULER_ENABLED", "false")
    with patch("core.runtime.tasks.spawn") as spawn_mock:
        result = mod.spawn_scheduler(bot=None)
    assert result is None
    spawn_mock.assert_not_called()


def test_spawn_scheduler_runs_when_env_flag_true(monkeypatch):
    from services import automation_scheduler as mod

    monkeypatch.setenv("AUTOMATION_SCHEDULER_ENABLED", "true")
    fake_task = MagicMock()
    with patch("core.runtime.tasks.spawn", return_value=fake_task) as spawn_mock:
        result = mod.spawn_scheduler(bot=None)
    assert result is fake_task
    spawn_mock.assert_called_once()
    assert spawn_mock.call_args.args[0] == "automation_scheduler"


def test_spawn_scheduler_force_bypasses_env_flag(monkeypatch):
    from services import automation_scheduler as mod

    monkeypatch.delenv("AUTOMATION_SCHEDULER_ENABLED", raising=False)
    fake_task = MagicMock()
    with patch("core.runtime.tasks.spawn", return_value=fake_task) as spawn_mock:
        result = mod.spawn_scheduler(bot=None, force=True)
    assert result is fake_task
    spawn_mock.assert_called_once()
