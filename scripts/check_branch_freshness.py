#!/usr/bin/env python3.10
"""Branch-freshness advisory hook — warn when the working branch falls behind main.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: owner-directed in-session (Q-0138, 2026-06-14). A PR can sit CONFLICTED and
  unmerged unnoticed when `main` advances *after* you pushed — exactly what happened to
  #857 (a parallel PR merged a shared ledger file). GitHub auto-merge silently waits on a
  dirty PR; nothing wakes the session. This hook surfaces the staleness so the session
  rebases (fetch + UNION-merge the ledgers) instead of leaving a rotting PR.
- Added: 2026-06-14. **Unverified** — confirm its output against ground truth over a few
  sessions before fully trusting it. **Delete this hook if it proves noisy/unreliable over
  multiple sessions** (remove the two settings.json entries + this file); it is a disposable
  convenience guard, not load-bearing.

Trigger modes:
- ``--event pretooluse`` (exit 0): wired on Bash. Reads the hook JSON on stdin; acts only when
  the command is a ``git push``. The "about to ship" moment.
- ``--event stop`` (exit 0): wired on Stop. Ignores stdin; checks the current branch on every
  turn, so a branch that fell behind *after* its last push gets flagged next turn (the #857 case).
- ``--event sessionstart`` (exit 1 when behind, else 0): called by ``claude_session_summary.py``
  so the SessionStart banner flags a *restart on a stale branch* — common when a chat spans
  several sessions and PRs merge between them, leaving the branch behind/divergent before any
  turn ends or push fires (owner-directed, Q-0188, 2026-06-20). Prints a concise one-line verdict
  to stdout; the non-zero exit is the "behind" signal the summary formats on (it is NOT wired as a
  Claude hook, so the exit code is free to differ from the always-0 advisory modes).

Robustness: every failure path swallows the error and exits 0. A PreToolUse hook runs before
*every* Bash call, so it must never block a command or add latency to non-push calls (it
returns immediately unless the command is a push).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

# High-traffic ledger/coordination files most likely to collide between parallel sessions.
# An update to one of these on main is a strong "rebase before you ship" signal.
_CROSS_CUTTING = (
    "docs/owner/active-work.md",
    "docs/current-state.md",
    "docs/ideas/README.md",
    "docs/owner/maintainer-question-router.md",
    "docs/roadmap.md",
)


def _git(*args: str, timeout: int = 15) -> str:
    """Run a git command, returning stripped stdout ('' on any failure)."""
    try:
        out = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _is_git_push(stdin_text: str) -> bool:
    """True if the PreToolUse payload is a ``git push`` Bash command."""
    try:
        payload = json.loads(stdin_text)
    except (ValueError, TypeError):
        return False
    if payload.get("tool_name") != "Bash":
        return False
    command = str(payload.get("tool_input", {}).get("command", ""))
    # Match `git push` even when chained (`a && git push ...`) or flagged.
    return any(
        seg.strip().startswith("git push")
        for seg in command.replace("&&", ";").replace("|", ";").split(";")
    )


def _freshness_warning() -> str | None:
    """Return an advisory string if the current branch is behind origin/main, else None."""
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    if not branch or branch in ("HEAD", "main"):
        return None  # detached / on main → nothing to rebase

    # Refresh our view of main (shallow, time-boxed; never hang the hook).
    _git("fetch", "origin", "main", timeout=12)

    behind = _git("rev-list", "--count", "HEAD..origin/main")
    if not behind or behind == "0":
        return None  # up to date with main — silent

    merges = _git("log", "--merges", "--pretty=format:%s", "HEAD..origin/main")
    pr_lines = [m for m in merges.splitlines() if m][:6]

    changed = set(_git("diff", "--name-only", "HEAD...origin/main").splitlines())
    hot = [f for f in _CROSS_CUTTING if f in changed]

    lines = [
        f"⚠️  branch '{branch}' is {behind} commit(s) behind origin/main — "
        "an open PR on it may now be CONFLICTED and silently un-mergeable.",
    ]
    if pr_lines:
        lines.append("   Merged on main since you branched:")
        lines.extend(f"     • {p}" for p in pr_lines)
    if hot:
        lines.append(
            "   ⚑ High-conflict ledger files changed on main: " + ", ".join(hot),
        )
    lines.append(
        "   → git fetch origin main && git merge origin/main "
        "(UNION-resolve the ledgers per the journal rule), re-verify, then re-push.",
    )
    return "\n".join(lines)


def _sessionstart_verdict() -> tuple[str, bool]:
    """(line, behind) for the SessionStart banner.

    ``behind`` is False when on main / detached / already current. The line is a single concise
    string; the count of commits *ahead* is included so the next session can tell a purely-behind
    branch (safe to reset) from a divergent one (already-squash-merged old commits, or genuine
    unpushed work — judge before resetting).
    """
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    if not branch or branch in ("HEAD", "main"):
        return ("on main / detached — n/a", False)
    _git("fetch", "origin", "main", timeout=12)
    behind = _git("rev-list", "--count", "HEAD..origin/main")
    if not behind or behind == "0":
        return ("up to date with origin/main ✓", False)
    ahead = _git("rev-list", "--count", "origin/main..HEAD") or "0"
    return (
        f"branch '{branch}' is {behind} behind / {ahead} ahead of origin/main",
        True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event",
        choices=("pretooluse", "stop", "sessionstart"),
        default="stop",
    )
    args = parser.parse_args(argv)

    if args.event == "sessionstart":
        # Called by claude_session_summary.py — print the verdict and signal behind via exit code.
        try:
            line, behind = _sessionstart_verdict()
            print(line)
            return 1 if behind else 0
        except Exception:
            return 0  # never break session start

    try:
        if args.event == "pretooluse":
            # Only the "about to push" case warrants the network round-trip.
            stdin_text = sys.stdin.read() if not sys.stdin.isatty() else ""
            if not _is_git_push(stdin_text):
                return 0
        warning = _freshness_warning()
        if warning:
            # stderr so it surfaces in the transcript without being parsed as tool output.
            print(warning, file=sys.stderr)
    except Exception:
        pass  # never let an advisory hook break a push or a turn
    return 0  # ALWAYS non-blocking


if __name__ == "__main__":
    sys.exit(main())
