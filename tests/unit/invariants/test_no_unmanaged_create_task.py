"""PR-02a/b invariant: no unmanaged ``asyncio.create_task`` outside an allowlist.

Every entry-point/cog/service background task must go through
``core.runtime.tasks.spawn`` so the canonical supervisor can hold a
strong reference, log exceptions, increment the
``task_outcome_total{name,outcome}`` Prometheus counter, and (for
app-level callers) invoke an ``on_error`` hook.

Bare ``asyncio.create_task`` is allowed only at two locations:

1. ``disbot/core/runtime/tasks.py`` — the legitimate definition site
   inside ``spawn()`` itself.
2. ``disbot/bot1.py`` — the one-shot coordination primitive used
   inside ``asyncio.wait({...}, timeout=5.0)`` to race the
   health-server bind-ready event against a supervised task.  This is
   not a long-lived background task; it's a transient join helper.

PR-02b migrated ``session_gc.start()`` to ``tasks.spawn``; the
allowlist entry for ``core/runtime/session_gc.py`` has been removed.

Any new occurrence of ``asyncio.create_task`` outside the allowlist
fails CI; add the callsite to the allowlist (with rationale) or
migrate it to ``tasks.spawn``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Allowlist: (relative_path, expected_callsite_count).  Each entry must
# include the count so accidentally adding a SECOND bare create_task to
# an allowlisted file still fails the invariant.
_ALLOWED_CREATE_TASK_SITES: dict[str, int] = {
    # Legitimate definition inside spawn().
    "core/runtime/tasks.py": 1,
    # One-shot coordination primitive racing health-bind vs supervised
    # task inside asyncio.wait.  Not a background root.
    "bot1.py": 1,
}


def _iter_disbot_py_files() -> list[Path]:
    return [
        p
        for p in _DISBOT.rglob("*.py")
        if "__pycache__" not in p.parts and "tests" not in p.parts
    ]


def _count_create_task_calls(path: Path) -> int:
    """Return the number of ``asyncio.create_task(...)`` callsites."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        pytest.fail(f"Could not parse {path}: SyntaxError")
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # asyncio.create_task(...)
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "create_task"
            and isinstance(func.value, ast.Name)
            and func.value.id == "asyncio"
        ):
            count += 1
    return count


def test_no_unmanaged_create_task_outside_allowlist():
    """Every bare ``asyncio.create_task`` callsite is allowlisted."""
    violations: list[str] = []
    for path in _iter_disbot_py_files():
        rel = str(path.relative_to(_DISBOT))
        count = _count_create_task_calls(path)
        if count == 0:
            continue
        expected = _ALLOWED_CREATE_TASK_SITES.get(rel)
        if expected is None:
            violations.append(
                f"{rel}: {count} bare asyncio.create_task call(s); "
                f"migrate to core.runtime.tasks.spawn",
            )
            continue
        if count != expected:
            violations.append(
                f"{rel}: {count} bare asyncio.create_task call(s); "
                f"allowlist expects {expected}.  Add new callsite to "
                f"_ALLOWED_CREATE_TASK_SITES with rationale or migrate "
                f"to core.runtime.tasks.spawn.",
            )
    assert not violations, (
        "Unmanaged asyncio.create_task callsite(s):\n  " + "\n  ".join(violations)
    )


def test_allowlist_entries_still_exist():
    """An allowlist entry whose path was deleted (or whose count went
    to zero) indicates the underlying callsite was migrated; remove
    the allowlist entry rather than leaving dead config."""
    stale: list[str] = []
    for rel, _expected in _ALLOWED_CREATE_TASK_SITES.items():
        path = _DISBOT / rel
        if not path.is_file():
            stale.append(f"{rel}: file no longer exists")
            continue
        if _count_create_task_calls(path) == 0:
            stale.append(f"{rel}: file has zero create_task callsites")
    assert not stale, (
        "Allowlist has stale entries (remove from "
        "_ALLOWED_CREATE_TASK_SITES):\n  " + "\n  ".join(stale)
    )
