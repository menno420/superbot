#!/usr/bin/env python3.10
"""Assert every "run-at-close" checker is actually wired into ``/session-close``.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: a checker authored "to be run at session close" is only useful if it is
  *invoked* at close. The 2026-06-26 dispatch run shipped exactly the failure this
  guards against twice over: ``check_sector_next_freshness.py`` (#1476) was created
  with **no invocation site**, then a follow-up (#1477) had to wire it into the
  ``/session-close`` Step-4 quality gate by hand. The Step-4 block is a hand-maintained
  list of ``python3.10 scripts/check_*.py`` calls that has drifted before — a guard that
  exists but nobody runs is the same drift class it was built to catch.
- The fix is a machine contract: a checker that *should* run at session close declares
  the distinctive ``[session-close-gate]`` sentinel in its source; this meta-check asserts
  each sentinel-bearing checker is referenced in the ``/session-close`` SKILL.md Step-4
  block. It also walks the *reverse* direction — every ``scripts/check_*.py`` referenced
  in Step-4 must exist on disk — so a renamed/removed checker can't leave a dangling call.
- Added: 2026-06-26 (autonomous dispatch run, S3 mechanism — the previous run's Q-0089
  idea, PR #1477). **Unverified** — confirm its output against ground truth over a few
  sessions before trusting it. **Delete this script if it proves noisy/unreliable over
  multiple sessions**; it is a disposable convenience guard, not load-bearing. It is run
  from ``/session-close`` Step 4 (it guards that block), not wired into CI.
- A note on the design vs. the original idea: the idea proposed grepping for the Q-0105
  provenance phrasing. That over-matches (many ``check_*.py`` mention "session close /
  reconciliation routine" in their headers without being Step-4 gates), so a dedicated,
  distinctive sentinel is used instead — low-false-positive and explicit.

What it checks (read-only; exits 1 on any finding, 0 when clean):
- Scan ``scripts/check_*.py`` for the ``[session-close-gate]`` sentinel marker.
- Extract the ``### Step 4`` block of the ``/session-close`` skill and the
  ``scripts/<name>.py`` filenames it references.
- FORWARD: every sentinel-bearing checker must be referenced in the Step-4 block.
- REVERSE: every ``scripts/check_*.py`` referenced in the Step-4 block must exist on disk.

Usage::

    python3.10 scripts/check_session_close_gate.py            # report + exit code
    python3.10 scripts/check_session_close_gate.py --quiet     # exit code only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SKILL_FILE = REPO_ROOT / ".claude" / "skills" / "session-close" / "SKILL.md"

# The distinctive marker a checker declares to say "run me at session close".
SENTINEL = "[session-close-gate]"

# A ``scripts/<name>.py`` reference inside the SKILL.md Step-4 block.
_SCRIPT_REF = re.compile(r"scripts/([A-Za-z0-9._-]+\.py)")


def _read(path: Path) -> str:
    """Return the file text, or an empty string if it does not exist."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def sentinel_checkers() -> list[str]:
    """Return the filenames of ``scripts/check_*.py`` carrying the sentinel."""
    found: list[str] = []
    for path in sorted(SCRIPTS_DIR.glob("check_*.py")):
        if SENTINEL in _read(path):
            found.append(path.name)
    return found


def step4_block(text: str) -> str:
    """Return the text of the ``### Step 4`` section of the skill file.

    The section starts at the ``### Step 4`` heading and ends at the next ``### ``
    heading (or end-of-file).
    """
    lines = text.splitlines()
    buf: list[str] | None = None
    for line in lines:
        if line.startswith("### Step 4"):
            buf = [line]
            continue
        if buf is not None:
            if line.startswith("### "):
                break
            buf.append(line)
    return "\n".join(buf) if buf is not None else ""


def step4_script_refs(block: str) -> set[str]:
    """Return the set of ``scripts/<name>.py`` filenames referenced in a block."""
    return set(_SCRIPT_REF.findall(block))


def run() -> list[str]:
    """Run both directions of the gate contract and return combined findings."""
    findings: list[str] = []

    skill_text = _read(SKILL_FILE)
    if not skill_text:
        return [f"cannot read session-close skill {SKILL_FILE}"]

    block = step4_block(skill_text)
    if not block:
        return [f"no '### Step 4' section found in {SKILL_FILE}"]

    refs = step4_script_refs(block)

    # FORWARD: every sentinel checker must be referenced in Step 4.
    for name in sentinel_checkers():
        if name not in refs:
            findings.append(
                f"{name} declares the {SENTINEL} sentinel but is NOT referenced in "
                f"the /session-close Step-4 block — wire it in (a gate nobody runs is "
                f"useless), or drop the sentinel.",
            )

    # REVERSE: every check_*.py referenced in Step 4 must exist on disk.
    for ref in sorted(refs):
        if not ref.startswith("check_"):
            continue  # Step 4 also runs check_quality.py etc.; the contract is the check_* gates.
        if not (SCRIPTS_DIR / ref).is_file():
            findings.append(
                f"/session-close Step-4 references scripts/{ref} but that file does "
                f"not exist — a dangling gate call (renamed/removed checker).",
            )

    return findings


def main() -> int:
    """CLI entry point: print findings and return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress output; return exit code only",
    )
    args = parser.parse_args()

    findings = run()
    if findings:
        if not args.quiet:
            print("check_session_close_gate: FAIL — session-close gate wiring drift:")
            for f in findings:
                print(f"  - {f}")
        return 1
    if not args.quiet:
        n = len(sentinel_checkers())
        print(
            f"check_session_close_gate: OK — {n} {SENTINEL} checker(s) all wired into "
            f"/session-close Step 4, no dangling references ✓",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
