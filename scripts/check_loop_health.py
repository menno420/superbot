#!/usr/bin/env python3.10
"""Loop-health probe — verify the autonomous control-plane against live GitHub.

The autonomous loop spans the repo **and** a GitHub/Railway/console control plane.
The repo-side `check_*` scripts can't see the control-plane half, so its state lived
only in a hand-maintained table in `docs/operations/autonomous-routines.md` § Control-plane
state — and that table **drifted**: it claimed `ROUTINE_PAT` was unverified and the loop had
never self-fired, when live GitHub already proved both true (2026-06-14 review). This probe
closes that gap: it reads recent issues via the `gh` CLI and re-derives the verifiable rows,
so a session (or the reconciliation routine) can spot regressions instead of trusting a stale
tick-box.

What it can verify from GitHub alone:
- **ROUTINE_PAT live?** — the workflows auto-open the scheduled-executor / `reconcile` trigger
  issues; if `ROUTINE_PAT` is set they are authored by the PAT owner (a real user login), and
  if it is unset they fall back to `github-actions[bot]`, which does NOT start a Claude routine.
  So the *author* of the newest auto-opened trigger issue is a live read of the secret's state.
- **DATABASE_PUBLIC_URL set?** — `backup-db.yml` opens a "Postgres backup failed" issue when the
  secret is missing; an OPEN one means backups are inert right now.
- **Loop self-fired?** — a closed "Scheduled executor run" issue is evidence the unattended cron
  path ran end-to-end.

What it canNOT see (stays maintainer-verified in the table): Railway env-var deploys, routine
model/prompt config in the console. Those rows are out of scope by design.

Fetch order: the `gh` CLI first (works in dev shells / Actions), then — when `gh` is absent (the
routine container) — a stdlib `urllib` read of the GitHub REST API authed with `GITHUB_TOKEN`
(the **gh-absent REST fallback**, added 2026-06-20 so the script is verifiable in the one place it
is meant to run). Only if both are unavailable does it emit an *actionable* SKIP that names the
manual MCP read.

Reliability (Q-0105): **unverified — added 2026-06-14 (Q-0135); REST fallback added 2026-06-20.**
Confirm its verdicts against the real GitHub state a few times before trusting it; if its
heuristics (or the REST read — rate limits, token scope) misclassify over multiple sessions,
**delete it** — it is a convenience drift-guard, not load-bearing. Degrades to SKIP (exit 0)
wherever neither `gh` nor a token is available, so it never reddens a session.

Usage:
    python3.10 scripts/check_loop_health.py            # advisory, human-readable
    python3.10 scripts/check_loop_health.py --json      # machine-readable verdicts
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "menno420/superbot"

# Title prefix the reconcile trigger workflow uses (reconciliation-trigger.yml). The
# executor-nightly.yml workflow was removed 2026-06-15 (Q-0146 — dispatch is now the console
# Schedule, which opens no issue); its old "Scheduled executor run" issues may still exist in
# history, so the prefix is kept as a legacy match. The reconcile issue is now the live
# ROUTINE_PAT canary.
_EXECUTOR_PREFIX = "Scheduled executor run"
_RECONCILE_TITLE = "Docs reconciliation due"
_BACKUP_PREFIX = "Postgres backup failed"

# A bot login here means ROUTINE_PAT was NOT used (GITHUB_TOKEN fallback) → routine won't fire.
_BOT_LOGINS = {"github-actions", "github-actions[bot]"}


def classify(issues: list[dict]) -> list[tuple[str, str, str]]:
    """Pure core: derive (check, status, detail) verdicts from a list of issues.

    Each issue dict: {number, title, author_login, state, created_at}. ``issues`` is assumed
    newest-first (the order ``gh issue list`` returns). status ∈ {PASS, WARN, FAIL, SKIP}.
    """
    verdicts: list[tuple[str, str, str]] = []

    # --- ROUTINE_PAT (the hard blocker) -------------------------------------------------
    trigger = next(
        (
            i
            for i in issues
            if i["title"].startswith(_EXECUTOR_PREFIX)
            or i["title"].startswith(_RECONCILE_TITLE)
        ),
        None,
    )
    if trigger is None:
        verdicts.append(
            (
                "ROUTINE_PAT",
                "SKIP",
                "no auto-opened trigger issue in recent history to read",
            ),
        )
    elif trigger["author_login"] in _BOT_LOGINS:
        verdicts.append(
            (
                "ROUTINE_PAT",
                "FAIL",
                f"trigger issue #{trigger['number']} is authored by "
                f"`{trigger['author_login']}` — ROUTINE_PAT looks UNSET, so the routine will "
                f"not fire. Add the fine-grained PAT (Issues: read/write).",
            ),
        )
    else:
        verdicts.append(
            (
                "ROUTINE_PAT",
                "PASS",
                f"trigger issue #{trigger['number']} authored by `{trigger['author_login']}` "
                f"(not a bot) — ROUTINE_PAT is set and the loop can self-fire.",
            ),
        )

    # --- DATABASE_PUBLIC_URL (backups) --------------------------------------------------
    open_backup = next(
        (
            i
            for i in issues
            if i["title"].startswith(_BACKUP_PREFIX) and i["state"].upper() == "OPEN"
        ),
        None,
    )
    if open_backup is not None:
        verdicts.append(
            (
                "DATABASE_PUBLIC_URL",
                "FAIL",
                f"open backup-failure issue #{open_backup['number']} — the daily pg_dump is "
                f"inert; DATABASE_PUBLIC_URL is likely unset/stale. No working DB backups.",
            ),
        )
    else:
        verdicts.append(
            (
                "DATABASE_PUBLIC_URL",
                "PASS",
                "no open backup-failure issue — backups are not currently erroring.",
            ),
        )

    # --- Loop self-fired (informational) ------------------------------------------------
    fired = next((i for i in issues if i["title"].startswith(_EXECUTOR_PREFIX)), None)
    if fired is not None:
        verdicts.append(
            (
                "loop-self-fired",
                "PASS",
                f"scheduled executor issue #{fired['number']} exists — the unattended cron "
                f"path has run.",
            ),
        )
    else:
        verdicts.append(
            (
                "loop-self-fired",
                "SKIP",
                "no scheduled-executor issue seen in recent history",
            ),
        )

    return verdicts


def _fetch_via_gh(limit: int = 40) -> list[dict] | None:
    """Fetch recent issues via `gh`. Returns None if gh is unavailable/unauth'd."""
    try:
        proc = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                REPO,
                "--state",
                "all",
                "--limit",
                str(limit),
                "--json",
                "number,title,author,state,createdAt",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return [
        {
            "number": i.get("number"),
            "title": i.get("title", ""),
            "author_login": (i.get("author") or {}).get("login", ""),
            "state": i.get("state", ""),
            "created_at": i.get("createdAt", ""),
        }
        for i in raw
    ]


