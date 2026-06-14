"""PreToolUse stance guard — makes the stance layer enforced, not just advisory.

Claude Code calls a PreToolUse hook before each tool runs, passing the tool name
in a JSON payload on stdin. This maps the tool to a stance action category
(read / run / edit / comment) and, if that action is outside the active stance's
tool-scope, produces an advisory warning — the agent stays free to proceed
(stances are advisory by default, plan section 3b). The bootstrap
``hook pretooluse`` command is the runtime entry point; ``settings_snippet``
generates the ``.claude/settings.json`` wiring a host installs.

Everything here **fails open**: an unknown tool, an unknown stance, or a
malformed payload yields no warning — the guard never gets in the way when it is
unsure.
"""

from __future__ import annotations

import json

from engine.stances.stances import EDIT, READ, RUN, is_out_of_stance

# Claude Code tool name -> the stance action category it performs. Tools not
# listed (Task, the slash-command tools, …) carry no stance opinion (fail open).
TOOL_ACTIONS: dict[str, str] = {
    "Read": READ,
    "Grep": READ,
    "Glob": READ,
    "NotebookRead": READ,
    "Edit": EDIT,
    "Write": EDIT,
    "NotebookEdit": EDIT,
    "Bash": RUN,
    "WebFetch": RUN,
    "WebSearch": RUN,
}


def tool_to_action(tool_name: str) -> str | None:
    """Return the stance action category a Claude Code tool performs (or None)."""
    return TOOL_ACTIONS.get(tool_name)


def tool_from_payload(raw: str) -> str:
    """Extract the tool name from a PreToolUse stdin payload (``""`` if absent)."""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return ""
    name = payload.get("tool_name", "") if isinstance(payload, dict) else ""
    return name if isinstance(name, str) else ""


def evaluate_tool(stance: str, tool_name: str) -> str | None:
    """Return an out-of-stance warning for ``tool_name`` under ``stance``, or None.

    ``None`` means no objection — the tool carries no stance opinion, or the
    action is within the stance's tool-scope. Fails open: an unknown stance or
    tool never warns.
    """
    action = tool_to_action(tool_name)
    if action is None or not is_out_of_stance(stance, action):
        return None
    return (
        f"out-of-stance: {tool_name} ({action}) while stance is '{stance}'. "
        "Re-check the task, or switch stance (`bootstrap stance <name>`). "
        "(advisory — not blocked)"
    )


def settings_snippet(command: str) -> str:
    """Return a ``.claude/settings.json`` PreToolUse wiring snippet (JSON text).

    ``command`` is the shell command Claude Code runs before each tool (e.g.
    ``python3 bootstrap.py hook pretooluse``). The host merges the returned
    ``hooks.PreToolUse`` block into their ``.claude/settings.json``.
    """
    snippet = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [{"type": "command", "command": command}],
                },
            ],
        },
    }
    return json.dumps(snippet, indent=2) + "\n"
