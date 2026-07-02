"""Trigger scan for the self-improving loop (plan section 5, Lane B1).

The loop's sensory layer: ``check_triggers`` inspects the project tree plus the
state document and reports which of the five trigger kinds fired —

- ``critical_unfilled`` — a graduation-critical slot is still not ``filled``
  after the cadence's grace window (one trigger per slot).
- ``blocking_open``     — escalated blocking questions sit on
  ``state["open_questions"]``.
- ``drift``             — the doc-hygiene checks (badge / link / reachable)
  report findings.
- ``staleness``         — the newest session log is older than
  ``cadence["staleness_days"]`` days, or reconciliation is overdue by session
  count.
- ``new_area``          — a direct subdirectory of the docs root holds only
  unreachable *and* unbadged markdown (nobody owns it yet).

``mandatory_questions`` then maps fired triggers back onto question-bank
entries, and ``trigger_block`` renders the orientation text block. The mode
policy (``engine.lib.modes.triggers_mandate``) decides whether the block is a
mandate or an advisory — this module only renders whichever the caller picked.
Pure stdlib; returns data / text, never prints.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, NamedTuple

from engine.checks.check_docs import badge_token, check_reachable, run_doc_checks
from engine.checks.check_session_log import latest_session_log
from engine.interview.question_bank import QUESTIONS
from engine.lib.config import Config

_TRG_PRIORITY_ORDER = {"blocking": 0, "high": 1, "normal": 2}
_TRG_SECONDS_PER_DAY = 86_400.0


class Trigger(NamedTuple):
    """One fired trigger: kind, severity, human message, related question ids."""

    kind: str
    severity: str
    message: str
    question_ids: tuple[str, ...]


def _trg_critical_unfilled(
    state: dict[str, Any],
    cadence: dict[str, int],
    bank: list[dict],
) -> list[Trigger]:
    """One trigger per critical slot still unfilled past the grace window."""
    grace = int(cadence.get("critical_slot_grace_sessions", 3))
    if int(state.get("session_count", 0)) <= grace:
        return []
    slots = state.get("slots", {})
    critical = dict.fromkeys(q["slot"] for q in bank if q.get("critical"))
    triggers: list[Trigger] = []
    for slot in critical:
        if slots.get(slot) == "filled":
            continue
        ids = tuple(q["id"] for q in bank if q["slot"] == slot)
        message = (
            f"critical slot '{slot}' is not filled after the "
            f"{grace}-session grace window"
        )
        triggers.append(Trigger("critical_unfilled", "blocking", message, ids))
    return triggers


def _trg_blocking_open(state: dict[str, Any]) -> list[Trigger]:
    """One trigger when escalated blocking questions are open."""
    open_questions = [str(q) for q in state.get("open_questions", [])]
    if not open_questions:
        return []
    listed = ", ".join(open_questions)
    message = f"{len(open_questions)} blocking question(s) open: {listed}"
    return [Trigger("blocking_open", "blocking", message, tuple(open_questions))]


def _trg_drift(docs_root: Path, config: Config) -> list[Trigger]:
    """One trigger when the doc-hygiene checks report any finding."""
    findings = run_doc_checks(docs_root, config.badge_tokens, config.readpath_docs)
    if not findings:
        return []
    kinds = ", ".join(sorted({f.kind for f in findings}))
    message = f"doc hygiene reports {len(findings)} finding(s) ({kinds})"
    return [Trigger("drift", "high", message, ())]


def _trg_staleness(
    state: dict[str, Any],
    cadence: dict[str, int],
    sessions_dir: Path,
) -> list[Trigger]:
    """One trigger when memory looks stale (old log or overdue reconciliation)."""
    reasons: list[str] = []
    stale_days = int(cadence.get("staleness_days", 14))
    newest = latest_session_log(sessions_dir)
    if newest is not None:
        age_days = (time.time() - newest.stat().st_mtime) / _TRG_SECONDS_PER_DAY
        if age_days > stale_days:
            reasons.append(
                f"newest session log is {int(age_days)} days old "
                f"(threshold {stale_days})",
            )
    overdue = int(cadence.get("reconciliation_sessions", 20))
    since = int(state.get("session_count", 0)) - int(
        state.get("last_compaction_session", 0),
    )
    if since >= overdue:
        reasons.append(
            f"{since} sessions since the last compaction (cadence {overdue})",
        )
    if not reasons:
        return []
    return [Trigger("staleness", "normal", "; ".join(reasons), ())]


def _trg_new_area(docs_root: Path, config: Config) -> list[Trigger]:
    """One trigger per docs subdirectory whose docs are all orphaned + unbadged."""
    if not docs_root.is_dir():
        return []
    orphans = {f.path for f in check_reachable(docs_root, config.readpath_docs)}
    triggers: list[Trigger] = []
    for sub in sorted(p for p in docs_root.iterdir() if p.is_dir()):
        files = sorted(sub.rglob("*.md"))
        if not files:
            continue
        all_unowned = all(
            f.relative_to(docs_root).as_posix() in orphans and badge_token(f) is None
            for f in files
        )
        if all_unowned:
            message = (
                f"new docs area '{sub.name}/' ({len(files)} file(s)) is "
                "entirely unreachable and unbadged — no ownership entry yet"
            )
            triggers.append(Trigger("new_area", "high", message, ()))
    return triggers


def check_triggers(
    root: Path,
    config: Config,
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[Trigger]:
    """Scan the project tree + state and return every fired trigger.

    ``root`` is the project root; the docs root and sessions dir are resolved
    from ``config``. Returns triggers grouped by kind in the fixed order
    critical_unfilled, blocking_open, drift, staleness, new_area.
    """
    bank = QUESTIONS if bank is None else bank
    cadence = dict(config.cadence or {})
    docs_root = root / config.docs_root
    sessions_dir = root / config.sessions_dir
    return (
        _trg_critical_unfilled(state, cadence, bank)
        + _trg_blocking_open(state)
        + _trg_drift(docs_root, config)
        + _trg_staleness(state, cadence, sessions_dir)
        + _trg_new_area(docs_root, config)
    )


def mandatory_questions(
    triggers: list[Trigger],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return the bank questions the fired triggers pull into this session.

    Selects entries whose ``trigger`` field matches a fired kind, plus the
    entries a ``critical_unfilled`` trigger names via ``question_ids``.
    De-duplicated by id; priority-ordered (blocking, high, normal — stable).
    """
    bank = QUESTIONS if bank is None else bank
    fired_kinds = {t.kind for t in triggers}
    named_ids = {
        qid for t in triggers if t.kind == "critical_unfilled" for qid in t.question_ids
    }
    selected: list[dict] = []
    seen: set[str] = set()
    for question in bank:
        wanted = question.get("trigger") in fired_kinds or question["id"] in named_ids
        if wanted and question["id"] not in seen:
            seen.add(question["id"])
            selected.append(question)
    return sorted(
        selected,
        key=lambda q: _TRG_PRIORITY_ORDER.get(q.get("priority", "normal"), 2),
    )


def trigger_block(
    triggers: list[Trigger],
    questions: list[dict],
    *,
    mandate: bool,
) -> str:
    """Render the orientation trigger block ('' when nothing fired).

    ``mandate=True`` (guided/active modes) opens with a MANDATORY
    question-session header; otherwise the block is an advisory.
    """
    if not triggers:
        return ""
    if mandate:
        header = "## ⚠️ MANDATORY question session — triggers fired"
    else:
        header = "## Trigger advisory (non-mandatory)"
    lines = [header, ""]
    lines += [f"- [{t.severity}] {t.kind}: {t.message}" for t in triggers]
    if questions:
        lines += ["", "Questions to ask this session:"]
        lines += [
            f"- {q['id']} ({q.get('priority', 'normal')}): {q['prompt']}"
            for q in questions
        ]
    return "\n".join(lines) + "\n"
