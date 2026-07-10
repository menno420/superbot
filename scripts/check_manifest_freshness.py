#!/usr/bin/env python3.10
"""Advisory checker: is the fleet manifest stale against the lanes' live state?

``docs/eap/fleet-manifest.md`` is the manager Project's hand-maintained registry
— one row per fleet Project, with a ``Last-seen`` cell the manager stamps from
each lane repo's ``control/status.md`` heartbeat. The gen-1 grand review
(PR #1911 §5) found every cell stale within hours of seeding (the kit-lab row
said v1.0.0 while the kit's main was at v1.6.0; the superbot-next row said "no
wind-down reaction" while the retro pair sat merged). PR #1915 reconciled it by
hand; this checker makes that reconcile free ("enforce, don't exhort", Q-0132).

What it does:

- Parses the manifest table rows → (project, repos, Last-seen date).
- For each lane repo, reads the live state **over git transport** — a shallow
  ``git fetch --depth 1`` of the default branch into a throwaway temp repo,
  then ``git cat-file`` of ``control/status.md`` to read its ``updated:``
  header. Where a repo has no ``control/status.md`` (e.g. superbot itself),
  it falls back to the HEAD committer date as an activity signal.
- Verdict per row, compared at **day precision** (the manifest cell is a date):
    FRESH  — lane's status.md ``updated:`` is not newer than Last-seen.
    STALE  — status.md ``updated:`` is a *later day* than Last-seen: the lane
             heartbeat moved and the manifest row lags. The manager re-stamp
             is the fix.
    DRIFT  — no status.md; the repo's HEAD commit is newer than Last-seen.
             Activity-only signal (a repo like superbot moves constantly), so
             it is advisory even under ``--strict``.
    SKIP   — row has no parsable repo/date, or every fetch failed (offline /
             no credentials). **Fail-open by design**: a network failure must
             never red a session.

Why git transport and not the GitHub REST API the idea file named: in agent
containers the REST API is proxy-blocked ("GitHub access is not enabled for
this session") while git is credential-injected by the same proxy — an
API-based checker would fail in exactly the environment the reconciliation
routine runs it in. Verified live against menno420/fleet-manager, 2026-07-10.

Run:  python3.10 scripts/check_manifest_freshness.py             # advisory, exit 0
      python3.10 scripts/check_manifest_freshness.py --strict    # exit 1 on STALE only
      python3.10 scripts/check_manifest_freshness.py --only kit  # filter by project

Not CI-wired (and must not be: it needs network + sibling-repo credentials).
Home: the reconciliation routine's checklist (docs/operations/autonomous-routines.md).

UNVERIFIED (Q-0105, 2026-07-10): confirm its verdicts against ground truth (open
each lane repo's control/status.md by hand) a few times across sessions before
trusting it; delete this script if it proves unreliable over multiple sessions —
it is a convenience guard, the manifest + lane repos are the source of truth.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "docs" / "eap" / "fleet-manifest.md"
STATUS_PATH = "control/status.md"

# owner/repo tokens inside the manifest's Repo(s) column (prose-tolerant).
_REPO_TOKEN = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")
_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_UPDATED_HEADER = re.compile(r"^updated:\s*(\S+)", re.MULTILINE)

FRESH = "FRESH"
STALE = "STALE"
DRIFT = "DRIFT"
SKIP = "SKIP"


@dataclass(frozen=True)
class ManifestRow:
    """One Project row of the fleet-manifest table."""

    project: str
    repos: tuple[str, ...]
    last_seen: date | None
    line: int


@dataclass
class LaneState:
    """Live state of one lane repo, read over git transport."""

    repo: str
    updated: datetime | None = None  # status.md ``updated:`` or HEAD commit date
    from_status: bool = False  # True = status.md header, False = HEAD fallback
    error: str | None = None


@dataclass
class RowVerdict:
    row: ManifestRow
    verdict: str
    detail: str
    states: list[LaneState] = field(default_factory=list)


def parse_manifest_rows(text: str) -> list[ManifestRow]:
    """Extract Project rows from the manifest's first table.

    Columns (by position, matching the committed header):
    ``| Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |``.
    The header row, the ``|---|`` separator, and any row without an
    ``owner/repo`` token in the Repo(s) column are skipped.
    """
    rows: list[ManifestRow] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if set(cells[0]) <= {"-", " "} or cells[0].lower() == "project":
            continue  # separator / header
        project = cells[0].strip("*").strip()
        repos = tuple(dict.fromkeys(_REPO_TOKEN.findall(cells[1])))
        if not repos:
            continue
        m = _DATE.search(cells[4])
        last_seen = date.fromisoformat(m.group(1)) if m else None
        rows.append(ManifestRow(project, repos, last_seen, lineno))
    return rows


def parse_status_updated(text: str) -> datetime | None:
    """The ``updated:`` header of a control/status.md, as an aware datetime."""
    m = _UPDATED_HEADER.search(text)
    if not m:
        return None
    raw = m.group(1).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _run_git(args: list[str], cwd: Path, timeout: int) -> str:
    """One git call; raises on any failure (caller converts to a SKIP)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return proc.stdout


def _repo_url(repo: str) -> str:
    """github.com URL for an ``owner/repo`` token (tests repoint to local paths)."""
    return f"https://github.com/{repo}.git"


