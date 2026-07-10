#!/usr/bin/env python3.10
"""Band PR status — classify a band's PRs as merged / closed-unmerged / open.

The Q-0107 reconciliation routine's ledger step relies on
``check_current_state_ledger.py``, which greps ``origin/main`` for merge-commit subjects
to find merged PRs not yet in the ledger. That works for the *recording* step, but it
**cannot tell a closed-unmerged PR apart from a genuinely-missing merged one** — so every
pass reconstructs that distinction by hand (e.g. band-#1140 had to verify #1133 was
*superseded and closed unmerged* — correctly getting no ledger entry — while #1127…#1140
were merged-and-missing). That manual cross-reference is exactly the #763-class false-green
risk the Q-0120 / Q-0181 ground-truth discipline warns about: a tool that looks authoritative
but silently omits a case the human then reconstructs ad-hoc.

This makes that classification deterministic and pasteable into a pass record's §1. For every
PR number **newer than the reconciliation marker** (``Last reconciliation pass:** PR #N`` in
``current-state.md``, or ``--since``) it prints one of:

- **merged** — a merge/squash subject for ``#N`` is reachable on ``origin/main`` (git is ground
  truth here), or the GitHub PR object reports ``merged``;
- **closed-unmerged** — the GitHub PR is closed but never merged (the #1133 case);
- **open** — still open;
- **unknown** — git says it is *not* merged on main but no GitHub read is available to tell
  closed-unmerged from open (the token-absent degraded row).

Fetch order mirrors ``check_loop_health.py``: the ``gh`` CLI first (dev shells / Actions), then a
stdlib ``urllib`` read of the GitHub REST API authed with ``GITHUB_TOKEN`` / ``GH_TOKEN`` (the
gh-absent fallback, so the script is verifiable in the routine container where ``gh`` is absent).
With neither, it still prints the **merged** rows from git alone and labels the rest ``unknown``
(naming the manual MCP read), so it never hard-fails.

Reliability (Q-0105): **unverified — added 2026-06-20.** Confirm its classification against live
GitHub a few times before trusting it; if it misclassifies over multiple sessions (a truncated PR
list, a rebase-merge git can't see, a REST rate limit), **delete it** — it is a convenience guard
for the reconciliation routine, not load-bearing. Advisory, always exit 0.

Usage:
    python3.10 scripts/band_pr_status.py            # band since the marker, human table
    python3.10 scripts/band_pr_status.py --since 1170
    python3.10 scripts/band_pr_status.py --json
    python3.10 scripts/band_pr_status.py --themes    # draft grouped-entry skeleton

``--themes`` (the band-#1260 Q-0089 idea) buckets the band's *merged* PRs by the top-level area their
files touch (read from each merge's first-parent diff) and emits a draft grouped-entry skeleton — turning
the most-manual half of a pass (reverse-engineering what each opaque ``Merge pull request #N from
…claude/funny-franklin-…`` PR actually did) into a one-command starting point the pass edits. Git-only,
so it works in the routine container with no ``gh``/token.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

REPO = "menno420/superbot"
REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO_ROOT / "docs" / "current-state.md"

# The same lag/drift boundary marker ``check_current_state_ledger.py`` keys off — kept as a
# local copy (disposable tools stay self-contained so deleting one can't break another).
_MARKER_RE = re.compile(r"Last reconciliation pass:\*\*\s*PR #(\d+)")
# A PR reference in a merge-commit subject: "Merge pull request #734", "Merge PR #734: …"
# (the MCP-merge style), or "title (#734)" (squash). Mirrors check_current_state_ledger.
# Anchored to real PR-landing forms ONLY (2026-07-10, the "#104" false-red): a
# merge commit head ("Merge pull request #N ..." / "Merge PR #N: ...") or a squash
# suffix ("title (#N)" at end-of-subject). An UN-anchored "PR #N" also matched
# cross-repo references inside ordinary branch-commit subjects that reach main via
# a true merge (e.g. "... (superbot-next ORDER 010, PR #104); ..." -> phantom #104).
_MERGE_SUBJECT_RE = re.compile(r"^Merge (?:pull request|PR) #(\d+)|\(#(\d+)\)\s*$")

MERGED = "merged"
CLOSED_UNMERGED = "closed-unmerged"
OPEN = "open"
UNKNOWN = "unknown"


def marker_pr(text: str | None = None) -> int | None:
    """The ``Last reconciliation pass:** PR #N`` marker — the band's lower bound, or None."""
    if text is None:
        try:
            text = CURRENT_STATE.read_text(encoding="utf-8")
        except OSError:
            return None
    m = _MARKER_RE.search(text)
    return int(m.group(1) or m.group(2)) if m else None