def _github_token() -> str | None:
    """The token to authenticate the REST fallback, if the env supplies one."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None


def _fetch_via_rest(limit: int = 40) -> list[dict] | None:
    """Fetch recent issues over the GitHub REST API with stdlib urllib (gh-absent fallback).

    No new dependency — `urllib` + `json` are stdlib. Returns None when no token is set or the
    request fails (→ the caller falls through to an actionable SKIP). Note: the REST issues
    endpoint also returns pull requests; ``classify`` matches on title prefixes only, so the PR
    rows are harmless, but we keep the same fields ``classify`` consumes.
    """
    token = _github_token()
    if token is None:
        return None
    url = (
        f"https://api.github.com/repos/{REPO}/issues"
        f"?state=all&sort=created&direction=desc&per_page={limit}"
    )
    req = urllib.request.Request(  # noqa: S310 — fixed https GitHub API URL
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "superbot-check-loop-health",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            raw = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None
    if not isinstance(raw, list):
        return None
    return [
        {
            "number": i.get("number"),
            "title": i.get("title", ""),
            "author_login": (i.get("user") or {}).get("login", ""),
            "state": i.get("state", ""),
            "created_at": i.get("created_at", ""),
        }
        for i in raw
    ]


def fetch_issues(limit: int = 40) -> tuple[list[dict] | None, str]:
    """Try `gh`, then the REST fallback. Returns (issues, source) — source ∈ {gh, REST, SKIP}."""
    issues = _fetch_via_gh(limit)
    if issues is not None:
        return issues, "gh"
    issues = _fetch_via_rest(limit)
    if issues is not None:
        return issues, "REST"
    return None, "SKIP"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    issues, source = fetch_issues()
    if issues is None:
        reason = (
            "neither `gh` nor a GITHUB_TOKEN is available — control-plane not probed. "
            "Manual fallback: read the newest `reconcile` issue's author via the GitHub MCP "
            "(a real-user login = ROUTINE_PAT set; `github-actions[bot]` = unset)."
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "SKIP",
                        "source": "SKIP",
                        "reason": reason,
                        "verdicts": [],
                    },
                ),
            )
        else:
            print(f"check_loop_health: SKIP — {reason}")
        return 0

    verdicts = classify(issues)
    if args.json:
        print(
            json.dumps(
                {
                    "source": source,
                    "verdicts": [
                        {"check": c, "status": s, "detail": d} for c, s, d in verdicts
                    ],
                },
            ),
        )
    else:
        print(
            f"Loop-health probe (control-plane state, live from GitHub via {source}):",
        )
        for check, status, detail in verdicts:
            print(f"  [{status:>4}] {check}: {detail}")
        print(
            "\n(Advisory only — exit 0. FAIL rows are real but maintainer-side; see "
            "docs/operations/autonomous-routines.md § Control-plane state.)",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