def fetch_lane_state(repo: str, timeout: int = 60) -> LaneState:
    """Read one repo's live state: status.md ``updated:``, else HEAD date.

    Shallow-fetches the default branch (``HEAD``) into a throwaway temp repo —
    the transport the agent proxy authenticates (the REST API is blocked).
    """
    state = LaneState(repo=repo)
    url = _repo_url(repo)
    try:
        with tempfile.TemporaryDirectory(prefix="manifest-freshness-") as tmp:
            tmpdir = Path(tmp)
            _run_git(["init", "-q"], tmpdir, timeout)
            _run_git(["fetch", "--depth", "1", url, "HEAD"], tmpdir, timeout)
            try:
                blob = _run_git(
                    ["cat-file", "blob", f"FETCH_HEAD:{STATUS_PATH}"], tmpdir, timeout
                )
            except subprocess.CalledProcessError:
                blob = None  # no control/status.md in this repo → HEAD fallback
            if blob is not None:
                updated = parse_status_updated(blob)
                if updated is not None:
                    state.updated = updated
                    state.from_status = True
                    return state
                state.error = f"{STATUS_PATH} has no parsable 'updated:' header"
            head = _run_git(
                ["log", "-1", "--format=%cI", "FETCH_HEAD"], tmpdir, timeout
            ).strip()
            state.updated = datetime.fromisoformat(head)
            state.from_status = False
            state.error = None
            return state
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
        ValueError,
    ) as exc:
        state.error = f"{type(exc).__name__}: {exc}"
        return state


def _as_utc_date(dt: datetime) -> date:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.date()


def classify(row: ManifestRow, states: list[LaneState]) -> RowVerdict:
    """Compare a manifest row against its lanes' live state (day precision).

    status.md-backed states outrank HEAD-fallback ones; within a tier the
    *newest* timestamp wins (a multi-repo row is as fresh as its most recent
    lane). Same-day is FRESH — the manifest cell is date-granular, so a
    later-same-day heartbeat is indistinguishable from the stamp itself.
    """
    if row.last_seen is None:
        return RowVerdict(row, SKIP, "no parsable Last-seen date", states)
    status_backed = [s for s in states if s.updated and s.from_status]
    head_backed = [s for s in states if s.updated and not s.from_status]
    if status_backed:
        newest = max(status_backed, key=lambda s: s.updated)  # type: ignore[arg-type,return-value]
        lane_day = _as_utc_date(newest.updated)  # type: ignore[arg-type]
        detail = f"manifest {row.last_seen} vs {newest.repo} {STATUS_PATH} updated {lane_day}"
        verdict = STALE if lane_day > row.last_seen else FRESH
        return RowVerdict(row, verdict, detail, states)
    if head_backed:
        newest = max(head_backed, key=lambda s: s.updated)  # type: ignore[arg-type,return-value]
        lane_day = _as_utc_date(newest.updated)  # type: ignore[arg-type]
        detail = (
            f"manifest {row.last_seen} vs {newest.repo} HEAD {lane_day}"
            f" (no {STATUS_PATH}; activity signal only)"
        )
        verdict = DRIFT if lane_day > row.last_seen else FRESH
        return RowVerdict(row, verdict, detail, states)
    errors = "; ".join(f"{s.repo}: {s.error}" for s in states if s.error) or "no repos"
    return RowVerdict(row, SKIP, f"unreadable ({errors})", states)


def check_manifest(
    manifest: Path,
    only: str | None = None,
    timeout: int = 60,
    fetcher=None,
) -> list[RowVerdict]:
    """All row verdicts; ``fetcher`` is injectable so tests never touch network.

    ``fetcher`` resolves late (module attribute, not a def-time default) so a
    test may monkeypatch ``fetch_lane_state`` and still exercise ``main``.
    """
    if fetcher is None:
        fetcher = fetch_lane_state
    rows = parse_manifest_rows(manifest.read_text(encoding="utf-8"))
    if only:
        rows = [r for r in rows if only.lower() in r.project.lower()]
    cache: dict[str, LaneState] = {}
    verdicts: list[RowVerdict] = []
    for row in rows:
        states: list[LaneState] = []
        for repo in row.repos:
            if repo not in cache:
                cache[repo] = fetcher(repo, timeout)
            states.append(cache[repo])
        verdicts.append(classify(row, states))
    return verdicts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST, help="manifest file to check"
    )
    parser.add_argument(
        "--only", help="only rows whose Project name contains this substring"
    )
    parser.add_argument(
        "--timeout", type=int, default=60, help="per-git-call timeout (seconds)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any row is STALE (never on DRIFT/SKIP/network failure)",
    )
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(f"check_manifest_freshness: SKIP — {args.manifest} not found")
        return 0

    verdicts = check_manifest(args.manifest, only=args.only, timeout=args.timeout)
    counts = {FRESH: 0, STALE: 0, DRIFT: 0, SKIP: 0}
    for v in verdicts:
        counts[v.verdict] += 1
        print(f"  {v.verdict:5}  {v.row.project:24}  {v.detail}")
    print(
        f"check_manifest_freshness: {len(verdicts)} rows — "
        f"{counts[FRESH]} fresh, {counts[STALE]} stale, "
        f"{counts[DRIFT]} drift, {counts[SKIP]} skipped"
    )
    if counts[STALE]:
        print(
            "  STALE rows: the lane heartbeat moved after the manifest's Last-seen"
            " stamp — re-stamp docs/eap/fleet-manifest.md from each lane's"
            f" {STATUS_PATH} (the manager's reconcile, done by hand in #1915)."
        )
    return 1 if (args.strict and counts[STALE]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
