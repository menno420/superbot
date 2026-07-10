#!/usr/bin/env python3.10
"""check_lane_overlap.py — before starting work on a scope, flag whether that scope was
already touched by *recently-merged* work (the #1133/#1128 duplicate-work lesson).

PROVENANCE / RELIABILITY (2026-06-19, mechanizes ultracode-fleet-plan rule #7 / the #1137
fleet-dispatch overlap-check rule):
    Why: lane B4 (PR #1133) rebuilt the consistency-linter cog-scope work that #1128 had
    merged ~8 minutes earlier, because the orchestrator trusted a stale claim ledger instead
    of scanning what had actually shipped. The fleet's fix was a *procedural* "MUST scan
    recent PRs" rule — but the incident happened *because* a manual step got skipped. This
    gives that rule teeth: a script the orchestrator runs so overlap-detection doesn't depend
    on memory.

    UNVERIFIED — heuristic, and **partial by construction**: it sees only the *recently-merged*
    half (local git history). The *open-PR* half (a concurrent unmerged PR touching the same
    files) needs GitHub and CANNOT be checked locally — always ALSO run `list_pull_requests`.
    Confirm its hits across a few sessions; **delete it if it proves noisy/unreliable.**

PROVENANCE / RELIABILITY — ``--remote`` mode (2026-07-10, builds
``docs/ideas/claim-remote-visibility-scan-2026-07-08.md``):
    Why: a claim committed on a sibling session's un-merged branch is invisible to the local
    claims dir until that branch merges — in practice ``docs/owner/claims/`` on ``main`` is
    almost always just ``README.md``, because claims are deleted at close before the PR merges.
    So the pre-PR window (born-red push → PR open) was uncovered — the exact race a parallel
    wave lives in (the #1221 duplicate-PR lesson). ``--remote`` reads sibling claims at their
    *native* layer (git refs): enumerate recent ``origin/claude/*`` / ``origin/bot/*`` tips,
    diff each one's ``docs/owner/claims/`` files against ``origin/main``, and fold those
    claims into the same overlap scan.

    UNVERIFIED — confirm its hits against real sibling branches a few times across sessions
    before trusting it; **delete the ``--remote`` half if it proves noisy/unreliable.** It
    degrades gracefully offline (warns and returns local-only results; exit code unaffected
    by the degradation itself).

Usage:
    check_lane_overlap.py <scope> [<scope> ...] [--limit N] [--strict]
                          [--remote] [--remote-days D] [--no-fetch]

    <scope>       — files / directories / globs the lane will touch
                    (e.g. `scripts/check_consistency.py`, `disbot/views/mining/`).
    --limit       — how many recent commits to scan (default 80 — ~2 burst bands).
    --strict      — exit 1 if any overlap is found (for a dispatch gate once trusted).
    --remote      — ALSO scan recent un-merged `origin/claude/*` / `origin/bot/*` branches
                    for claim files not on main: a sibling that pushed its born-red first
                    commit becomes visible BEFORE its PR exists. Fetches first.
    --remote-days — how far back a remote branch tip counts as "recent" (default 4).
    --no-fetch    — with --remote: skip `git fetch origin`; scan already-fetched refs only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from fnmatch import fnmatch
from pathlib import Path
from posixpath import basename
from typing import cast

_RS = "\x1e"  # record separator between commits
_US = "\x1f"  # unit separator between hash and subject

# The claim ledger (Q-0126) — the *earliest* duplicate-work signal: a claim
# exists before any PR or commit does, so it catches overlap the merged-commit
# scan structurally cannot (the #1221 duplicate-reaction-roles-PR2 lesson).
# Q-0195 (2026-06-22): claims are now **one file per claim** under
# ``docs/owner/claims/`` (the single shared file produced a ~98% merge-conflict
# rate — `tools/sim/claim_layout_sim.py`). Each file holds one claim bullet in the
# same backtick-token format, so the same parser reads it.
_CLAIMS_DIR = Path(__file__).resolve().parents[1] / "docs" / "owner" / "claims"

# A backtick token is a *path* (not a branch/component name) when it contains a
# "/" or ends in a source extension — and is not a branch ref.
_PATH_EXTS = (".py", ".sql", ".md", ".yml", ".yaml", ".json", ".ts", ".tsx", ".js")
_BRANCH_PREFIXES = ("claude/", "bot/", "origin/")
_BACKTICK = re.compile(r"`([^`]+)`")


def _recent_commits(limit: int) -> list[tuple[str, str, list[str]]]:
    """Return [(short_hash, subject, [changed_files])] for the last *limit* commits."""
    out = subprocess.run(
        ["git", "log", f"-n{limit}", "--name-only", f"--format={_RS}%h{_US}%s"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits: list[tuple[str, str, list[str]]] = []
    for record in out.split(_RS):
        if not record.strip():
            continue
        lines = record.split("\n")
        short_hash, _, subject = lines[0].partition(_US)
        files = [ln for ln in lines[1:] if ln.strip()]
        commits.append((short_hash, subject, files))
    return commits


def _matches(path: str, scope: str) -> bool:
    """A changed *path* belongs to *scope* (an exact file, a dir prefix, or a glob)."""
    scope = scope.rstrip("/")
    if path == scope or path.startswith(scope + "/"):
        return True
    return any(ch in scope for ch in "*?[") and fnmatch(path, scope)


# ---------------------------------------------------------------------------
# Claim-ledger scan (docs/owner/claims/, Q-0195)
# ---------------------------------------------------------------------------


def _norm_path(p: str) -> str:
    """Normalize for cross-comparison: drop a leading ``disbot/``, trailing ``/``.

    Claim lines write repo-relative paths inconsistently (``services/x.py`` vs
    ``disbot/services/x.py``); stripping the package prefix aligns both forms.
    """
    p = p.strip().rstrip("/")
    return p[len("disbot/") :] if p.startswith("disbot/") else p


def _is_path_token(tok: str) -> bool:
    if tok.startswith(_BRANCH_PREFIXES):
        return False
    return "/" in tok or tok.endswith(_PATH_EXTS)


def _paths_overlap(a: str, b: str) -> bool:
    """True when normalized paths ``a`` and ``b`` are the same or nest either way."""
    a, b = _norm_path(a), _norm_path(b)
    if not a or not b:
        return False
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def _build_claim(entry_lines: list[str]) -> dict[str, object]:
    """Build one ``{branch, summary, paths}`` entry from a claim bullet's lines."""
    entry_text = " ".join(s.strip() for s in entry_lines).strip()
    tokens = _BACKTICK.findall(entry_text)
    branch = next((t for t in tokens if t.startswith(_BRANCH_PREFIXES)), "?")
    paths = [t for t in tokens if _is_path_token(t)]
    # The human-readable scope is the bold **...** title, when present.
    m = re.search(r"\*\*(.+?)\*\*", entry_text)
    summary = m.group(1) if m else entry_text[:80]
    return {"branch": branch, "summary": summary, "paths": paths}


