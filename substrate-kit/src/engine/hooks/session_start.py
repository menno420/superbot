"""SessionStart orientation composer (plan section 5.B, Lane B7).

The nervous system's *injection* point: when Claude Code starts a session, the
``bootstrap hook sessionstart`` entry point prints the text this module
composes, so the agent boots already knowing the project's mode, stance,
learned lessons, fired triggers, and pending questions. The composition is
**mode-aware** — ``orientation_depth`` (observe → minimal, guided → standard,
active → full) decides which sections render and how hard they cap.

Section order (the plan's fixed sequence): status header → stance briefing →
user-style block → learned lessons (AFTER user-style) → trigger block →
guided-practices line → economy-gauges advisory (over-cap only) → pending
questions (quota view) → observe-mode workflow proposal.

Every section is defensive: a failure inside one section drops that section,
never the whole composition — orientation must never crash a session. This is
the one place broad ``except Exception`` is correct by design (fail open, like
the stance guard).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.economy.engine import economy_gauges
from engine.interview.interview import pending_questions, session_questions
from engine.lib.config import Config
from engine.lib.modes import (
    active_practices,
    orientation_depth,
    triggers_mandate,
    workflow_proposal_due,
)
from engine.loop.reflections import (
    REFLECTIONS_FILENAME,
    active_lessons,
    lessons_block,
    load_reflections,
)
from engine.loop.triggers import check_triggers, mandatory_questions, trigger_block
from engine.stances.stances import stance_briefing

# Depth "standard" caps the learned-lessons section at this many entries.
_ORI_STANDARD_LESSON_CAP = 3
# Depth "minimal" (observe) renders only these section numbers: the status
# header (1), the trigger block as an advisory (5), and the workflow proposal
# (9) — observe imposes nothing else.
_ORI_MINIMAL_SECTIONS = frozenset({1, 5, 9})


def _ori_status_header(state: dict[str, Any], config: Config) -> str:
    """Render section 1 — the compact status header line block."""
    project = str(state.get("project_id") or config.project_id)
    return (
        f"# Session orientation — {project}\n"
        f"mode: {state.get('mode', '?')} · stage: {state.get('stage', '?')} · "
        f"stance: {state.get('stance', '?')} · "
        f"session: {int(state.get('session_count', 0))}"
    )


def _ori_stance(state: dict[str, Any]) -> str:
    """Render section 2 — the active stance briefing ('' when no stance set)."""
    stance = state.get("stance")
    if not stance:
        return ""
    return stance_briefing(str(stance))


def _ori_user_style(state: dict[str, Any]) -> str:
    """Render section 3 — the owner_profile user-style block ('' when unfilled)."""
    entry = state.get("slot_values", {}).get("owner_profile")
    value = entry.get("value") if isinstance(entry, dict) else entry
    text = str(value).strip() if value else ""
    if not text:
        return ""
    return f"## How the owner works:\n\n> {text}"


def _ori_lessons(root: Path, config: Config, depth: str) -> str:
    """Render section 4 — learned lessons (standard caps at 3, full uncapped)."""
    entries = load_reflections(root / config.state_dir / REFLECTIONS_FILENAME)
    cap = _ORI_STANDARD_LESSON_CAP if depth == "standard" else len(entries)
    return lessons_block(active_lessons(entries, cap))


def _ori_triggers(root: Path, config: Config, state: dict[str, Any]) -> str:
    """Render section 5 — the trigger block (mandate flag per the mode policy)."""
    triggers = check_triggers(root, config, state)
    questions = mandatory_questions(triggers)
    return trigger_block(triggers, questions, mandate=triggers_mandate(state))


def _ori_practices(state: dict[str, Any], config: Config) -> str:
    """Render section 6 — the one-line guided-practices block ('' when empty)."""
    practices = active_practices(state, dict(config.cadence or {}))
    if not practices:
        return ""
    return "Active practices: " + ", ".join(practices)


def _ori_gauges(root: Path, config: Config) -> str:
    """Render section 7 — economy advisory listing ONLY over-cap gauges."""
    over = [g for g in economy_gauges(root, config) if g.get("over")]
    if not over:
        return ""
    lines = ["## Economy advisory — over-cap gauges", ""]
    lines += [
        f"- {g['name']} ({g['kind']}): {g['value']} words/items over cap {g['cap']}"
        for g in over
    ]
    return "\n".join(lines)


def _ori_questions(state: dict[str, Any]) -> str:
    """Render section 8 — the quota-capped ask list with a '+N more' suffix."""
    asks = session_questions(state)
    if not asks:
        return ""
    lines = ["## Questions this session", ""]
    lines += [
        f"- {q['id']} ({q.get('priority', 'normal')}): {q['prompt']}" for q in asks
    ]
    extra = len(pending_questions(state)) - len(asks)
    if extra > 0:
        lines += ["", f"(+{extra} more later)"]
    return "\n".join(lines)


def _ori_proposal(state: dict[str, Any]) -> str:
    """Render section 9 — observe mode's workflow proposal when it is due."""
    if state.get("mode") != "observe" or not workflow_proposal_due(state):
        return ""
    return (
        "## Proposed workflow\n\n"
        "Observe mode has watched enough sessions to propose a tailored "
        "workflow. If the pacing looks right, switch mode to adopt it: "
        "`bootstrap mode guided` (one practice at a time) or "
        "`bootstrap mode active` (the full workflow now). Observe imposes "
        "nothing until you do."
    )


def _ori_safe(build: Any) -> str:
    """Run one section builder, returning '' on any failure (fail open).

    The one place broad ``except Exception`` is correct by design: a bad state
    document or an unreadable file drops that single section — orientation
    must never crash a session.
    """
    try:
        return str(build()).strip()
    except Exception:  # fail open — one bad section never breaks the whole
        return ""


def compose_orientation(root: Path, config: Config, backend: Any) -> str:
    """Compose the mode-aware SessionStart orientation injection.

    Assembles the nine plan sections in fixed order, gated by
    ``orientation_depth``: ``minimal`` renders only the status header, the
    trigger advisory, and the observe-mode proposal; ``standard`` renders all
    sections but caps lessons at 3; ``full`` renders everything uncapped.
    Every section builder runs inside its own guard — a bad state document or
    an unreadable file drops that one section, never the whole composition
    (orientation must never crash a session).
    """
    try:
        state = dict(backend.data)
    except Exception:  # fail open — orientation never crashes a session
        state = {}
    try:
        depth = orientation_depth(state)
    except Exception:  # fail open — fall back to the default depth
        depth = "standard"
    builders = (
        (1, lambda: _ori_status_header(state, config)),
        (2, lambda: _ori_stance(state)),
        (3, lambda: _ori_user_style(state)),
        (4, lambda: _ori_lessons(root, config, depth)),
        (5, lambda: _ori_triggers(root, config, state)),
        (6, lambda: _ori_practices(state, config)),
        (7, lambda: _ori_gauges(root, config)),
        (8, lambda: _ori_questions(state)),
        (9, lambda: _ori_proposal(state)),
    )
    sections: list[str] = []
    for number, build in builders:
        if depth == "minimal" and number not in _ORI_MINIMAL_SECTIONS:
            continue
        text = _ori_safe(build)
        if text:
            sections.append(text)
    if not sections:
        return ""
    return "\n\n".join(sections) + "\n"
