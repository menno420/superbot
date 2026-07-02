"""Maintenance actuators for the self-improving loop (plan section 5, Lane B3).

The loop's housekeeping arm: the compaction cadence and its pre-compaction
"State Delta" snapshot, the escalated open-question list (the blocking-question
brake graduation waits on), the promotion-rights downgrade, and the composed
``maintain`` human report. Pure stdlib; every file write goes through
``atomic_write_text``; functions return data / text, never print — the CLI
owns all output.

The sibling loop modules (``reflections``, ``kpis``, ``review_seam``) are
imported lazily with fail-open fallbacks, so this module keeps working when a
build ships without them (the single-file bootstrap concatenation case).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config
from engine.loop.kpis import kpi_footer
from engine.loop.reflections import (
    REFLECTIONS_FILENAME,
    active_lessons,
    load_reflections,
)

_MNT_VALUE_WIDTH = 80


def compaction_due(state: dict[str, Any], cadence: dict[str, int]) -> bool:
    """True when the compaction cadence window has elapsed.

    Fires when ``session_count - last_compaction_session`` reaches
    ``cadence["compaction_sessions"]`` (default 20).
    """
    every = int(cadence.get("compaction_sessions", 20))
    since = int(state.get("session_count", 0)) - int(
        state.get("last_compaction_session", 0),
    )
    return since >= every


def _mnt_cell(value: Any) -> str:
    """Collapse ``value`` to one table-safe line truncated to 80 chars."""
    text = " ".join(str(value).split()).replace("|", "/")
    return text[:_MNT_VALUE_WIDTH]


def _mnt_lesson_lines(reflections: list[dict]) -> list[str]:
    """Render the active-lesson lines from the reflection entries."""
    live = active_lessons(reflections, len(reflections))
    return [f"- [{e.get('id', '?')}] {e.get('lesson', '')}" for e in live]


def _mnt_slot_lines(state: dict[str, Any]) -> list[str]:
    """Render the slot table (name-sorted; values truncated to 80 chars)."""
    slots = state.get("slots", {})
    if not slots:
        return []
    values = state.get("slot_values", {})
    lines = ["| slot | status | value |", "| --- | --- | --- |"]
    for slot in sorted(slots):
        entry = values.get(slot, {})
        value = entry.get("value", "") if isinstance(entry, dict) else entry
        lines.append(f"| {slot} | {slots[slot]} | {_mnt_cell(value)} |")
    return lines


def state_delta(state: dict[str, Any], reflections: list[dict]) -> str:
    """Render the pre-compaction State Delta markdown — dense, deterministic.

    The counters line always appears; the slot table, open-questions list, and
    active-lessons list appear only when non-empty. No timestamps: two calls
    over the same inputs return identical text.
    """
    lines = [
        f"# State Delta — session {int(state.get('session_count', 0))}",
        "",
        f"- mode: {state.get('mode', '?')} · stage: {state.get('stage', '?')} · "
        f"sessions: {int(state.get('session_count', 0))} · "
        f"quiet: {int(state.get('quiet_sessions', 0))}",
    ]
    slot_lines = _mnt_slot_lines(state)
    if slot_lines:
        lines += ["", "## Slots", "", *slot_lines]
    open_questions = [str(q) for q in state.get("open_questions", [])]
    if open_questions:
        lines += ["", "## Open questions", ""]
        lines += [f"- {qid}" for qid in open_questions]
    lesson_lines = _mnt_lesson_lines(reflections)
    if lesson_lines:
        lines += ["", "## Active lessons", "", *lesson_lines]
    return "\n".join(lines) + "\n"


def _mnt_load_reflections(state_dir: Path) -> list[dict]:
    """Load the reflection buffer for the delta (``[]`` when unavailable)."""
    return load_reflections(state_dir / REFLECTIONS_FILENAME)


def run_compaction(root: Path, config: Config, backend: Any) -> Path:
    """Write the State Delta snapshot and reset the compaction counter.

    Writes ``<state_dir>/state-delta-<session_count>.md`` atomically, then
    stamps ``last_compaction_session`` so ``compaction_due`` stays quiet until
    the next cadence window. Returns the written path.
    """
    state_dir = root / config.state_dir
    session = int(backend.get("session_count", 0))
    delta = state_delta(backend.data, _mnt_load_reflections(state_dir))
    path = state_dir / f"state-delta-{session}.md"
    atomic_write_text(path, delta)
    backend.set("last_compaction_session", session)
    return path


def escalate_blocking(backend: Any, question_id: str) -> bool:
    """Append ``question_id`` to the escalated open-questions list once.

    Idempotent: True when it appended, False when the id was already open.
    Open questions hold graduation until answered (the blocking brake).
    """
    open_questions = list(backend.get("open_questions", []))
    if question_id in open_questions:
        return False
    open_questions.append(question_id)
    backend.set("open_questions", open_questions)
    return True


def resolve_open_question(backend: Any, question_id: str) -> bool:
    """Drop ``question_id`` from the open-questions list; False when absent."""
    open_questions = list(backend.get("open_questions", []))
    if question_id not in open_questions:
        return False
    open_questions.remove(question_id)
    backend.set("open_questions", open_questions)
    return True


def downgrade_promotion(backend: Any, *, reason: str) -> None:
    """Cap autonomy: ``promotion_rights`` → ``"propose"``, logged with why.

    Appends a ``promotion_downgrade`` event to ``review_log`` so the loss of
    apply-rights always carries its provenance.
    """
    log = list(backend.get("review_log", []))
    log.append(
        {
            "event": "promotion_downgrade",
            "reason": reason,
            "date": date.today().isoformat(),
        },
    )
    with backend.transaction():
        backend.set("promotion_rights", "propose")
        backend.set("review_log", log)


def _mnt_item_line(item: Any) -> str:
    """Render one report line for a trigger or a checker finding.

    Triggers (kind/severity/message) render like the orientation block;
    findings (path/kind/message) render path-first; anything else renders as
    its ``str``.
    """
    kind = getattr(item, "kind", None)
    message = getattr(item, "message", None)
    if kind is None or message is None:
        return f"- {item}"
    severity = getattr(item, "severity", None)
    if severity is not None:
        return f"- [{severity}] {kind}: {message}"
    path = getattr(item, "path", None)
    prefix = f"{path}: " if path else ""
    return f"- {prefix}[{kind}] {message}"


def _mnt_review_dir() -> str:
    """Return the review-payload directory name.

    Mirrors ``review_seam.REVIEW_DIR`` as a literal: ``review_seam`` imports
    this module at top level, so importing it back would be circular — the
    seam's own test pins the two values equal.
    """
    return "review"


def _mnt_advisories(root: Path, config: Config, backend: Any) -> list[str]:
    """Return the maintenance advisories: compaction due, payloads waiting."""
    advisories: list[str] = []
    if compaction_due(backend.data, dict(config.cadence or {})):
        advisories.append("compaction due — write the State Delta snapshot")
    review_dir = root / config.state_dir / _mnt_review_dir()
    if review_dir.is_dir():
        pending = sorted(review_dir.glob("payload-*.json"))
        if pending:
            advisories.append(
                f"{len(pending)} review payload(s) awaiting a reviewer",
            )
    return advisories


def _mnt_footer(kpis: dict[str, Any]) -> str:
    """Render the KPI footer line for the report."""
    return kpi_footer(kpis)


def maintenance_report(
    root: Path,
    config: Config,
    backend: Any,
    *,
    triggers: list[Any],
    economy_findings: list[Any],
    ledger_findings: list[Any],
    kpis: dict[str, Any],
) -> str:
    """Compose the ``maintain`` human report from the loop's sensor outputs.

    Every section is skipped when its input is empty; a maintenance-advisories
    section surfaces compaction cadence and accumulated review payloads (the
    no-reviewer graceful fallback); the report ends with the KPI footer when
    ``kpis`` is non-empty.
    """
    lines = [
        f"# Maintenance report — session {int(backend.get('session_count', 0))}",
    ]
    sections: tuple[tuple[str, list[Any]], ...] = (
        ("Triggers", triggers),
        ("Economy findings", economy_findings),
        ("Ledger findings", ledger_findings),
    )
    for title, items in sections:
        if not items:
            continue
        lines += ["", f"## {title}", ""]
        lines += [_mnt_item_line(item) for item in items]
    advisories = _mnt_advisories(root, config, backend)
    if advisories:
        lines += ["", "## Maintenance", ""]
        lines += [f"- {advisory}" for advisory in advisories]
    if kpis:
        lines += ["", _mnt_footer(kpis)]
    return "\n".join(lines) + "\n"
