#!/usr/bin/env python3.10
r"""Ledger-hygiene linter — surface duplicate claim branches / idea-file links.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch)
---------------------------------------------------------------------------
- Why: PR #1003 put git's ``merge=union`` driver on the two append-only
  coordination ledgers (``docs/owner/active-work.md`` claim ledger,
  ``docs/ideas/README.md`` idea index) so concurrent appends from parallel
  sessions auto-merge instead of conflicting (the #995 livelock, hit 3x). Union's
  one accepted downside: it never deletes and never dedups, so over time a
  duplicate claim line or a twice-linked idea file can land and accumulate
  silently — the convention already *permits* pruning these by hand, but nothing
  *surfaces* them. This linter is the surface. It pairs with #1003: union keeps
  the ledgers conflict-free, this keeps them clean. Idea:
  ``docs/ideas/ledger-dedup-linter-2026-06-16.md`` (fleet unit B2).
- Added: 2026-06-19. **Unverified** — confirm its output against ground truth a
  few times across sessions before trusting it (the duplicate counts it reports
  should match a hand grep of the two ledgers). **Delete this script + its test if
  it proves unreliable / noisy over multiple sessions** — it is a disposable
  convenience guard (Q-0105), not load-bearing. It is read-only: it never modifies
  the ledgers it inspects.

Behavior
--------
Read-only over two well-structured lists:

* **Active claims** (``active-work.md`` § "Active claims") — flags the same
  ``\`claude/<branch>\``` appearing twice *within that section*. A branch may
  legitimately appear once in Active claims and again under "Recently cleared",
  so the scan is scoped to the Active-claims section only.
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

ACTIVE_WORK = REPO_ROOT / "docs" / "owner" / "active-work.md"
IDEAS_README = REPO_ROOT / "docs" / "ideas" / "README.md"

# A `claude/<slug>` branch token inside backticks. Slug is lowercase alnum + dashes.
_BRANCH_RE = re.compile(r"`(claude/[A-Za-z0-9][A-Za-z0-9-]*)`")

# A top-level idea **index entry**: a list item that opens with a markdown link to
# a sibling idea file, e.g. `- [`foo-2026-06-16.md`](./foo-2026-06-16.md) — ...`.
_INDEX_ENTRY_RE = re.compile(r"^-\s+\[[^\]]*\]\((\./[A-Za-z0-9._-]+\.md)\)")

# Any markdown link to a sibling idea file, wherever it appears (entry or inline ref).
_ANY_IDEA_LINK_RE = re.compile(r"\]\((\./[A-Za-z0-9._-]+\.md)\)")


def section_body(text: str, heading: str) -> str:
    """Return the body of the ``## <heading>`` section (up to the next ``## ``).

    Returns "" when the heading is absent. Matching is exact on the heading text
    after the ``## `` marker (leading/trailing whitespace stripped), so
    "Active claims" finds ``## Active claims`` but not ``## Recently cleared``.
    """
    lines = text.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.startswith("## "):
            if capturing:
                break  # reached the next section — stop
            capturing = line[3:].strip() == heading
            continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def duplicate_active_claims(text: str) -> list[tuple[str, int]]:
    """``(branch, count)`` for each branch appearing >1x in the Active-claims section.

    Sorted by branch for deterministic output. Scans only the Active-claims
    section so a branch that also appears under "Recently cleared" is not a dupe.
    """
    body = section_body(text, "Active claims")
    counts = Counter(_BRANCH_RE.findall(body))
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
        "--active-work",
        type=Path,
        default=ACTIVE_WORK,
        help="path to the claim ledger (default: docs/owner/active-work.md)",
    )
    parser.add_argument(
        "--ideas-readme",
        type=Path,
        default=IDEAS_README,
        help="path to the idea index (default: docs/ideas/README.md)",
    )
    args = parser.parse_args(argv)

    active_text = _read(args.active_work)
    ideas_text = _read(args.ideas_readme)

    dup_claims = duplicate_active_claims(active_text)
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
        print("Duplicate Active-claims branches (active-work.md § Active claims):")
        for branch, n in dup_claims:
            print(f"  - `{branch}` appears {n}x — prune the stale duplicate line.")
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
