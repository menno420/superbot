"""Hook layer — the PreToolUse stance guard (plan section 3b, the enforcement half).

Stances ship advisory by default; this is the optional guard that makes them
*enforced*. Claude Code calls a PreToolUse hook before each tool runs, passing
the tool name; the guard maps that tool to a stance action category and, if the
action is outside the active stance's tool-scope, emits a warning. Advisory —
it warns, it does not block.
"""
