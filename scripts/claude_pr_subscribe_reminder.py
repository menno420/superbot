#!/usr/bin/env python3.10
"""PostToolUse hook: nudge the agent to subscribe right after creating a PR.

Hooks are shell commands and cannot call MCP tools (``subscribe_pr_activity``)
directly. Instead this injects ``additionalContext`` reminding the agent to
subscribe immediately — closing the recurring gap where a PR got merged but the
session never learned about it (the agent only knows what's in its context).

Wired to the ``mcp__github__create_pull_request`` PostToolUse matcher in
``.claude/settings.json``.
"""

from __future__ import annotations

import json
import re
import sys

_PR_URL_RE = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")


def main() -> int:
    raw = sys.stdin.read()
    match = _PR_URL_RE.search(raw)
    pr_hint = f" ({match.group(0)})" if match else ""
    message = (
        f"A pull request was just created{pr_hint}. Before ending this turn, "
        "call mcp__github__subscribe_pr_activity for it so this session is "
        "notified of its merge, CI results, and review comments — this prevents "
        "losing track of the PR's status across the conversation."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                },
            },
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
