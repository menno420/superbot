#!/usr/bin/env python3.10
"""Reconcile-marker band-consistency guard — keep the `Last reconciliation pass` marker honest.

The ``Last reconciliation pass:** PR #N`` marker in ``docs/current-state.md`` is hand-written
by every Q-0107 reconciliation pass, and it conflates two numbers that *look* interchangeable
but are not:

- the **reset target** — the latest *merged* PR at pass time. ``check_reconciliation_due.py``
  keys the cadence off it, and ``check_current_state_ledger.py`` treats it as the lag/drift
  boundary ("everything up to and including #N has been reconciled"). The routine prompt
  (``docs/operations/autonomous-routines.md``) says reset it to **the latest PR**.
- the **pass identity** — the PR the docs-only pass itself shipped as.

These drift apart in a recurring micro-way. The band-#1440 pass wrote ``PR #1441`` (correct reset
target) but its parenthetical claimed #1441 *was* the pass (it shipped as #1443); the band-#1470
pass wrote ``PR #1472`` (its *own* PR) while its parenthetical said "reset to the latest merged PR
#1470" — an internal contradiction. Every pass re-writes the marker by hand, so every pass can
re-introduce the conflation, and the *next* pass re-explains it in prose instead of a checker
catching it (idea ``reconcile-trigger-band-consistency-guard-2026-06-26``).

This guard asserts three independent, internally-checkable invariants on the marker line. Each
is **skipped if its clause is absent**, so an older / abbreviated marker format never false-reds:

1. **Conflation guard (the core):** when the line carries "reset to the latest merged PR #R", the
   leading ``PR #N`` must equal ``R`` — they are the same thing (the reset target), so a leading
   number that is the pass's own PR is the bug.
2. **Band-boundary:** a ``band-#M`` label must satisfy ``M == (N // STEP) * STEP`` (the cadence
   boundary at/under the marker; ``STEP`` mirrors ``check_reconciliation_due.STEP``).
3. **Pass-record link exists:** the linked ``planning/reconciliation-pass-*.md`` resolves on disk.

Advisory by default (exit 0) like its siblings; ``--strict`` exits 1 on any inconsistency. Pure
stdlib, like ``check_docs.py``.

Reliability (Q-0105): **unverified** — confirm its flags against the actual marker over a few
reconciliation passes before trusting it. If it false-positives on a legitimate marker format (or
misses a real conflation) over multiple sessions, **delete it** — it is a convenience guard for
the Q-0107 cadence bookkeeping, not load-bearing.

Usage:
    python3.10 scripts/check_reconcile_marker.py            # advisory report (exit 0)
    python3.10 scripts/check_reconcile_marker.py --strict   # exit 1 on any inconsistency
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO_ROOT / "docs" / "current-state.md"

# Mirrors ``check_reconciliation_due.STEP`` (the multiple-of-N cadence band, 30 since Q-0134).
# Kept as a local constant rather than a cross-script import so this guard stays standalone +
# disposable (scripts/ is not a package); if STEP ever changes, change it in both — they are
# checked against each other by ``test_step_matches_reconciliation_due``.
STEP = 30

# The marker, e.g.:
#   > **Last reconciliation pass:** PR #1470 (2026-06-26, twenty-sixth Q-0107 cadence pass,
#     band-#1470 — [the pass record + next-band queue](planning/reconciliation-pass-2026-06-26-band1470.md);
#     marker reset to the latest merged PR **#1470**). ...
# In ``current-state.md`` it is a multi-line blockquote paragraph, so the clauses (band, doc link,
# reset target) live on *different physical lines* than the leading ``PR #N`` — we must normalise the
# whole paragraph into one logical line before matching, or the conflation check silently skips.
_MARKER_START_RE = re.compile(r"Last reconciliation pass:\*\*\s*PR #\d+", re.IGNORECASE)
# The leading ``PR #N`` captured from the normalised block.
_MARKER_N_RE = re.compile(r"Last reconciliation pass:\*\*\s*PR #(\d+)", re.IGNORECASE)
# The "reset to the latest merged PR #R" clause (R is the true reset target).
_RESET_TARGET_RE = re.compile(
    r"reset to the latest (?:merged )?PR\s*\*{0,2}#(\d+)",
    re.IGNORECASE,
)
# The band label "band-#M".
_BAND_LABEL_RE = re.compile(r"band-#(\d+)", re.IGNORECASE)
# A linked reconciliation-pass record path, e.g. (planning/reconciliation-pass-2026-06-26-band1470.md).
# The captured path forbids inner parens/whitespace so it can only match the markdown link target,
# never the outer ``(2026-06-26, …)`` paren that also wraps the marker sentence.
_PASS_DOC_RE = re.compile(
    r"\(([^()\s]*reconciliation-pass-[^()\s]*\.md)\)",
    re.IGNORECASE,
)


def find_marker_line(text: str) -> str | None:
    """The full ``Last reconciliation pass`` marker paragraph as one normalised logical line.

    The marker is a blockquote paragraph that wraps across several physical lines; this collapses
    it (from the marker start to the next blank line) into a single ``> ``-stripped, single-spaced
    string so the band / doc-link / reset-target clauses are all in scope at once. ``None`` if the
    marker is absent.
    """
    m = _MARKER_START_RE.search(text)
    if not m:
        return None
    start = text.rfind("\n", 0, m.start()) + 1
    end = text.find("\n\n", m.start())  # paragraph break ends the marker block
    block = text[start:] if end == -1 else text[start:end]
    stripped = [re.sub(r"^\s*>\s?", "", ln) for ln in block.splitlines()]
    return re.sub(r"\s+", " ", " ".join(stripped)).strip()


def check_marker(
    text: str | None = None,
    *,
    docs_root: Path | None = None,
) -> list[str]:
    """Return a list of human-readable inconsistency messages (empty = consistent).

    ``text`` defaults to ``current-state.md``; ``docs_root`` (for the pass-doc existence check)
    defaults to ``docs/`` next to it. Each assertion is skipped when its clause is absent, so an
    older marker format degrades to "fewer checks", never a false positive.
    """
    if text is None:
        try:
            text = CURRENT_STATE.read_text(encoding="utf-8")
        except OSError:
            return []
    if docs_root is None:
        docs_root = CURRENT_STATE.parent

    line = find_marker_line(text)
    if line is None:
        return []

    marker_match = _MARKER_N_RE.search(line)
    if marker_match is None:  # defensive: find_marker_line only returns a matched block
        return []
    marker_n = int(marker_match.group(1))

    problems: list[str] = []

    # 1. Conflation guard — leading #N must equal the stated reset target #R.
    reset = _RESET_TARGET_RE.search(line)
    if reset is not None:
        reset_r = int(reset.group(1))
        if reset_r != marker_n:
            problems.append(
                f"leading marker PR #{marker_n} != the stated 'reset to the latest merged PR "
                f"#{reset_r}' — the marker's leading number must be the reset target (the latest "
                f"merged PR), not the pass's own PR. Set the leading number to #{reset_r}.",
            )

    # 2. Band-boundary — band-#M must be the cadence boundary at/under the marker.
    band = _BAND_LABEL_RE.search(line)
    if band is not None:
        band_m = int(band.group(1))
        expected = (marker_n // STEP) * STEP
        if band_m != expected:
            problems.append(
                f"band label band-#{band_m} != the cadence boundary band-#{expected} for marker "
                f"#{marker_n} (M must be (N // {STEP}) * {STEP}).",
            )

    # 3. Pass-record link — the referenced reconciliation-pass-*.md must exist on disk.
    doc = _PASS_DOC_RE.search(line)
    if doc is not None:
        rel = doc.group(1).strip()
        # Marker links are relative to docs/ (e.g. "planning/reconciliation-pass-...md").
        target = (docs_root / rel).resolve()
        if not target.is_file():
            problems.append(
                f"linked pass record '{rel}' does not resolve to a file under {docs_root}.",
            )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="reconcile-marker band-consistency guard (idea "
        "reconcile-trigger-band-consistency-guard-2026-06-26).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if the marker is inconsistent",
    )
    args = parser.parse_args(argv)

    if not CURRENT_STATE.is_file():
        print(
            "check_reconcile_marker: docs/current-state.md not found — nothing to check.",
        )
        return 0

    problems = check_marker()
    if not problems:
        print(
            "check_reconcile_marker: reconciliation marker is internally consistent ✓",
        )
        return 0

    print(
        f"check_reconcile_marker: {len(problems)} inconsistency(ies) in the "
        "`Last reconciliation pass` marker:",
    )
    for p in problems:
        print(f"  - {p}")
    print(
        "\nThis is the reconcile-marker conflation class (idea "
        "reconcile-trigger-band-consistency-guard-2026-06-26): the leading marker PR # must be the "
        "reset target (the latest merged PR), the band-#M label its cadence boundary, and the "
        "linked pass record must exist. Fix the marker line in docs/current-state.md.",
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