def _bullets_to_claims(block: list[str]) -> list[dict[str, object]]:
    """Group ``- `` bullets (with continuation lines) into claim entries."""
    claims: list[dict[str, object]] = []
    current: list[str] = []
    for ln in block:
        if ln.lstrip().startswith("- "):  # new claim entry
            if current:
                claims.append(_build_claim(current))
            current = [ln]
        elif current:  # continuation line of the current claim
            current.append(ln)
    if current:
        claims.append(_build_claim(current))
    return claims


def parse_claims(text: str) -> list[dict[str, object]]:
    """Parse the ``## Active claims`` block into ``{branch, summary, paths}`` entries.

    Pure (text in, structured out) so it is unit-testable without the real file.
    Retained for the legacy single-file layout / tests; the live source is now a
    directory of per-claim files (see :func:`parse_claim_file`).
    """
    lines = text.splitlines()
    try:
        start = next(
            i for i, ln in enumerate(lines) if ln.strip().lower() == "## active claims"
        )
    except StopIteration:
        return []
    block: list[str] = []
    for ln in lines[start + 1 :]:
        if ln.startswith("## "):  # next section ends the block
            break
        block.append(ln)
    return _bullets_to_claims(block)


def parse_claim_file(text: str) -> list[dict[str, object]]:
    """Parse one per-claim file (Q-0195) — its top-level ``- `` bullets, no header.

    A claim file holds a single claim bullet, but tolerate more than one. Heading
    lines and prose are ignored; only ``- `` bullets become claims.
    """
    return _bullets_to_claims(text.splitlines())


