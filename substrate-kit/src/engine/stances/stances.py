"""Task-stance definitions — the fourth control axis (plan section 3b).

A *stance* is the working agent's operational posture for the current task,
distinct from adoption-pace (``mode``), promotion-rights, and stage. Following
Roo Code's proven mode model, each stance scopes three things to cut context rot
and tool misfires:

  - a **reading-route** — which docs to load first;
  - a **tool-scope** — which action categories are in-bounds;
  - an **output contract** — what the stance is expected to produce.

The active stance lives in state (``"stance"``) and is **advisory**: the contract
guides the agent, and an optional PreToolUse guard can warn on an out-of-stance
action (e.g. an edit while in ``review``) via :func:`is_out_of_stance`.

Like the question bank, the set ships as a Python module — not the plan's literal
``stances.yml`` — so it embeds in the stdlib-only bootstrap with no YAML parser
and runs identically in ``src`` and the single-file ``dist``.
"""

from __future__ import annotations

# Canonical action categories a stance's tool-scope is drawn from.
READ = "read"  # read files / memory / source
RUN = "run"  # run read-only tools / commands
EDIT = "edit"  # modify files
COMMENT = "comment"  # emit review comments (no file edits)

ACTIONS = (READ, RUN, EDIT, COMMENT)

DEFAULT_STANCE = "analysis"

STANCES: list[dict] = [
    {
        "name": "question",
        "role": "Answer concisely from memory and source; make no changes.",
        "when_to_use": "A direct question that memory or a quick read can answer.",
        "reading_route": ["current-state.md", "AGENT_ORIENTATION.md"],
        "tools": [READ],
        "output": "A concise answer grounded in memory/source; no edits.",
    },
    {
        "name": "analysis",
        "role": "Read-only deep-dive: investigate and report, do not change.",
        "when_to_use": "Understanding a system, tracing a behavior, scoping work.",
        "reading_route": ["AGENT_ORIENTATION.md", "architecture.md", "ownership.md"],
        "tools": [READ, RUN],
        "output": "Findings (evidence + conclusion), not changes.",
    },
    {
        "name": "debug",
        "role": "Read, run, and make targeted edits to fix a known fault.",
        "when_to_use": "A reproduced, localized fault with a clear blast radius.",
        "reading_route": ["runtime_contracts.md", "current-state.md"],
        "tools": [READ, RUN, EDIT],
        "output": "A targeted fix for the known fault; no broad refactor.",
    },
    {
        "name": "review",
        "role": "Evaluate a diff against the contracts; comment, do not edit.",
        "when_to_use": "Assessing a change someone else (or a prior stance) produced.",
        "reading_route": ["architecture.md", "ownership.md", "runtime_contracts.md"],
        "tools": [READ, COMMENT],
        "output": "A verdict + comments against the contracts; no edits.",
    },
    {
        "name": "plan",
        "role": "Research + safe prototyping, then propose a plan for approval.",
        "when_to_use": "A multi-step or architectural change worth designing first.",
        "reading_route": ["AGENT_ORIENTATION.md", "current-state.md", "roadmap.md"],
        "tools": [READ, RUN],
        "output": "An approved plan (research + safe prototyping; no committed change).",
    },
]

_BY_NAME = {s["name"]: s for s in STANCES}


def stance_names() -> list[str]:
    """Return the available stance names, in declared order."""
    return [s["name"] for s in STANCES]


def get_stance(name: str) -> dict | None:
    """Return the stance definition for ``name`` (or None if unknown)."""
    return _BY_NAME.get(name)


def action_allowed(name: str, action: str) -> bool:
    """True if ``action`` is in ``name``'s tool-scope (False for an unknown stance)."""
    stance = _BY_NAME.get(name)
    return stance is not None and action in stance["tools"]


def is_out_of_stance(name: str, action: str) -> bool:
    """True if ``action`` falls *outside* a known stance's tool-scope.

    The predicate a PreToolUse guard calls to warn on, e.g., an edit while the
    active stance is ``review``. Returns False for an unknown stance (nothing to
    enforce) so the guard fails **open** — it never blocks on a misconfigured name.
    """
    stance = _BY_NAME.get(name)
    if stance is None:
        return False
    return action not in stance["tools"]


def stance_briefing(name: str) -> str:
    """Return the orientation block injected for the active stance.

    The reading-route + tool-scope + output contract, formatted for injection into
    session orientation (alongside the user-style block and reflection buffer).
    """
    stance = _BY_NAME.get(name)
    if stance is None:
        choices = ", ".join(stance_names())
        return f"Unknown stance {name!r} (choose from {choices})."
    route = " -> ".join(stance["reading_route"])
    tools = ", ".join(stance["tools"])
    return (
        f"Stance: {stance['name']} — {stance['role']}\n"
        f"  When: {stance['when_to_use']}\n"
        f"  Read first: {route}\n"
        f"  In-scope actions: {tools}\n"
        f"  Output: {stance['output']}"
    )
