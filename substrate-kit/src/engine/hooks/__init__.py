"""Hook layer — the kit's runtime seams into a Claude Code session.

Four hooks: the **PreToolUse stance guard** (warns on an out-of-stance tool),
**SessionStart orientation** (injects the mode-aware composition), the
**PostToolUse edit advisor** (generated-artifact / unbadged-doc warnings), and
the **Stop-check advisor** (session-close hygiene). All advisory and fail-open
— they inform, they never block. ``settings.py`` builds the staged
``settings.template.json`` + fill-table a host merges into ``.claude/``.
"""
