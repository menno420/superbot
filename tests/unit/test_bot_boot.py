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


def test_bot1_spawns_restart_close_driver() -> None:
    """LP-3: the restart watchdog must be supervised at boot so a
    ``lifecycle.request_restart`` call turns into ``bot.close()``."""
    src = _src()
    assert "restart_close_driver" in src, (
        "bot1.py must spawn a supervised task named "
        "'restart_close_driver' to drive bot.close() on restart (LP-3)."
    )
    assert "_drive_close_on_restart_request" in src, (
        "bot1.py must define and spawn _drive_close_on_restart_request "
        "(LP-3)."
    )


def test_bot1_restart_watchdog_uses_bounded_close_timeout() -> None:
    """LP-3: the watchdog must wrap ``bot.close()`` in
    ``asyncio.wait_for`` with a timeout so a wedged close cannot hold
    the runtime lock past its TTL."""
    src = _src()
    assert "RESTART_CLOSE_TIMEOUT_SECONDS" in src, (
        "bot1.py must declare RESTART_CLOSE_TIMEOUT_SECONDS as the "
        "named bound for the restart close (LP-3)."
    )
    assert re.search(
        r"asyncio\.wait_for\(\s*bot\.close\(\)\s*,",
        src,
    ), (
        "bot1.py must wrap bot.close() in asyncio.wait_for with a "
        "bounded timeout (LP-3)."
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
