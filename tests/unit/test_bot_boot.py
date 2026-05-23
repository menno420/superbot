"""Static invariants on ``disbot/bot1.py`` startup wiring.

Verifies that the entry-point module wires every supervised task we
expect at boot. These are intentionally grep-style assertions: the
runtime path runs inside ``async def main()`` and touching it from
unit tests would require building the full bot lifecycle.

Each invariant has a short rationale tied to the reconciliation plan.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BOT1 = _REPO_ROOT / "disbot" / "bot1.py"


def _src() -> str:
    return _BOT1.read_text()


def _has_call(tree: ast.AST, *, attr: str, named_arg: str | None = None) -> bool:
    """True if ``tree`` contains a Call whose attribute name matches.

    When ``named_arg`` is given, the call must reference an argument with
    that name (e.g. ``_APP_TASKS.append(scheduler_task)`` matches
    ``attr="append"`` + ``named_arg="scheduler_task"``).
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != attr:
            continue
        if named_arg is None:
            return True
        for arg in node.args:
            if isinstance(arg, ast.Name) and arg.id == named_arg:
                return True
    return False


def test_bot1_imports_and_calls_spawn_scheduler() -> None:
    """PR-F: the automation scheduler must actually be spawned at boot.

    ``spawn_scheduler`` is defined in
    ``services/automation_scheduler.py`` but for production it must be
    invoked from the entry-point module. The reconciliation plan §6
    PR-F documents this as the call site.
    """
    src = _src()
    assert "from services.automation_scheduler import spawn_scheduler" in src, (
        "bot1.py must import spawn_scheduler so the automation scheduler "
        "can be spawned at boot (PR-F)."
    )
    # Must call it with ``bot`` so the cog can reach the running loop.
    assert re.search(r"spawn_scheduler\s*\(\s*bot\s*\)", src), (
        "bot1.py must call spawn_scheduler(bot) at startup (PR-F)."
    )


def test_bot1_does_not_double_supervise_scheduler_task() -> None:
    """PR-02b: ``spawn_scheduler`` already routes through
    ``core.runtime.tasks.spawn`` internally, so the entry-point module
    must NOT also append the returned task to ``_APP_TASKS``.  Double
    supervision was the original wiring; PR-02b removes it so
    ``tasks.cancel_all`` is the single owner of the scheduler's
    cancellation."""
    src = _src()
    assert "spawn_scheduler(bot)" in src
    # AST-level check (so comments mentioning the historical pattern
    # don't false-positive).
    tree = ast.parse(src)
    assert not _has_call(tree, attr="append", named_arg="scheduler_task"), (
        "bot1.py must NOT append spawn_scheduler() result to _APP_TASKS — "
        "the scheduler is already supervised by core.runtime.tasks.spawn."
    )


def test_bot1_shutdown_drains_via_core_runtime_tasks() -> None:
    """PR-02b (revised): shutdown drain calls ``tasks.cancel_all()``
    and awaits the **returned snapshot** — not a re-snapshot via
    ``active()``.  The 5 s drain budget is preserved and timeout is
    observable via a WARNING log."""
    src = _src()
    # Heartbeat stop must precede the cancellation request.
    assert "_heartbeat_stop.set()" in src
    # Drain captures the cancellation snapshot.
    assert re.search(r"cancelled\s*=\s*_runtime_tasks\.cancel_all\(\s*\)", src), (
        "bot1.py shutdown must assign the cancel_all() return value to "
        "the drain snapshot so done-callbacks cannot race the await."
    )
    # The await must be on the captured snapshot, not on active().
    assert re.search(r"asyncio\.wait\(\s*cancelled\s*,\s*timeout=5\.0\s*\)", src), (
        "bot1.py shutdown must await asyncio.wait(cancelled, timeout=5.0) "
        "on the snapshot returned by cancel_all()."
    )
    # Active() must NOT be called in the shutdown finally-block — the
    # re-snapshot pattern is the bug we just fixed.
    finally_block = src.split("finally:", 1)[-1]
    assert "_runtime_tasks.active(" not in finally_block, (
        "Shutdown finally-block must not re-snapshot via active() — "
        "use the snapshot returned by cancel_all() instead."
    )
    # Drain must run on every exit, not just SIGTERM.  The legacy
    # ``if _shutting_down:`` guard around the drain was a real bug:
    # normal exits would cancel without awaiting.
    assert not re.search(
        r"if\s+_shutting_down\s*:\s*\n\s+(?:pending|cancelled|_,)\s*=",
        src,
    ), (
        "Shutdown drain must run on every exit, not gated on _shutting_down."
    )