def scan_claims(
    scopes: list[str],
    claims: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """Map each scope -> the active claims whose declared paths overlap it."""
    hits: dict[str, list[dict[str, object]]] = {}
    for scope in scopes:
        matched: list[dict[str, object]] = []
        for claim in claims:
            paths = cast("list[str]", claim["paths"])
            overlap = [p for p in paths if _paths_overlap(p, scope)]
            if overlap:
                matched.append({**claim, "matched": overlap})
        if matched:
            hits[scope] = matched
    return hits


def _load_claims() -> list[dict[str, object]]:
    """Load every live claim from the per-claim directory (Q-0195).

    One file per claim under ``docs/owner/claims/`` (``README.md`` excluded). The
    directory layout is what keeps concurrent sessions conflict-free; never collapse
    it back into one shared file (see the module + README provenance notes).
    """
    if not _CLAIMS_DIR.is_dir():
        return []
    claims: list[dict[str, object]] = []
    for path in sorted(_CLAIMS_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        try:
            claims.extend(parse_claim_file(path.read_text(encoding="utf-8")))
        except OSError:
            continue
    return claims


# ---------------------------------------------------------------------------
# Remote-branch claim scan (--remote) — claims on un-merged sibling branches
# ---------------------------------------------------------------------------

# Branch namespaces agent sessions push to (see Q-0126 / claims README).
_REMOTE_REF_PATTERNS = ("refs/remotes/origin/claude", "refs/remotes/origin/bot")
_REMOTE_BASE = "origin/main"
_CLAIMS_REL = "docs/owner/claims/"


def _git(args: list[str], timeout: int = 60) -> str:
    """Run one git command and return stdout (raises on failure — callers degrade)."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout,
    ).stdout


def parse_ref_lines(text: str, cutoff_epoch: int) -> list[str]:
    """Pure: ``<unix-committerdate>\\t<refname>`` lines -> refs at/after *cutoff_epoch*."""
    refs: list[str] = []
    for ln in text.splitlines():
        stamp, _, ref = ln.strip().partition("\t")
        if not ref:
            continue
        try:
            fresh = int(stamp) >= cutoff_epoch
        except ValueError:
            continue
        if fresh:
            refs.append(ref)
    return refs


def _own_remote_ref() -> str:
    """The remote-tracking name of the *current* branch (skipped — it's our own claim)."""
    try:
        branch = _git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    except (subprocess.SubprocessError, OSError):
        return ""
    return f"origin/{branch}" if branch and branch != "HEAD" else ""


def _claim_files_at(ref: str) -> set[str]:
    """Claim-file paths present at *ref*'s tip (README excluded). Raises on git failure.

    Tip-state comparison on purpose (not a merge-base diff): claims are transient
    tip-state by design (created at open, deleted at close), and ``ls-tree`` needs
    only the tip object — so this also works in the shallow clones agent containers
    use, where ``origin/main...ref`` often has **no merge base** and diff dies.
    """
    out = _git(["ls-tree", "-r", "--name-only", ref, "--", _CLAIMS_REL])
    return {
        ln.strip()
        for ln in out.splitlines()
        if ln.strip() and basename(ln.strip()).lower() != "readme.md"
    }


def load_remote_claims(
    days: int,
    fetch: bool = True,
) -> tuple[list[dict[str, object]], list[str]]:
    """Claims present on recent un-merged sibling branch tips but not on origin/main.

    Each claim dict gains a ``"ref"`` key naming the branch it was found on. Every
    network/git failure degrades to a warning string instead of raising, so an
    offline run still produces the local-only result.
    """
    warnings: list[str] = []
    if fetch:
        try:
            _git(["fetch", "--quiet", "origin"], timeout=120)
        except (subprocess.SubprocessError, OSError):
            warnings.append(
                "git fetch failed (offline?) — scanning already-fetched refs only",
            )
    try:
        out = _git(
            [
                "for-each-ref",
                "--format=%(committerdate:unix)\t%(refname:short)",
                *_REMOTE_REF_PATTERNS,
            ],
        )
        base_files = _claim_files_at(_REMOTE_BASE)
    except (subprocess.SubprocessError, OSError):
        warnings.append("remote-ref scan unavailable — local-only results")
        return [], warnings

    cutoff = int(time.time()) - days * 86400
    own = _own_remote_ref()
    claims: list[dict[str, object]] = []
    skipped: list[str] = []
    for ref in parse_ref_lines(out, cutoff):
        if ref == own:
            continue  # our own branch's claim is not a *sibling* claim
        try:
            names = _claim_files_at(ref) - base_files
        except (subprocess.SubprocessError, OSError):
            skipped.append(ref)
            continue
        for name in sorted(names):
            try:
                text = _git(["show", f"{ref}:{name}"])
            except (subprocess.SubprocessError, OSError):
                continue
            for claim in parse_claim_file(text):
                claims.append({**claim, "ref": ref})
    if skipped:
        shown = ", ".join(skipped[:3]) + ("…" if len(skipped) > 3 else "")
        warnings.append(f"could not inspect {len(skipped)} ref(s) — skipped ({shown})")
    return claims, warnings


def scan(scopes: list[str], limit: int) -> dict[str, list[tuple[str, str, list[str]]]]:
    """Map each scope -> the recent commits whose files overlap it."""
    commits = _recent_commits(limit)
    hits: dict[str, list[tuple[str, str, list[str]]]] = {}
    for scope in scopes:
        overlaps = []
        for short_hash, subject, files in commits:
            matched = [f for f in files if _matches(f, scope)]
            if matched:
                overlaps.append((short_hash, subject, matched))
        if overlaps:
            hits[scope] = overlaps
    return hits


_FOOTER = (
    "\n  NOTE: this covers the recently-MERGED commits (local git) + the docs/owner/claims/ "
    "claim ledger (add --remote to also see claims pushed on un-merged sibling branches). "
    "The OPEN-PR half (a concurrent unmerged PR with no claim line) still "
    "needs GitHub — ALSO run `list_pull_requests`."
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "scopes",
        nargs="+",
        help="files / dirs / globs the lane will touch",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=80,
        help="recent commits to scan (default 80)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any overlap is found (dispatch gate)",
    )
    ap.add_argument(
        "--remote",
        action="store_true",
        help="also scan recent un-merged origin/claude|bot branches for claim files",
    )
    ap.add_argument(
        "--remote-days",
        type=int,
        default=4,
        help="how far back a remote branch tip counts as recent (default 4 days)",
    )
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="with --remote: skip `git fetch origin` (offline mode)",
    )
    args = ap.parse_args()

    hits = scan(args.scopes, args.limit)
    claim_hits = scan_claims(args.scopes, _load_claims())
    remote_hits: dict[str, list[dict[str, object]]] = {}
    if args.remote:
        remote_claims, remote_warnings = load_remote_claims(
            args.remote_days,
            fetch=not args.no_fetch,
        )
        for warning in remote_warnings:
            print(f"check_lane_overlap: ⚠ {warning}")
        remote_hits = scan_claims(args.scopes, remote_claims)

    if not hits and not claim_hits and not remote_hits:
        checked = "recently-merged commits + local claims"
        if args.remote:
            checked += f" + un-merged origin branches (last {args.remote_days}d)"
        print(
            f"check_lane_overlap: no overlap ({checked}, last {args.limit} commits) with "
            f"{', '.join(args.scopes)} ✓" + _FOOTER,
        )
        return 0

    if remote_hits:
        print(
            "check_lane_overlap: ⚠ REMOTE CLAIM — an un-merged sibling branch claims this "
            "scope (pushed; its PR may not exist yet). Coordinate or pick another lane:\n",
        )
        for scope, claims in remote_hits.items():
            print(f"  scope `{scope}`:")
            for claim in claims:
                shown = ", ".join(cast("list[str]", claim["matched"])[:4])
                print(f"    {claim['ref']}  {claim['summary']}")
                print(f"             ↳ {shown}")
        print()

    if claim_hits:
        print(
            "check_lane_overlap: ⚠ CLAIMED — this scope is claimed by a parallel session "
            "in docs/owner/claims/. Coordinate or pick another lane before building:\n",
        )
        for scope, claims in claim_hits.items():
            print(f"  scope `{scope}`:")
            for claim in claims:
                shown = ", ".join(cast("list[str]", claim["matched"])[:4])
                print(f"    {claim['branch']}  {claim['summary']}")
                print(f"             ↳ {shown}")
        print()

    if hits:
        print(
            "check_lane_overlap: ⚠ OVERLAP — this scope was touched by recently-merged work. "
            "Verify it didn't already ship your lane (drop/re-scope before dispatch):\n",
        )
        for scope, overlaps in hits.items():
            print(f"  scope `{scope}`:")
            for short_hash, subject, matched in overlaps:
                shown = ", ".join(matched[:4])
                more = "" if len(matched) <= 4 else f" (+{len(matched) - 4})"
                print(f"    {short_hash}  {subject[:72]}")
                print(f"             ↳ {shown}{more}")
    print(_FOOTER)
    return 1 if (args.strict and (hits or claim_hits or remote_hits)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
