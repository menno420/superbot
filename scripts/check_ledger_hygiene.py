#!/usr/bin/env python3.10
r"""Ledger-hygiene linter — surface duplicate claim branches / idea-file links.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch)
---------------------------------------------------------------------------
- Why: PR #1003 put git's ``merge=union`` driver on the append-only coordination
  ledgers so concurrent appends from parallel sessions auto-merge instead of
  conflicting (the #995 livelock, hit 3x). Union's one accepted downside: it never
  deletes and never dedups, so over time a duplicate claim or a twice-linked idea
  file can land and accumulate silently — the convention already *permits* pruning
  these by hand, but nothing *surfaces* them. This linter is the surface. It pairs
  with #1003: union keeps the ledgers conflict-free, this keeps them clean. Idea:
  ``docs/ideas/ledger-dedup-linter-2026-06-16.md`` (fleet unit B2).
- Added: 2026-06-19. De-staled 2026-06-27 for the **Q-0195 per-claim-file
  restructure**: the single shared ``docs/owner/active-work.md`` claim ledger was
  retired (now a pointer stub) in favour of **one file per claim** under
  ``docs/owner/claims/``, so the old "Active claims section" scan no-op'd against a
  stub. The claim half now scans the per-file claim directory for a branch claimed
  by more than one file (the per-file analogue of a duplicate claim line — e.g. a
  hand-named claim file whose ``claude/<branch>`` collides with another's). The
  idea-index half is unchanged. Per-file claim *staleness* (a claim left behind after
  merge) is owned by ``check_stale_claims.py``; lane *overlap* by
  ``check_lane_overlap.py`` — this stays narrowly the dedup surface.
- **Unverified** — confirm its output against ground truth a few times across
  sessions before trusting it (the duplicate counts should match a hand grep).
  **Delete this script + its test if it proves unreliable / noisy over multiple
  sessions** — it is a disposable convenience guard (Q-0105), not load-bearing. It
  is read-only: it never modifies the ledgers it inspects.

Behavior
--------
Read-only over two well-structured sources:

* **Claims** (``docs/owner/claims/*.md``, excluding ``README.md``) — flags the same
  ``\`claude/<branch>\``` appearing in more than one claim file. One file per claim
  (Q-0195) makes a duplicate *filename* impossible, but a hand-authored claim file
  can still name a branch another file already claims; that collision is the dupe.
* **Idea index** (``ideas/README.md`` § "What lives here") — flags the same
  ``./<file>.md`` linked twice as a top-level **index entry** (a list item that
  opens ``- [\`...\`](./<file>.md)``). Inline cross-references to an idea from
  inside *another* idea's prose are reported separately as advisory only (they
  are intentional and never fail ``--strict``).

Exit codes: report-only by default (always 0 — it lists what it found and
returns clean so it can run as an advisory without blocking). ``--strict`` exits
1 when a hard duplicate (duplicate Active claim branch, or duplicate idea index
entry) is found, for the reconciliation-cadence pass / opt-in CI.

Pure stdlib, unit-tested.

Usage:
    python3.10 scripts/check_ledger_hygiene.py            # report-only (exit 0)
    python3.10 scripts/check_ledger_hygiene.py --strict   # fail on hard dupes
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CLAIMS_DIR = REPO_ROOT / "docs" / "owner" / "claims"
IDEAS_README = REPO_ROOT / "docs" / "ideas" / "README.md"

# A `claude/<slug>` branch token inside backticks. Slug is lowercase alnum + dashes.
_BRANCH_RE = re.compile(r"`(claude/[A-Za-z0-9][A-Za-z0-9-]*)`")

# A top-level idea **index entry**: a list item that opens with a markdown link to
# a sibling idea file, e.g. `- [`foo-2026-06-16.md`](./foo-2026-06-16.md) — ...`.
_INDEX_ENTRY_RE = re.compile(r"^-\s+\[[^\]]*\]\((\./[A-Za-z0-9._-]+\.md)\)")

# Any markdown link to a sibling idea file, wherever it appears (entry or inline ref).
_ANY_IDEA_LINK_RE = re.compile(r"\]\((\./[A-Za-z0-9._-]+\.md)\)")


def duplicate_claim_branches(claims_dir: Path) -> list[tuple[str, int]]:
    """``(branch, count)`` for each ``claude/<branch>`` claimed by >1 file in ``claims_dir``.

    Scans every ``*.md`` claim file (excluding ``README.md``) under the per-file claim
    directory (Q-0195). A branch is counted **once per file** (a single claim file naming
    its own branch repeatedly is not a duplicate), so the count is the number of *distinct
    files* that claim the same branch — a genuine collision needing a manual prune. Sorted
    by branch for deterministic output. Missing/empty directory → ``[]``.
    """
    counts: Counter[str] = Counter()
    if not claims_dir.is_dir():
        return []
    for path in sorted(claims_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        branches = set(_BRANCH_RE.findall(_read(path)))  # once per file
        counts.update(branches)
    return sorted((b, n) for b, n in counts.items() if n > 1)


def duplicate_idea_entries(text: str) -> list[tuple[str, int]]:
    """``(link, count)`` for each idea file linked >1x as a top-level INDEX entry.

    Only list items that *open* with the idea link count — these are the canonical
    index rows, where a true duplicate means the same idea was indexed twice.
    Sorted by link for deterministic output.
    """
    counts: Counter[str] = Counter()
    for line in text.splitlines():
        m = _INDEX_ENTRY_RE.match(line)
        if m:
            counts[m.group(1)] += 1
    return sorted((link, n) for link, n in counts.items() if n > 1)


def duplicate_idea_links(text: str) -> list[tuple[str, int]]:
    """``(link, count)`` for each idea file linked >1x ANYWHERE (entry or inline).

    A superset of :func:`duplicate_idea_entries`: an idea indexed once but also
    cross-referenced from another idea's prose shows here (advisory) but not in
    the entries report (it is intentional, so it never fails ``--strict``).
    """
    counts = Counter(_ANY_IDEA_LINK_RE.findall(text))
    return sorted((link, n) for link, n in counts.items() if n > 1)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot ledger-hygiene linter.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a hard duplicate (claim branch / idea index entry) is found",
    )
    parser.add_argument(
        "--claims-dir",
        type=Path,
        default=CLAIMS_DIR,
        help="path to the per-file claim directory (default: docs/owner/claims/)",
    )
    parser.add_argument(
        "--ideas-readme",
        type=Path,
        default=IDEAS_README,
        help="path to the idea index (default: docs/ideas/README.md)",
    )
    args = parser.parse_args(argv)

    ideas_text = _read(args.ideas_readme)

    dup_claims = duplicate_claim_branches(args.claims_dir)
    dup_entries = duplicate_idea_entries(ideas_text)
    # Advisory-only set: cross-reference dupes that are NOT duplicate index entries.
    entry_links = {link for link, _ in dup_entries}
    dup_refs = [
        (link, n)
        for link, n in duplicate_idea_links(ideas_text)
        if link not in entry_links
    ]

    hard = bool(dup_claims or dup_entries)

    if dup_claims:
        print("Duplicate claim branches (docs/owner/claims/*.md):")
        for branch, n in dup_claims:
            print(
                f"  - `{branch}` claimed by {n} files — prune the stale duplicate claim.",
            )
    if dup_entries:
        print("Duplicate idea index entries (ideas/README.md § What lives here):")
        for link, n in dup_entries:
            print(f"  - {link} indexed {n}x — keep one index entry, drop the rest.")
    if dup_refs:
        print("Advisory — idea files linked more than once (incl. cross-references):")
        for link, n in dup_refs:
            print(f"  - {link} linked {n}x (likely an intentional cross-ref; review).")

    if not hard and not dup_refs:
        print(
            "check_ledger_hygiene: ledgers clean — no duplicate claims or idea links. ✓",
        )
        return 0

    if hard and args.strict:
        print(
            "\ncheck_ledger_hygiene: FAIL (--strict) — prune the duplicate(s) above. "
            "The append-only union driver (#1003) never dedups, so a duplicate must "
            "be removed by hand.",
        )
        return 1

    print(
        "\ncheck_ledger_hygiene: report-only — exiting 0. Run with --strict to fail "
        "on a hard duplicate (claim branch / idea index entry).",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