def test_bot1_applies_config_log_level_at_boot() -> None:
    """LP-0: bot1.py applies ``config.LOG_LEVEL`` to the root logger at
    boot so the env var matches the runtime behaviour of the
    ``!loglevel`` operator command at ``cogs/admin_cog.py:329-334``.
    Invalid values fall back to ``logging.INFO`` so a typo in the env
    var never blocks startup.
    """
    src = _src()
    assert re.search(r"getattr\(\s*logging\s*,\s*config\.LOG_LEVEL\s*,", src), (
        "bot1.py must resolve config.LOG_LEVEL via getattr(logging, ...) "
        "so the LOG_LEVEL env var takes effect at boot (LP-0)."
    )
    assert not re.search(r"_root\.setLevel\(\s*logging\.INFO\s*\)", src), (
        "bot1.py must not hardcode root setLevel to logging.INFO — "
        "the LOG_LEVEL env var must be honoured (LP-0)."
    )


def test_bot1_sigterm_handler_routes_through_lifecycle() -> None:
    """LP-2: SIGTERM must enter the lifecycle service rather than
    flipping a module-local ``_shutting_down: bool``. The legacy global
    is gone; observers (``_channel_guard``, future PRs) read from
    ``lifecycle.can_accept_commands()``.
    """
    src = _src()
    assert "_lifecycle.request_shutdown(reason=" in src, (
        "bot1._begin_shutdown must call lifecycle.request_shutdown(...) "
        "so SIGTERM is observable through the lifecycle event buffer (LP-2)."
    )
    assert "_shutting_down = True" not in src, (
        "Legacy ``_shutting_down = True`` assignment must be gone — "
        "the lifecycle service is now the single source of truth (LP-2)."
    )


def test_bot1_channel_guard_admits_via_lifecycle() -> None:
    """LP-2: ``_channel_guard`` must consult
    :func:`core.runtime.lifecycle.can_accept_commands` rather than the
    legacy ``_shutting_down`` bool.
    """
    src = _src()
    assert "_lifecycle.can_accept_commands()" in src, (
        "bot1._channel_guard must check lifecycle.can_accept_commands() "
        "so command admission tracks the lifecycle phase (LP-2)."
    )


def test_bot1_posts_startup_summary_webhook_before_bot_start() -> None:
    """LP-7: the deterministic startup-summary webhook must be posted
    AFTER all startup_outcome.record_* calls and BEFORE
    ``bot.start(...)``, so operators see boot health immediately rather
    than after the Discord handshake."""
    src = _src()
    assert "reporter.on_startup_summary(" in src, (
        "bot1.py must call reporter.on_startup_summary(...) before "
        "bot.start() so the deterministic boot health surfaces "
        "without waiting for on_ready (LP-7)."
    )
    # Order: the on_startup_summary call must appear before bot.start.
    summary_idx = src.find("reporter.on_startup_summary(")
    bot_start_idx = src.find("await bot.start(config.DISCORD_BOT_TOKEN)")
    assert summary_idx != -1 and bot_start_idx != -1
    assert summary_idx < bot_start_idx, (
        "on_startup_summary must be posted BEFORE bot.start() — "
        "otherwise it races with on_ready and loses the 'deterministic, "
        "early' property that's the whole point of LP-7."
    )


def test_bot1_spawns_lifecycle_close_driver() -> None:
    """The lifecycle close-driver must be supervised at boot so any
    pending lifecycle request (SIGTERM shutdown or ``!restart``) turns
    into ``bot.close()``."""
    src = _src()
    assert "lifecycle_close_driver" in src, (
        "bot1.py must spawn a supervised task named "
        "'lifecycle_close_driver' to drive bot.close() on any pending "
        "lifecycle request."
    )
    assert "_drive_close_on_lifecycle_request" in src, (
        "bot1.py must define and spawn _drive_close_on_lifecycle_request."
    )


def test_bot1_close_driver_uses_bounded_timeout() -> None:
    """The close-driver must wrap ``bot.close()`` in
    ``asyncio.wait_for`` with a timeout so a wedged close cannot hold
    the runtime lock past its TTL."""
    src = _src()
    assert "LIFECYCLE_CLOSE_TIMEOUT_SECONDS" in src, (
        "bot1.py must declare LIFECYCLE_CLOSE_TIMEOUT_SECONDS as the "
        "named bound for the close."
    )
    assert re.search(
        r"asyncio\.wait_for\(\s*bot\.close\(\)\s*,",
        src,
    ), (
        "bot1.py must wrap bot.close() in asyncio.wait_for with a "
        "bounded timeout."
    )


def test_bot1_close_driver_gates_on_pending_and_draining() -> None:
    """The close-driver eligibility must consult both the lifecycle
    pending request and the DRAINING phase — that pair is what makes
    one watchdog cover both shutdown and restart."""
    src = _src()
    assert "_lifecycle.get_pending()" in src, (
        "bot1.py close-driver must consult _lifecycle.get_pending() — "
        "not restart_requested() — so shutdown intent is also closed."
    )
    assert "_lifecycle.Phase.DRAINING" in src, (
        "bot1.py close-driver must gate on _lifecycle.Phase.DRAINING."
    )