def git_merged_pr_map(limit: int = 240) -> dict[int, str]:
    """``{pr_number: merge-subject}`` for recent merges on origin/main, newest wins."""
    try:
        result = subprocess.run(
            ["git", "log", "origin/main", "--pretty=format:%s", "-n", str(limit)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return {}
    if result.returncode != 0:
        return {}
    mapping: dict[int, str] = {}
    for subject in result.stdout.splitlines():
        match = _MERGE_SUBJECT_RE.search(subject)
        if match:
            pr = int(match.group(1) or match.group(2))
            mapping.setdefault(pr, subject.strip())
    return mapping


# ---------------------------------------------------------------------------
# Theming (--themes): bucket merged PRs by the area their files touch
# ---------------------------------------------------------------------------

# Top-level path → area label, **most specific first** (first match wins per file).
# This is the bucketing the reconciliation pass does by eye when it reads a
# merge's file fan-out; the order makes `disbot/services/` beat `disbot/`.
AREA_PREFIXES: list[tuple[str, str]] = [
    ("disbot/migrations/", "disbot/migrations"),
    ("disbot/cogs/", "disbot/cogs"),
    ("disbot/services/", "disbot/services"),
    ("disbot/views/", "disbot/views"),
    ("disbot/utils/", "disbot/utils"),
    ("disbot/core/", "disbot/core"),
    ("disbot/", "disbot (other)"),
    ("docs/planning/", "docs/planning"),
    ("docs/ideas/", "docs/ideas"),
    ("docs/owner/", "docs/owner"),
    ("docs/operations/", "docs/operations"),
    ("docs/health/", "docs/health"),
    ("docs/", "docs (other)"),
    ("scripts/", "scripts"),
    ("dashboard/", "dashboard"),
    ("botsite/", "botsite"),
    (".github/", ".github"),
    (".claude/", ".claude"),
    (".sessions/", ".sessions"),
    ("tests/", "tests"),
]

# Generated artifacts + session cards accompany almost every PR and never describe
# its theme — de-weighted so they only decide the area if a PR touched nothing else.
_NOISE_PREFIXES = ("tests/", ".sessions/")
_NOISE_FILES = frozenset(
    {
        "dashboard/data/dashboard.json",
        "botsite/data/site.json",
        "botsite/site/data.js",
        "docs/owner/active-work.md",
    },
)
_AREA_ORDER = {label: i for i, (_, label) in enumerate(AREA_PREFIXES)}


def _area_of_path(path: str) -> str:
    """The area label for one file path (first matching AREA_PREFIXES entry)."""
    for prefix, label in AREA_PREFIXES:
        if path.startswith(prefix):
            return label
    return "other"


def dominant_area(files: list[str]) -> str:
    """The dominant **signal** area among a PR's touched files.

    Test files, session cards, and generated artifacts are de-weighted: they ride
    along on nearly every PR and don't describe its theme, so they only decide the
    area when a PR touched *nothing else*. Ties break by ``AREA_PREFIXES`` order
    (most specific wins), so a PR that is half ``disbot/services`` and half
    ``docs/planning`` themes as the code area, not the docs.
    """
    if not files:
        return "(no files)"
    signal = [
        f for f in files if not f.startswith(_NOISE_PREFIXES) and f not in _NOISE_FILES
    ]
    counts = Counter(_area_of_path(f) for f in (signal or files))
    best = max(counts.values())
    candidates = [area for area, c in counts.items() if c == best]
    return min(candidates, key=lambda a: _AREA_ORDER.get(a, len(AREA_PREFIXES)))


def group_by_theme(pr_files: dict[int, list[str]]) -> dict[str, list[int]]:
    """Map each area label to its band PRs (newest-first within an area)."""
    groups: dict[str, list[int]] = {}
    for pr, files in pr_files.items():
        groups.setdefault(dominant_area(files), []).append(pr)
    for prs in groups.values():
        prs.sort(reverse=True)
    return groups


def render_theme_skeleton(
    groups: dict[str, list[int]],
    pr_files: dict[int, list[str]],
) -> str:
    """A draft grouped-entry skeleton the pass edits (not the final prose).

    One bullet per area (ordered by ``AREA_PREFIXES`` specificity), naming the
    band PRs in that area and a sample of the touched paths, so the pass starts
    from "what each opaque merge-commit PR did" instead of reconstructing it cold.
    """
    if not groups:
        return "_(no merged PRs in this band)_"
    ordered = sorted(
        groups.items(),
        key=lambda kv: _AREA_ORDER.get(kv[0], len(AREA_PREFIXES)),
    )
    lines = [
        "> Draft skeleton — edit into Recently-shipped prose; not the final entry.",
        "",
    ]
    for area, prs in ordered:
        refs = " · ".join(f"#{n}" for n in prs)
        all_files = [f for n in prs for f in pr_files.get(n, [])]
        # Prefer the signal files (skip session cards / tests / generated artifacts);
        # fall back to all files when a PR touched only noise (e.g. an auto-refresh PR).
        sample: list[str] = []
        for f in all_files:
            if (
                f not in sample
                and not f.startswith(_NOISE_PREFIXES)
                and f not in _NOISE_FILES
            ):
                sample.append(f)
        if not sample:
            for f in all_files:
                if f not in sample:
                    sample.append(f)
        shown = ", ".join(sample[:4]) or "(no files)"
        more = f" (+{len(sample) - 4} more)" if len(sample) > 4 else ""
        lines.append(f"- **{area}** ({refs}) — _theme?_ · touched: {shown}{more}")
    return "\n".join(lines)


def git_merged_pr_shas(limit: int = 240) -> dict[int, str]:
    """``{pr_number: commit_sha}`` for recent merges on origin/main (newest wins)."""
    try:
        result = subprocess.run(
            ["git", "log", "origin/main", "--pretty=format:%H%x09%s", "-n", str(limit)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return {}
    if result.returncode != 0:
        return {}
    mapping: dict[int, str] = {}
    for line in result.stdout.splitlines():
        sha, _, subject = line.partition("\t")
        match = _MERGE_SUBJECT_RE.search(subject)
        if match:
            mapping.setdefault(int(match.group(1) or match.group(2)), sha.strip())
    return mapping


def pr_changed_files(sha: str) -> list[str]:
    """Files a commit changed via its first parent (``<sha>^..<sha>``).

    First-parent works for both a merge commit (the branch's net diff) and a
    squash commit (that commit's own diff). A root/parentless commit → ``[]``.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{sha}^..{sha}"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]


def classify_band(
    marker: int,
    merged_on_main: dict[int, str],
    prs: list[dict] | None,
) -> list[tuple[int, str, str]]:
    """Pure core: ``(number, status, detail)`` rows for every PR with number > ``marker``.

    ``merged_on_main`` maps a merged PR number to its merge-commit subject (git ground truth).
    ``prs`` is an optional normalized GitHub PR list — each ``{number, state, merged, title}`` —
    that lets the non-merged half be split into ``closed-unmerged`` / ``open``; without it
    (no token) those numbers can't be enumerated, so only the merged rows are reported, plus the
    caller's token-absent note. Rows are newest-first (descending number).
    """
    pr_map = {
        int(p["number"]): p
        for p in (prs or [])
        if p.get("number") is not None and int(p["number"]) > marker
    }
    numbers = {n for n in merged_on_main if n > marker} | set(pr_map)

    rows: list[tuple[int, str, str]] = []
    for n in sorted(numbers, reverse=True):
        subject = merged_on_main.get(n, "")
        pr = pr_map.get(n)
        # Git ground truth wins for "merged": a merge commit on main is authoritative even if a
        # (truncated/eventually-consistent) PR list disagrees.
        if n in merged_on_main:
            rows.append((n, MERGED, subject))
        elif pr is not None:
            title = (pr.get("title") or "").strip()
            if pr.get("merged"):
                rows.append((n, MERGED, title))
            elif str(pr.get("state", "")).lower() == "closed":
                rows.append((n, CLOSED_UNMERGED, title))
            else:
                rows.append((n, OPEN, title))
        else:  # pragma: no cover — number can only enter via one of the two sources above
            rows.append((n, UNKNOWN, ""))
    return rows


def _fetch_prs_via_gh(limit: int) -> list[dict] | None:
    """Recent PRs via ``gh``; None if gh is unavailable/unauth'd."""
    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                REPO,
                "--state",
                "all",
                "--limit",
                str(limit),
                "--json",
                "number,state,mergedAt,title",
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
            "number": p.get("number"),
            "state": p.get("state", ""),
            "merged": bool(p.get("mergedAt")),
            "title": p.get("title", ""),
        }
        for p in raw
    ]


def _github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None


def _fetch_prs_via_rest(limit: int) -> list[dict] | None:
    """Recent PRs over the GitHub REST API with stdlib urllib (gh-absent fallback)."""
    token = _github_token()
    if token is None:
        return None
    url = (
        f"https://api.github.com/repos/{REPO}/pulls"
        f"?state=all&sort=created&direction=desc&per_page={min(limit, 100)}"
    )
    req = urllib.request.Request(  # noqa: S310 — fixed https GitHub API URL
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "superbot-band-pr-status",
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
            "number": p.get("number"),
            "state": p.get("state", ""),
            "merged": p.get("merged_at") is not None,
            "title": p.get("title", ""),
        }
        for p in raw
    ]


def fetch_prs(limit: int = 100) -> tuple[list[dict] | None, str]:
    """Try ``gh``, then REST. Returns ``(prs, source)`` — source ∈ {gh, REST, none}."""
    prs = _fetch_prs_via_gh(limit)
    if prs is not None:
        return prs, "gh"
    prs = _fetch_prs_via_rest(limit)
    if prs is not None:
        return prs, "REST"
    return None, "none"


def _render_table(rows: list[tuple[int, str, str]]) -> str:
    lines = ["| PR | status | title |", "|---|---|---|"]
    for number, status, detail in rows:
        cell = detail.replace("|", "\\|")
        lines.append(f"| #{number} | {status} | {cell} |")
    return "\n".join(lines)


def _run_themes(marker: int, *, limit: int, as_json: bool) -> int:
    """The ``--themes`` path: bucket the band's merged PRs by touched area.

    Git is the only source needed here (merge SHAs + per-PR file lists), so this
    works in the routine container with no ``gh``/token, unlike the status path's
    closed-vs-open split.
    """
    shas = git_merged_pr_shas(limit=max(limit, 240))
    band = {n: sha for n, sha in shas.items() if n > marker}
    pr_files = {n: pr_changed_files(sha) for n, sha in band.items()}
    groups = group_by_theme(pr_files)

    if as_json:
        print(
            json.dumps(
                {
                    "marker": marker,
                    "groups": {
                        area: prs
                        for area, prs in sorted(
                            groups.items(),
                            key=lambda kv: _AREA_ORDER.get(kv[0], len(AREA_PREFIXES)),
                        )
                    },
                    "pr_files": {
                        str(n): files for n, files in sorted(pr_files.items())
                    },
                },
            ),
        )
        return 0

    print(
        f"Band themes — {len(band)} merged PR(s) newer than marker #{marker}, "
        f"bucketed by touched area:\n",
    )
    print(render_theme_skeleton(groups, pr_files))
    print(
        "\n(Advisory — exit 0; a starting skeleton to edit into Recently-shipped "
        "prose, not the final entry.)",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="band PR merge-status classifier.")
    parser.add_argument(
        "--since",
        type=int,
        default=None,
        help="lower-bound PR number (default: the current-state.md reconciliation marker)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--themes",
        action="store_true",
        help="draft a grouped-entry skeleton (merged PRs bucketed by touched area)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="how many recent PRs to fetch from GitHub (default 100)",
    )
    args = parser.parse_args(argv)

    marker = args.since if args.since is not None else marker_pr()
    if marker is None:
        msg = (
            "no reconciliation marker found in current-state.md and no --since given — "
            "pass --since #N (the last reconciliation PR number)."
        )
        if args.json:
            print(json.dumps({"status": "error", "reason": msg}))
        else:
            print(f"band_pr_status: {msg}")
        return 0

    if args.themes:
        return _run_themes(marker, limit=args.limit, as_json=args.json)

    merged_on_main = git_merged_pr_map(limit=max(args.limit, 240))
    prs, source = fetch_prs(args.limit)
    rows = classify_band(marker, merged_on_main, prs)

    counts: dict[str, int] = {}
    for _, status, _ in rows:
        counts[status] = counts.get(status, 0) + 1

    if args.json:
        print(
            json.dumps(
                {
                    "marker": marker,
                    "source": source,
                    "counts": counts,
                    "rows": [
                        {"number": n, "status": s, "title": d} for n, s, d in rows
                    ],
                },
            ),
        )
        return 0

    summary = ", ".join(f"{n} {s}" for s, n in sorted(counts.items())) or "no PRs"
    print(
        f"Band PR status — {len(rows)} PR(s) newer than marker #{marker} "
        f"(GitHub read: {source}): {summary}",
    )
    if rows:
        print()
        print(_render_table(rows))
    if prs is None:
        print(
            "\nNote: no `gh` and no GITHUB_TOKEN — only git's merged-on-main rows are shown. "
            "To tell closed-unmerged from open for the rest, read the band's PRs via the GitHub "
            "MCP (`list_pull_requests`, state=all) or set GITHUB_TOKEN.",
        )
    print("\n(Advisory — exit 0; paste the table into the pass record's §1.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
