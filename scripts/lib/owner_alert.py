#!/usr/bin/env python3.10
"""owner_alert.py — one shared, idempotent owner-alert issue opener for CI watchdogs.

PROVENANCE / RELIABILITY (session idea Q-0089, 2026-07-05; extracted 2026-07-06):
    Every self-healing CI watchdog that gives up and escalates — ``check_ci_coverage`` (dropped
    ``pull_request:synchronize`` recovery) and ``check_codeql_coverage`` (stuck-scan recovery) — must
    open **exactly one** owner-alert issue per subject and never spam duplicates on its ``*/12`` cron.
    ``check_ci_coverage`` originally hand-rolled that marker-based dedupe; the CodeQL watchdog needs
    the identical thing. This centralizes it so escalation is consistent, deduped, and unit-tested in
    **one** place instead of each watchdog re-implementing it subtly differently.

    Best-effort ``gh`` I/O — degrades to a ``False`` return (the caller just logs) when ``gh``/token is
    absent, exactly like the watchdogs' other ``gh`` calls. **Delete/inline this module if it proves
    unreliable** (Q-0105); opening an alert issue by hand is always possible.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable

# ``search(repo, marker)`` — does an open issue carrying ``marker`` already exist?
#   True  → yes (dedupe: do nothing)   False → no (create one)   None → gh unavailable (can't tell)
IssueSearch = Callable[[str, str], "bool | None"]
# ``create(repo, title, body)`` — create the issue; True on success.
IssueCreate = Callable[[str, str, str], bool]


def alert_marker(kind: str, key: object) -> str:
    """A hidden HTML marker uniquely identifying an alert subject, for cross-run dedupe.

    ``kind`` namespaces the watchdog (e.g. ``"ci-coverage"``, ``"codeql-coverage"``); ``key`` is the
    subject (usually a PR number). Distinct ``kind`` values never collide, so two different watchdogs
    can alert on the same PR without deduping each other away.
    """
    return f"<!-- {kind}-alert:{key} -->"


def ensure_issue(
    repo: str,
    marker: str,
    title: str,
    body: str,
    *,
    search: IssueSearch | None = None,
    create: IssueCreate | None = None,
) -> bool:
    """Idempotently ensure one open owner-alert issue carrying ``marker`` exists.

    Returns True if the issue already existed or was just created; False if gh was unavailable or the
    create failed (the caller logs either way). ``body`` **must** contain ``marker`` so the next cron
    pass finds it and dedupes. ``search``/``create`` are injected in tests and default to the
    gh-backed implementations below.

    Conservative on an unknown dedupe state: if ``search`` returns None (gh unavailable), do **not**
    create — a delayed alert (the next 12-min pass retries) is better than a duplicate we could not
    rule out.
    """
    search = search or gh_issue_search
    create = create or gh_issue_create
    existing = search(repo, marker)
    if existing is None:
        return False  # gh unavailable — can't confirm dedupe, so don't risk a duplicate
    if existing:
        return True  # already alerted
    return create(repo, title, body)


# --------------------------------------------------------------------------- #
# gh-backed defaults (skipped cleanly when gh/token absent)
# --------------------------------------------------------------------------- #


def _gh(args: list[str]) -> str | None:
    try:
        return subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def gh_issue_search(repo: str, marker: str) -> bool | None:
    """True/False whether an open issue carrying ``marker`` exists; None if gh is unavailable."""
    out = _gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--search",
            marker,
            "--json",
            "number",
        ],
    )
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    return bool(data)


def gh_issue_create(repo: str, title: str, body: str) -> bool:
    """Create an issue; True on success, False on any failure."""
    return (
        _gh(
            ["issue", "create", "--repo", repo, "--title", title, "--body", body],
        )
        is not None
    )
