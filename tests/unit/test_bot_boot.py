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
    """PR-02b: shutdown drain calls ``tasks.cancel_all()`` and awaits
    ``tasks.active()`` instead of iterating ``_APP_TASKS``.  The 5 s
    drain budget is preserved."""
    src = _src()
    # Heartbeat stop must precede the cancellation request.
    assert "_heartbeat_stop.set()" in src
    assert re.search(r"_runtime_tasks\.cancel_all\(\s*\)", src), (
        "bot1.py shutdown must call core.runtime.tasks.cancel_all()."
    )
    assert re.search(r"_runtime_tasks\.active\(\s*\)", src), (
        "bot1.py shutdown must snapshot core.runtime.tasks.active() "
        "to await the in-flight tasks."
    )
    assert "timeout=5.0" in src, (
        "bot1.py shutdown must preserve the 5 s drain budget."
    )
