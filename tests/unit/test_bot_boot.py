"""Static invariants on ``disbot/bot1.py`` startup wiring.

Verifies that the entry-point module wires every supervised task we
expect at boot. These are intentionally grep-style assertions: the
runtime path runs inside ``async def main()`` and touching it from
unit tests would require building the full bot lifecycle.

Each invariant has a short rationale tied to the reconciliation plan.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BOT1 = _REPO_ROOT / "disbot" / "bot1.py"


def _src() -> str:
    return _BOT1.read_text()


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


def test_bot1_appends_scheduler_task_to_app_tasks() -> None:
    """The spawned task must be cancelled on shutdown via _APP_TASKS."""
    src = _src()
    # Look for the conditional append — the scheduler returns None
    # when the env flag is off, so the append is guarded.
    assert "scheduler_task = spawn_scheduler(bot)" in src
    assert (
        re.search(
            r"if\s+scheduler_task\s+is\s+not\s+None\s*:\s*\n\s*_APP_TASKS\.append\(\s*scheduler_task\s*\)",
            src,
        )
        is not None
    ), (
        "bot1.py must append the spawn_scheduler() task to _APP_TASKS "
        "when it is not None so shutdown can cancel it cleanly."
    )
