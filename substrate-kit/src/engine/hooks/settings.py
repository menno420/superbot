"""Hook settings template + customization contract (plan section 5.B, Lane B7).

The staging half of the hook layer (HOOK-2): ``full_settings_template`` emits
the complete ``.claude`` ``settings.template.json`` wiring all four hook
events — PreToolUse (stance guard), SessionStart (orientation), PostToolUse
(edit advisor), Stop (session-close advisor) — each to
``<interpreter> bootstrap.py hook <event>``, the same command shape the CLI's
``_hook_command`` builds. ``hooks_fill_table`` emits the markdown
customization contract a host reads before merging: which config fields must
match their repo, and the standing rule that the kit *stages* hook settings —
it never writes a live ``.claude/`` tree itself.
"""

from __future__ import annotations

import json

from engine.lib.config import Config

# (settings.json event key, bootstrap hook event, tool matcher or None).
_SET_EVENTS: tuple[tuple[str, str, str | None], ...] = (
    ("PreToolUse", "pretooluse", "*"),
    ("SessionStart", "sessionstart", None),
    ("PostToolUse", "postedit", "Edit|Write|NotebookEdit"),
    ("Stop", "stopcheck", None),
)

_SET_FILL_ROWS: tuple[tuple[str, str], ...] = (
    (
        "`interpreter`",
        "the Python that runs the kit itself — every hook command below "
        "starts with it; set it to an interpreter available on your PATH",
    ),
    (
        "`interpreter_for_checks`",
        "your *project's* verification interpreter (the version your CI "
        "pins, e.g. `python3.10`) — kept separate from `interpreter` on "
        "purpose",
    ),
    (
        "`bootstrap.py` path",
        "each hook command assumes `bootstrap.py` sits at your repo root; "
        "rewrite the path inside every command if it lives elsewhere",
    ),
    (
        "`state_dir`",
        "where kit state + staged artifacts live (default `.substrate`) — "
        "the post-edit generated-artifact warning keys off it",
    ),
    (
        "`docs_root`",
        "your documentation root (default `docs`) — the post-edit badge "
        "warning and the SessionStart trigger scan key off it",
    ),
    (
        "`sessions_dir`",
        "where per-session logs live (default `.sessions`) — the Stop-hook "
        "session-log advisory keys off it",
    ),
    (
        "cadence knobs",
        "`cadence.*` in `substrate.config.json` (`compaction_sessions`, "
        "`reconciliation_sessions`, `staleness_days`, "
        "`critical_slot_grace_sessions`, `guided_practice_sessions`) drive "
        "the SessionStart triggers and Stop-hook advisories",
    ),
)


def _set_command(config: Config, event: str, bootstrap_path: str) -> str:
    """Return the shell command Claude Code runs for one hook event."""
    return f"{config.interpreter} {bootstrap_path} hook {event}"


def full_settings_template(config: Config, bootstrap_path: str = "bootstrap.py") -> str:
    """Return the complete ``settings.template.json`` wiring all four hooks.

    JSON text (2-space indent) a host merges into ``.claude/settings.json``:
    PreToolUse (matcher ``*``), SessionStart, PostToolUse (matcher
    ``Edit|Write|NotebookEdit``), and Stop, each running
    ``<interpreter> <bootstrap_path> hook <event>``. Matcher-less events omit
    the ``matcher`` key entirely (they apply unconditionally).
    ``bootstrap_path`` is the path the hook commands reference — adopt passes
    the vendored/root-resolved location so staged hooks resolve inside the
    target repo (the Phase-2.5 staged-hook failure cause).
    """
    hooks: dict[str, list[dict]] = {}
    for settings_event, cli_event, matcher in _SET_EVENTS:
        entry: dict = {}
        if matcher is not None:
            entry["matcher"] = matcher
        entry["hooks"] = [
            {
                "type": "command",
                "command": _set_command(config, cli_event, bootstrap_path),
            },
        ]
        hooks[settings_event] = [entry]
    return json.dumps({"hooks": hooks}, indent=2) + "\n"


def hooks_fill_table() -> str:
    """Return the markdown customization contract for the settings template.

    One ``field | what must match your repo`` row per knob a host must verify
    before installing, plus the install instruction: merge the staged template
    into ``.claude/settings.json`` yourself — the kit stages hook settings, it
    never writes a live ``.claude/`` tree.
    """
    lines = [
        "# Hook settings — customization contract",
        "",
        "The kit **stages** `settings.template.json`; it never writes your",
        "`.claude/` tree. Install by merging the template's `hooks` block into",
        "your repo's `.claude/settings.json` yourself, after checking every",
        "row below against your repo.",
        "",
        "| field | what must match your repo |",
        "| --- | --- |",
    ]
    lines += [f"| {field} | {note} |" for field, note in _SET_FILL_ROWS]
    lines += [
        "",
        "All four hooks are advisory and fail open: they always exit 0 and",
        "never block a tool, an edit, or a session stop.",
    ]
    return "\n".join(lines) + "\n"
