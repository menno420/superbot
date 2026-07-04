#!/usr/bin/env python3
"""Warn-first check for `plan`-badged docs whose own body says the work shipped.

Provenance: added 2026-07-03 (capability-audit capstone, PR #1674) after the audit's
plans review found ≥17 ``docs/planning/*.md`` files still badged ``plan`` while their
own bodies carry shipped markers — stale badges that **materially misled a fleet lane**
(Lane E cited shipped mechanics as forward capability). Q-0194 friction→guard.
UNVERIFIED: confirm its output against ground truth a few times across sessions before
trusting it. **Delete this if it proves unreliable over multiple sessions.**

Three mechanical rules, zero judgment calls:

  1. **shipped-marker** — a ``docs/planning/*.md`` whose Status badge is ``plan`` but
     whose body contains a shipped marker (``✅ SHIPPED``, ``▶ BUILT``, ``AUDIT
     COMPLETE``, ``Applied (…PR #N)``) is flagged: either the badge should flip to
     ``historical`` or the plan should isolate its true remaining tail.
  2. **recon-band** — a ``reconciliation-pass-*-band<N>.md`` still badged ``plan``
     while ``docs/current-state.md``'s ``Last reconciliation pass: PR #<M>`` marker
     has moved past N is flagged (a completed pass record never stays ``plan``).
  3. **idea-shipped** — a ``docs/ideas/*.md`` badged ``ideas`` whose body carries a
     SHIPPED/BUILT/EXECUTED marker is flagged for re-badge (same drift class; the
     ideas sweeps found 16 of these misleading the same audit).

    python3.10 scripts/check_plan_staleness.py            # summary (always exit 0)
    python3.10 scripts/check_plan_staleness.py --list     # per-file detail
    python3.10 scripts/check_plan_staleness.py --strict   # exit 1 on findings (not CI-wired)

Warn-first: **not** wired into CI; run it in /session-close or a recon pass and fix
findings on sight (Q-0166). Promote to a gate only after it proves reliable.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLANNING = REPO_ROOT / "docs" / "planning"
IDEAS = REPO_ROOT / "docs" / "ideas"
CURRENT_STATE = REPO_ROOT / "docs" / "current-state.md"

_BADGE_RE = re.compile(r">\s*\*\*Status:\*\*\s*`?([a-z-]+)`?", re.IGNORECASE)
# Deliberately narrow, high-precision markers — a plan *discussing* shipping is fine;
# these phrasings only appear when a slice is recorded as done inside the doc itself.
_SHIPPED_RES = (
    re.compile(r"✅\s*(?:SHIPPED|DONE|#\d+)", re.IGNORECASE),
    re.compile(r"▶\s*BUILT", re.IGNORECASE),
    re.compile(r"AUDIT COMPLETE", re.IGNORECASE),
    re.compile(r"Applied \(.*PR #\d+\)", re.IGNORECASE),
)
_BAND_RE = re.compile(r"reconciliation-pass-.*band(\d+)\.md$")
_MARKER_RE = re.compile(r"Last reconciliation pass:\*{0,2}\s*PR #(\d+)")


def _badge(text: str) -> str | None:
    for line in text.splitlines()[:12]:
        m = _BADGE_RE.search(line)
        if m:
            return m.group(1).lower()
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="print per-file markers found")
    ap.add_argument("--strict", action="store_true", help="exit 1 on findings")
    args = ap.parse_args()

    marker_pr: int | None = None
    if CURRENT_STATE.exists():
        m = _MARKER_RE.search(CURRENT_STATE.read_text(encoding="utf-8"))
        if m:
            marker_pr = int(m.group(1))

    findings: list[tuple[Path, str]] = []
    for doc in sorted(PLANNING.glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        if _badge(text) != "plan":
            continue
        band = _BAND_RE.search(doc.name)
        if band and marker_pr is not None and int(band.group(1)) < marker_pr:
            findings.append(
                (
                    doc,
                    f"recon-band: band{band.group(1)} < marker PR #{marker_pr} — flip to `historical`",
                ),
            )
            continue
        hits = [rx.pattern for rx in _SHIPPED_RES if rx.search(text)]
        if hits:
            findings.append(
                (
                    doc,
                    f"shipped-marker: body matches {hits[0]!r} while badge is `plan` — flip badge or isolate the remaining tail",
                ),
            )

    idea_shipped_re = re.compile(r"\b(SHIPPED|EXECUTED|▶\s*BUILT)\b")
    for doc in sorted(IDEAS.glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        if _badge(text) != "ideas":
            continue
        if idea_shipped_re.search(text):
            findings.append(
                (
                    doc,
                    "idea-shipped: body carries a SHIPPED/EXECUTED/BUILT marker while badge is `ideas` — re-badge or split the live remainder",
                ),
            )

    if findings:
        print(f"check_plan_staleness: {len(findings)} stale-badged plan file(s) ⚠")
        if args.list or args.strict:
            for doc, why in findings:
                print(f"  - {doc.relative_to(REPO_ROOT)}: {why}")
        else:
            print("  (re-run with --list for detail)")
    else:
        print("check_plan_staleness: no stale-badged plans ✓")

    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