def test_bot1_close_driver_does_not_own_cleanup() -> None:
    """Architectural boundary: cleanup belongs to ``main()``'s finally
    block, not the close-driver.  The driver function body must not
    call runtime-lock release, db.close, reporter.close, os.execv, or
    sys.exit.  ``os._exit`` is permitted (close-timeout fail-safe).

    AST-scoped to the driver function so that legitimate uses of those
    same calls elsewhere in bot1.py (the actual finalizer) are not
    flagged.
    """
    tree = ast.parse(_src())
    driver_fn: ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_drive_close_on_lifecycle_request"
        ):
            driver_fn = node
            break
    assert driver_fn is not None, (
        "bot1.py must define async def _drive_close_on_lifecycle_request."
    )

    forbidden_attr_calls = {
        "release_lock_best_effort",
        "execv",
    }
    forbidden_attr_chains = {
        ("db", "close"),
        ("reporter", "close"),
        ("sys", "exit"),
    }
    for node in ast.walk(driver_fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr in forbidden_attr_calls:
                raise AssertionError(
                    f"close-driver must not call {func.attr!r}; "
                    f"cleanup is owned by main()'s finally block.",
                )
            if isinstance(func.value, ast.Name):
                pair = (func.value.id, func.attr)
                if pair in forbidden_attr_chains:
                    raise AssertionError(
                        f"close-driver must not call "
                        f"{pair[0]}.{pair[1]}; cleanup is owned by "
                        f"main()'s finally block.",
                    )


def test_bot1_no_legacy_restart_close_driver_names() -> None:
    """Guard against regressing the restart-only close-driver split.

    The previous design coupled close execution to restart intent;
    SIGTERM shutdowns therefore never reached bot.close().  Re-adding
    any of these names would reintroduce that split.
    """
    src = _src()
    for legacy in (
        "_drive_close_on_restart_request",
        "restart_close_driver",
        "RESTART_CLOSE_TIMEOUT_SECONDS",
        "_RESTART_CLOSE_POLL_INTERVAL",
    ):
        assert legacy not in src, (
            f"Legacy restart-only close-driver name {legacy!r} "
            f"reintroduced — see plan; the close-driver must remain "
            f"keyed on lifecycle pending + DRAINING phase."
        )


def test_bot1_finally_block_transitions_to_restarting_when_restart_pending() -> (
    None
):
    """LP-3: the finally block surfaces RESTARTING as the terminal
    phase when a restart was requested, so the recent-event buffer
    distinguishes restart-exit from shutdown-exit."""
    src = _src()
    finally_block = src.split("finally:", 1)[-1]
    assert "Phase.RESTARTING" in finally_block, (
        "bot1.py finally block must promote the terminal phase to "
        "RESTARTING when lifecycle.restart_requested() is true (LP-3)."
    )
    assert "restart_requested()" in finally_block, (
        "bot1.py finally block must consult "
        "lifecycle.restart_requested() to choose between STOPPED and "
        "RESTARTING (LP-3)."
    )


def test_bot1_finally_block_posts_close_completed_webhook_before_reporter_close() -> (
    None
):
    """Companion to the close-beginning webhook posted by the close-driver:
    the finalizer must post on_lifecycle_close_completed BEFORE
    reporter.close() tears down the HTTP session, otherwise the embed
    cannot reach the operator channel.  The two operator-visible signals
    bracket the shutdown / restart window so the gap between them is the
    close + cleanup duration."""
    src = _src()
    finally_block = src.split("finally:", 1)[-1]
    assert "on_lifecycle_close_completed" in finally_block, (
        "bot1.py finally block must invoke "
        "reporter.on_lifecycle_close_completed so the close-complete "
        "embed reaches the operator channel before reporter teardown."
    )
    # Ordering: the close-completed call must appear before
    # ``reporter.close()`` so the HTTP session is still alive.
    webhook_idx = finally_block.index("on_lifecycle_close_completed")
    reporter_close_idx = finally_block.index("reporter.close()")
    assert webhook_idx < reporter_close_idx, (
        "on_lifecycle_close_completed must be posted BEFORE "
        "reporter.close() — otherwise the webhook is dispatched on a "
        "torn-down aiohttp session and silently dropped."
    )


def test_bot1_shutdown_drain_logs_timeout() -> None:
    """PR-02b (revised): when the 5 s drain budget elapses with tasks
    still pending, a WARNING log must surface so operators see the
    timeout rather than discovering it only via event-loop close-time
    noise."""
    src = _src()
    finally_block = src.split("finally:", 1)[-1]
    assert "still_pending" in finally_block, (
        "Shutdown drain must capture still_pending tasks after timeout."
    )
    assert re.search(r"logger\.warning\([^)]*Shutdown drain", finally_block, re.DOTALL), (
        "Shutdown drain timeout must emit a WARNING log line so "
        "operators can detect the slow drain."
    )
