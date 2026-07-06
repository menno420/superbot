#!/usr/bin/env python3.10
"""Routine permission-surface lint — flag commands a routine runs that would hit the `ask` brake.

WHY THIS EXISTS
---------------
An **unattended** routine (the dispatch / reconciliation fleet in
``docs/operations/autonomous-routines.md``) that hits a Claude Code permission
prompt **silently stalls** — there is no human to click "Allow", so the whole
scheduled run is wasted. The web/remote harness does not honor
``bypassPermissions`` and enforces ``permissions.ask`` (which outranks ``allow``),
so *any* command matching the ``ask`` list blocks the run — including just one part
of a **compound** command (``A && rm scratch && B`` stalls on the ``rm``). This has
happened more than once and was fixed **reactively** each time by widening ``allow``
/ narrowing ``ask`` (Q-0149, then Q-0161). Reactive is one stalled run too late.

This guard turns that reactive fix into a **pre-flight** one: it evaluates a small,
hand-maintained corpus of the commands the routines actually issue against the
**current** ``.claude/settings.json`` ``ask``/``allow`` rules — using the same
prefix-match semantics Claude Code uses — and reports any routine-common command
that would resolve to ``ask`` (i.e. would stall an unattended run), naming the
offending command, the ``ask`` rule that catches it, and a suggested ``allow``
narrowing.

It only reads ``.claude/settings.json``, so it is cheap enough to run in
``check_docs`` / a CI step: a settings change that would re-introduce a routine
stall is caught **before** it burns a scheduled run, not after.

PROVENANCE + RELIABILITY HEADER (owner directive Q-0105)
--------------------------------------------------------
* WHY: machine version of the Q-0161 lesson — "every command an unattended routine
  issues should resolve to ``allow``, never ``ask``; the ``ask`` list is only for
  prod/DB/force-history/external brakes."
* DATE ADDED: 2026-06-19.
* IDEA: ``docs/ideas/routine-permission-surface-lint-2026-06-16.md``.
* UNVERIFIED: confirm its output against ground truth a few times across sessions
  before trusting it — the prefix-match model here is a faithful-but-simplified
  reimplementation of Claude Code's matcher, and the routine-command corpus is
  hand-maintained (it can drift from what the routines really run).
* DELETE THIS if it proves unreliable (false positives/negatives) over multiple
  sessions — it is a disposable convenience guard, not a load-bearing check.

Usage:
    python3.10 scripts/check_routine_permission_surface.py            # warn-only (exit 0)
    python3.10 scripts/check_routine_permission_surface.py --strict   # exit 1 on any ask-hit
    python3.10 scripts/check_routine_permission_surface.py --settings PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS = REPO_ROOT / ".claude" / "settings.json"

# ---------------------------------------------------------------------------
# Routine-common command corpus.
#
# These are the commands the autonomous routines (dispatch + reconciliation) and
# their Hermes bridge actually issue during an unattended run, harvested from the
# routine prompts in ``docs/operations/autonomous-routines.md`` and
# ``docs/operations/hermes-dispatch-bridge.md``. Every one of these MUST resolve to
# ``allow`` (never ``ask``) or the run stalls with no human to unblock it.
#
# Hand-maintained on purpose (the idea's "simplest start"): when a routine prompt
# starts issuing a new command, add it here so this guard sees it.
# ---------------------------------------------------------------------------
ROUTINE_COMMANDS: tuple[str, ...] = (
    # --- sync / branch (every run) ---
    "git fetch origin main --quiet",
    "git reset --hard origin/main",
    "git checkout -b claude/some-slug origin/main",
    "git add -A",
    "git commit -m 'routine work'",
    "git push -u origin claude/some-slug",
    "git merge --no-ff claude/some-slug",
    # --- the CI-mirror / docs guards a run must pass before shipping ---
    "python3.10 scripts/check_quality.py --full",
    "python3.10 scripts/check_architecture.py --mode strict",
    "python3.10 scripts/check_docs.py --strict",
    "python3.10 scripts/check_current_state_ledger.py --strict",
    "python3.10 scripts/check_session_log.py",
    "python3.10 scripts/check_loop_health.py",
    "python3.10 scripts/check_reconciliation_due.py --strict",
    "python3.10 scripts/export_dashboard_data.py",
    "python3.10 scripts/check_dashboard_data.py --drift",
    # --- formatters / tests via the pinned interpreter ---
    "python3.10 -m pytest tests/unit -q",
    "python3.10 -m ruff format .",
    "python3.10 -m ruff check .",
    "python3.10 -m mypy disbot/",
    # --- a scratch-file cleanup inside a compound command (the Q-0161 stall) ---
    "python3.10 scripts/check_quality.py --check-only && rm -f scratch.txt",
)

# Sub-command separators that Claude Code splits a command line on before matching
# each part independently (a compound command stalls if ANY part hits `ask`).
_SEPARATORS = ("&&", "||", ";", "|")


def load_rules(settings_path: Path) -> tuple[list[str], list[str], list[str]]:
    """Return (allow, ask, deny) Bash-rule patterns from a settings.json file.

    Only ``Bash(...)`` rules are relevant to shell-command resolution; MCP/tool
    rules (e.g. ``Read``, ``mcp__github__*``) are ignored here. Returns the inner
    pattern of each ``Bash(<pattern>)`` rule, e.g. ``rm -r*`` for ``Bash(rm -r*)``.
    """
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    perms = data.get("permissions", {})

    def _bash_patterns(rules: object) -> list[str]:
        out: list[str] = []
        if not isinstance(rules, list):
            return out
        for rule in rules:
            if (
                isinstance(rule, str)
                and rule.startswith("Bash(")
                and rule.endswith(")")
            ):
                out.append(rule[len("Bash(") : -1])
        return out

    return (
        _bash_patterns(perms.get("allow")),
        _bash_patterns(perms.get("ask")),
        _bash_patterns(perms.get("deny")),
    )


def _normalize(text: str) -> str:
    """Collapse internal whitespace so matching is insensitive to spacing.

    Claude Code's matcher is prefix-based on the command string; a rule written
    ``Bash(tr *)`` (with the deliberate space) and a command ``tr a b`` should
    both reduce to single-spaced tokens before the prefix compare.
    """
    return " ".join(text.split())


def matches(command: str, pattern: str) -> bool:
    """Does a (single, already-split) command match one Bash rule pattern?

    Models Claude Code's prefix matcher: a trailing ``*`` is a prefix wildcard
    (``rm -r*`` matches ``rm -r anything``); without a trailing ``*`` the match is
    exact. A bare ``*`` anywhere is treated literally for the prefix only — the
    repo's rules use the trailing-``*`` form, which is all the routines rely on.
    """
    cmd = _normalize(command)
    pat = _normalize(pattern)
    if pat.endswith("*"):
        prefix = pat[:-1]
        # A trailing-space-then-star (e.g. "tr *") means "the word `tr` then args";
        # rstrip so "tr " prefix-matches "tr a b" after normalization.
        return cmd == prefix.rstrip() or cmd.startswith(prefix)
    return cmd == pat


def split_command(command: str) -> list[str]:
    """Split a compound shell command into its independently-evaluated parts.

    Claude Code evaluates each part of ``A && B ; C`` against the permission rules
    separately, so one ``ask``-matching part stalls the whole line. We do a simple
    separator split — good enough for the routine corpus, which uses plain
    ``&&``/``;`` joins.
    """
    # Replace every separator with a single sentinel, then split on it.
    work = command
    for sep in _SEPARATORS:
        work = work.replace(sep, "\x00")
    parts = [p.strip() for p in work.split("\x00")]
    return [p for p in parts if p]


def resolve(command: str, allow: list[str], ask: list[str], deny: list[str]) -> str:
    """Resolve ONE atomic command to ``deny`` / ``ask`` / ``allow`` / ``prompt``.

    Precedence mirrors Claude Code: ``deny`` > ``ask`` > ``allow``. A command that
    matches no rule resolves to ``prompt`` — in the remote/web harness an unmatched
    command also blocks (no ``bypassPermissions``), but the corpus here is about the
    explicit ``ask`` brake, so ``prompt`` is reported separately from ``ask``.
    """
    if any(matches(command, p) for p in deny):
        return "deny"
    if any(matches(command, p) for p in ask):
        return "ask"
    if any(matches(command, p) for p in allow):
        return "allow"
    return "prompt"


def matching_rule(command: str, patterns: list[str]) -> str | None:
    """The first rule pattern that matches the command (for diagnostics)."""
    for p in patterns:
        if matches(command, p):
            return p
    return None


class Finding:
    """One routine command part that would NOT resolve to ``allow``."""

    def __init__(self, command: str, part: str, verdict: str, rule: str | None) -> None:
        self.command = command
        self.part = part
        self.verdict = verdict  # "ask" or "prompt"
        self.rule = rule

    def describe(self) -> str:
        if self.verdict == "ask":
            return (
                f"  ✗ ASK-BRAKE: `{self.part}`\n"
                f"      from routine command: `{self.command}`\n"
                f"      caught by ask rule:   Bash({self.rule})\n"
                f"      → an unattended routine stalls here. Narrow this `ask` rule "
                f"or add a tighter `allow` so this command resolves to `allow`."
            )
        return (
            f"  ? UNMATCHED: `{self.part}`\n"
            f"      from routine command: `{self.command}`\n"
            f"      → matches no allow/ask/deny rule; in the remote harness an "
            f"unmatched command also prompts. Add an `allow` rule for it."
        )


def scan(
    commands: tuple[str, ...],
    allow: list[str],
    ask: list[str],
    deny: list[str],
    include_unmatched: bool = False,
) -> list[Finding]:
    """Return findings for every routine command part that would not auto-run.

    ``ask`` hits are always reported (the core of the lint). ``prompt`` (unmatched)
    hits are reported only when ``include_unmatched`` is set — most routine commands
    are explicitly allow-listed, so an unmatched one is usually corpus drift rather
    than a real brake, and reporting it by default would be noisy.
    """
    findings: list[Finding] = []
    for command in commands:
        for part in split_command(command):
            verdict = resolve(part, allow, ask, deny)
            if verdict == "ask":
                findings.append(Finding(command, part, "ask", matching_rule(part, ask)))
            elif verdict == "prompt" and include_unmatched:
                findings.append(Finding(command, part, "prompt", None))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lint routine-common commands against the .claude/settings.json "
            "ask/allow rules; flag any that would stall an unattended run (Q-0161)."
        ),
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=DEFAULT_SETTINGS,
        help="path to settings.json (default: .claude/settings.json)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any routine command would resolve to `ask`",
    )
    parser.add_argument(
        "--include-unmatched",
        action="store_true",
        help="also report commands that match no rule (would prompt in the remote harness)",
    )
    args = parser.parse_args(argv)

    try:
        allow, ask, deny = load_rules(args.settings)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"check_routine_permission_surface: cannot read {args.settings}: {exc}")
        return 0  # cannot read settings → don't block (warn-only philosophy)

    findings = scan(
        ROUTINE_COMMANDS,
        allow,
        ask,
        deny,
        include_unmatched=args.include_unmatched,
    )
    ask_hits = [f for f in findings if f.verdict == "ask"]

    if not findings:
        print(
            f"check_routine_permission_surface: all {len(ROUTINE_COMMANDS)} "
            "routine commands resolve to `allow` — no unattended-run stall. ✓",
        )
        return 0

    print("check_routine_permission_surface: routine commands that would NOT auto-run:")
    for finding in findings:
        print(finding.describe())

    if ask_hits:
        print(
            f"\n{len(ask_hits)} routine command(s) hit the `ask` brake. The fix is a "
            "`.claude/settings.json` change (owner-live, Q-0106) — propose it via a router "
            "Q-block; do not self-edit settings.json.",
        )
        return 1 if args.strict else 0

    # Only unmatched (prompt) findings, no hard ask-brake.
    print(
        "\nNo hard `ask`-brake — the above only match no rule (corpus drift or a new "
        "command needing an `allow`). Warn-only.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
