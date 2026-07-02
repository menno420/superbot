"""Stop-hook session-close advisor (plan section 5.B, Lane B7).

Runs when a Claude Code session stops: the CLI's ``hook stopcheck`` entry
point prints the advisory lines ``evaluate_stop`` returns, reminding the agent
what the session ritual still owes —

- the session log is missing, or exists but lacks required markers
  (``latest_session_log`` + ``check_log`` with ``config.session_markers``);
- escalated blocking questions are still open (``state["open_questions"]``);
- the compaction cadence window has elapsed (``compaction_due``);
- the reflection buffer has not been mined today
  (``reflection_buffer.last_mined`` vs today's ISO date).

Returns ``[]`` when all clean. Advisory only, and it **fails open**: every
check runs inside its own guard, so a bad state document or an unreadable log
drops that one advisory rather than crashing the stop hook.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from engine.checks.check_session_log import check_log, latest_session_log
from engine.lib.config import Config
from engine.loop.maintenance import compaction_due

_STOP_UNMINED_MSG = "reflections unmined this session — run bootstrap reflect --mine"


def _stop_safe(check: Any) -> list[str]:
    """Run one advisory check, returning [] on any failure (fail open).

    Each check is guarded on its own so one bad input never suppresses the
    other advisories — the stop hook is advisory by contract.
    """
    try:
        return list(check())
    except Exception:  # fail open — one bad check drops only itself
        return []


def _stop_state(backend: Any) -> dict[str, Any]:
    """Return the state document ({} when the backend is unusable — fail open)."""
    try:
        return dict(backend.data)
    except Exception:  # fail open — a broken backend yields no state advisories
        return {}


def _stop_log(root: Path, config: Config) -> list[str]:
    """Advise when the session log is missing or lacks required markers."""
    log = latest_session_log(root / config.sessions_dir)
    if log is None:
        return [
            f"no session log found under {config.sessions_dir}/ — "
            "write one before ending the session",
        ]
    missing = check_log(log, config.session_markers)
    if missing:
        return [f"session log {log.name} is missing: {', '.join(missing)}"]
    return []


def _stop_questions(state: dict[str, Any]) -> list[str]:
    """Advise when escalated blocking questions are still open."""
    open_questions = [str(q) for q in state.get("open_questions", [])]
    if not open_questions:
        return []
    listed = ", ".join(open_questions)
    return [f"{len(open_questions)} blocking question(s) open: {listed}"]


def _stop_compaction(state: dict[str, Any], config: Config) -> list[str]:
    """Advise when the compaction cadence window has elapsed."""
    if compaction_due(state, dict(config.cadence or {})):
        return ["compaction due — write the State Delta snapshot (bootstrap maintain)"]
    return []


def _stop_reflections(state: dict[str, Any]) -> list[str]:
    """Advise when the reflection buffer has not been mined today."""
    buffer = state.get("reflection_buffer")
    last_mined = buffer.get("last_mined") if isinstance(buffer, dict) else None
    if last_mined == date.today().isoformat():
        return []
    return [_STOP_UNMINED_MSG]


def evaluate_stop(root: Path, config: Config, backend: Any) -> list[str]:
    """Return the session-close advisory lines ([] when all clean).

    Four checks in fixed order: session log, open blocking questions,
    compaction cadence, reflection mining. Each runs inside its own guard so
    one failing check never suppresses the others — the stop hook is advisory
    and fails open by contract.
    """
    state = _stop_state(backend)
    checks = (
        lambda: _stop_log(root, config),
        lambda: _stop_questions(state),
        lambda: _stop_compaction(state, config),
        lambda: _stop_reflections(state),
    )
    advisories: list[str] = []
    for check in checks:
        advisories.extend(_stop_safe(check))
    return advisories
